import os
import random
from xml.etree import ElementTree as ET

# This program scans the Output_PianoPlayer folder for MusicXML files and fills
# any notes missing fingering annotations with a random fingering (1-5).
# Output is saved to the Output_Random folder.

MUSICXML_NS = 'http://www.musicxml.org/ns/musicxml'

base_dir = os.path.dirname(os.path.abspath(__file__))

input_dir = os.path.join(base_dir, "Output_VNS_Reversed")
output_dir = os.path.join(base_dir, "Output_VNS_Reversed_Fixed")

os.makedirs(output_dir, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns_prefix(root):
    return f'{{{MUSICXML_NS}}}' if root.tag.startswith(f'{{{MUSICXML_NS}}}') else ''

def _has_fingering(note, p):
    notations = note.find(f'{p}notations')
    if notations is None:
        return False
    technical = notations.find(f'{p}technical')
    if technical is None:
        return False
    return technical.find(f'{p}fingering') is not None

def _is_rest(note, p):
    return note.find(f'{p}rest') is not None

def fill_missing_fingerings(input_path, output_path):
    ET.register_namespace('', MUSICXML_NS)
    tree = ET.parse(input_path)
    root = tree.getroot()
    p = _ns_prefix(root)

    added = 0
    for note in root.iter(f'{p}note'):
        if _is_rest(note, p) or _has_fingering(note, p):
            continue

        notations = note.find(f'{p}notations')
        if notations is None:
            notations = ET.SubElement(note, f'{p}notations')
        technical = notations.find(f'{p}technical')
        if technical is None:
            technical = ET.SubElement(notations, f'{p}technical')

        finger_elem = ET.SubElement(technical, f'{p}fingering')
        finger_elem.text = str(random.randint(1, 5))
        added += 1

    tree.write(output_path, encoding='unicode', xml_declaration=True)
    return added

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

extensions = ('.musicxml', '.xml')
files = [f for f in os.listdir(input_dir) if f.lower().endswith(extensions)]

if not files:
    print(f"No MusicXML files found in '{input_dir}'.")
else:
    print(f"Found {len(files)} file(s) to process.\n")
    for filename in sorted(files):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        try:
            added = fill_missing_fingerings(input_path, output_path)
            if added:
                print(f"  {filename}: filled {added} missing fingering(s)")
            else:
                print(f"  {filename}: no missing fingerings found")
        except ET.ParseError as e:
            print(f"  {filename}: SKIPPED (XML parse error: {e})")
        except Exception as e:
            print(f"  {filename}: SKIPPED (unexpected error: {e})")

    print(f"\nDone! Output written to '{output_dir}'")