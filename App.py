from flask import Flask, render_template, request, url_for, jsonify, session
import os
import subprocess
import music21
from werkzeug.utils import secure_filename
from Algorithm import dp
from flask import send_from_directory
from FileConversion import file2Stream
from AppendFingerings import addFingeringToPart
import secrets
import zipfile
import xml.etree.ElementTree as ET

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xml", "musicxml", "mxl"}
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = secrets.token_hex(16)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/download/xml")
def download_xml():
    original_name = session.get("original_filename", "annotated")
    base_name = os.path.splitext(original_name)[0]
    download_name = f"{base_name}_fingered.xml"
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        "annotated.xml",
        as_attachment=True,
        download_name=download_name
    )

@app.route("/download/pdf")
def download_pdf():
    original_name = session.get("original_filename", "annotated")
    base_name = os.path.splitext(original_name)[0]
    download_name = f"{base_name}_fingered.pdf"
    return send_from_directory(
        "static",
        "annotated.pdf",
        as_attachment=True,
        download_name=download_name
    )


def _get_xml_content(filepath):
    """Return raw XML string from either a plain .xml/.musicxml or a .mxl zip."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".mxl":
        with zipfile.ZipFile(filepath, "r") as z:
            # Find the rootfile listed in META-INF/container.xml
            with z.open("META-INF/container.xml") as cf:
                ctree = ET.parse(cf)
                rootfile = ctree.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
                if rootfile is None:
                    # Fallback: find first .xml that isn't in META-INF
                    rootfile_path = next(
                        n for n in z.namelist()
                        if n.endswith(".xml") and not n.startswith("META-INF")
                    )
                else:
                    rootfile_path = rootfile.attrib.get("full-path")
            with z.open(rootfile_path) as xf:
                return xf.read().decode("utf-8")
    else:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


def _extract_raw_metadata(filepath):
    """
    Parse the source MusicXML and return a dict with:
      - work_title (str or None)
      - credits: list of raw XML strings for each <credit> element
      - defaults_raw: raw XML string of the <defaults> block (page size / scaling)
      - identification_raw: raw XML string of the <identification> block

    We preserve these verbatim because <credit-words> use absolute coordinates
    (default-x, default-y) that are relative to the page dimensions in <defaults>.
    If music21 rewrites <defaults> with different dimensions the title will no
    longer be centered.
    """
    content = _get_xml_content(filepath)
    lines = [l for l in content.splitlines() if not l.strip().startswith("<!DOCTYPE")]
    content_clean = "\n".join(lines)

    try:
        root = ET.fromstring(content_clean)
    except ET.ParseError:
        return {"work_title": None, "credits": [], "defaults_raw": None, "identification_raw": None}

    ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
    def tag(t):
        return f"{{{ns}}}{t}" if ns else t

    # work-title
    work_title = None
    work = root.find(tag("work"))
    if work is not None:
        wt = work.find(tag("work-title"))
        if wt is not None and wt.text:
            work_title = wt.text.strip()

    # <credit> blocks — title, subtitle, composer, lyricist, etc.
    credits_raw = []
    for credit in root.findall(tag("credit")):
        credits_raw.append(ET.tostring(credit, encoding="unicode"))

    # <defaults> — page dimensions and scaling (needed so credit coordinates are correct)
    defaults_raw = None
    defaults_el = root.find(tag("defaults"))
    if defaults_el is not None:
        defaults_raw = ET.tostring(defaults_el, encoding="unicode")

    # <identification> — software, encoding date, source URL, etc.
    identification_raw = None
    ident_el = root.find(tag("identification"))
    if ident_el is not None:
        identification_raw = ET.tostring(ident_el, encoding="unicode")

    return {
        "work_title": work_title,
        "credits": credits_raw,
        "defaults_raw": defaults_raw,
        "identification_raw": identification_raw,
    }


def _patch_metadata(xml_path, meta):
    import re

    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    work_title   = meta.get("work_title")
    credits_raw  = meta.get("credits", [])
    defaults_raw = meta.get("defaults_raw")
    ident_raw    = meta.get("identification_raw")

    # 1. Fix <work-title>
    if work_title:
        escaped = work_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = re.sub(
            r"<work-title>.*?</work-title>",
            lambda m: f"<work-title>{escaped}</work-title>",
            content,
            flags=re.DOTALL
        )

    # 2. Replace <defaults> with the original so page dimensions stay correct
    if defaults_raw:
        content = re.sub(
            r"<defaults\b.*?</defaults>",
            lambda m: defaults_raw,
            content,
            flags=re.DOTALL
        )

    # 3. Replace <identification> to preserve source / encoding info
    if ident_raw:
        content = re.sub(
            r"<identification\b.*?</identification>",
            lambda m: ident_raw,
            content,
            flags=re.DOTALL
        )

    # 4. Remove any auto-generated <credit> blocks music21 may have written
    content = re.sub(r"<credit\b.*?</credit>", "", content, flags=re.DOTALL)

    # 5. Re-inject original credits verbatim just before <part-list>
    if credits_raw:
        credits_block = "\n  ".join(credits_raw) + "\n  "
        content = content.replace("<part-list>", credits_block + "<part-list>", 1)

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(content)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def split_hands(score):
    parts = score.parts

    if len(parts) == 1:
        part = parts[0].chordify()
        right_notes = []
        left_notes = []

        for n in part.flatten().notes:
            if not n.isNote:
                continue
            if n.pitch.midi >= 60:
                right_notes.append(n)
            else:
                left_notes.append(n)

        return {
            "right": part if right_notes else None,
            "left": part if left_notes else None
        }

    return {
        "right": parts[0],
        "left": parts[1] if len(parts) > 1 else None
    }


def render_pdf(xml_path, pdf_path):
    subprocess.run(
        [MUSESCORE_PATH, xml_path, "-o", pdf_path],
        check=True
    )

def to_python_ints(x):
    if isinstance(x, list):
        return [to_python_ints(v) for v in x]
    return int(x)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle initial file upload and display original score"""
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded. Please select a valid .xml, .musicxml, or .mxl file."}), 400

    if not allowed_file(file.filename):
        ext = os.path.splitext(file.filename)[1] if "." in file.filename else "none"
        return jsonify({
            "error": f"Unsupported file type '{ext}'. Please upload a valid piano score in .xml, .musicxml, or .mxl format."
        }), 400

    filename = secure_filename(file.filename)
    # Store original filename (without path manipulation) in session
    session["original_filename"] = filename
    xml_input = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        file.save(xml_input)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

    try:
        original_pdf = os.path.join("static", "original.pdf")
        render_pdf(xml_input, original_pdf)
    except subprocess.CalledProcessError:
        return jsonify({
            "error": "Could not render your score. Please ensure the file is a valid MusicXML file and try again."
        }), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error during rendering: {str(e)}"}), 500

    return jsonify({
        "success": True,
        "pdf_url": url_for("static", filename="original.pdf"),
        "xml_path": filename
    })


