from flask import Flask, render_template, request, url_for, jsonify
import os
import subprocess
import music21
from werkzeug.utils import secure_filename
from RecursiveScaleTest import dp
from flask import send_from_directory
from FileConversion import file2Stream
from AppendFingerings import addFingeringToPart

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"xml", "musicxml", "mxl"}
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/download/xml")
def download_xml():
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        "annotated.xml",
        as_attachment=True
    )

@app.route("/download/pdf")
def download_pdf():
    return send_from_directory(
        "static",
        "annotated.pdf",
        as_attachment=True
    )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def split_hands(score):
    parts = score.parts

    if len(parts) == 1:
        part = parts[0]
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


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle initial file upload and display original score"""
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    filename = secure_filename(file.filename)
    xml_input = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(xml_input)

    # Render original PDF for preview
    original_pdf = os.path.join("static", "original.pdf")
    render_pdf(xml_input, original_pdf)

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
        return jsonify({"error": "No filename provided"}), 400

    xml_input = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(xml_input):
        return jsonify({"error": "File not found"}), 404

    score = file2Stream(xml_input)
    hands = split_hands(score)

    results = {}

    if hands["right"]:
        right_best = dp(hands["right"], is_left_hand=False)[0]
        addFingeringToPart(hands["right"], right_best.fingerings)
        results["right"] = right_best

    if hands["left"]:
        left_best = dp(hands["left"], is_left_hand=True)[0]
        addFingeringToPart(hands["left"], left_best.fingerings)
        results["left"] = left_best

    annotated_xml = os.path.join(app.config["UPLOAD_FOLDER"], "annotated.xml")
    annotated_pdf = os.path.join("static", "annotated.pdf")

    score.write("musicxml", annotated_xml)
    render_pdf(annotated_xml, annotated_pdf)

    result = {
        "pdf_url": url_for("static", filename="annotated.pdf"),
        "xml_url": url_for("download_xml"),
        "pdf_download_url": url_for("download_pdf"),
        "hands": {}
    }

    if "right" in results:
        result["hands"]["right"] = {
            "fingers": results["right"].fingerings,
            "notes": [n.nameWithOctave for n in results["right"].notes],
            "score": results["right"].score
        }

    if "left" in results:
        result["hands"]["left"] = {
            "fingers": results["left"].fingerings,
            "notes": [n.nameWithOctave for n in results["left"].notes],
            "score": results["left"].score
        }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)