@app.route("/process", methods=["POST"])
def process_file():
    """Process the uploaded file and apply fingerings"""
    data = request.get_json()
    filename = data.get("filename")

    if not filename:
        return jsonify({"error": "No filename provided. Please upload a file first."}), 400

    xml_input = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(xml_input):
        return jsonify({"error": "Uploaded file not found on the server. Please re-upload your file and try again."}), 404

    try:
        score = file2Stream(xml_input)
    except Exception as e:
        return jsonify({"error": f"Could not parse the score file: {str(e)}. Please ensure it is a valid MusicXML file."}), 500

    # Extract title/composer/credits directly from raw XML before music21 touches anything.
    # music21 re-serializes metadata unreliably (drops <credit> blocks, rewrites <defaults>
    # with different page dimensions, falls back to filename for title).
    # We read everything here and patch the output XML after writing.
    raw_meta = _extract_raw_metadata(xml_input)

    hands = split_hands(score)

    if not hands["right"] and not hands["left"]:
        return jsonify({"error": "No playable notes found in the score. Please upload a valid piano score."}), 400

    results = {}

    try:
        if hands["right"]:
            right_best = dp(hands["right"].chordify(), is_left_hand=False)[0]
            addFingeringToPart(hands["right"], right_best.fingerings)
            results["right"] = right_best

        if hands["left"]:
            left_best = dp(hands["left"].chordify(), is_left_hand=True)[0]
            addFingeringToPart(hands["left"], left_best.fingerings)
            results["left"] = left_best
    except Exception as e:
        return jsonify({"error": f"Fingering generation failed: {str(e)}. Please try a different file."}), 500

    annotated_xml = os.path.join(app.config["UPLOAD_FOLDER"], "annotated.xml")
    annotated_pdf = os.path.join("static", "annotated.pdf")

    newScore = music21.stream.Score()

    if hands["right"]:
        newScore.append(hands["right"])
    if hands["left"]:
        newScore.append(hands["left"])

    try:
        newScore.write("musicxml", annotated_xml)
        # Restore original page layout, title, subtitle, composer, and all credit blocks
        _patch_metadata(annotated_xml, raw_meta)
        render_pdf(annotated_xml, annotated_pdf)
    except Exception as e:
        return jsonify({"error": f"Failed to generate annotated score: {str(e)}"}), 500

    result = {
        "pdf_url": url_for("static", filename="annotated.pdf"),
        "xml_url": url_for("download_xml"),
        "pdf_download_url": url_for("download_pdf"),
        "hands": {}
    }

    if "right" in results:
        right_notes = results["right"].notes
        result["hands"]["right"] = {
            "fingers": to_python_ints(results["right"].fingerings),
            "notes": [n.nameWithOctave for n in right_notes[0]] if right_notes else [],
            "score": int(results["right"].score)
        }

    if "left" in results:
        left_notes = results["left"].notes
        result["hands"]["left"] = {
            "fingers": to_python_ints(results["left"].fingerings),
            "notes": [n.nameWithOctave for n in left_notes[0]] if left_notes else [],
            "score": int(results["left"].score)
        }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)