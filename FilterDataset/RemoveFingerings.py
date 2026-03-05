import os
import warnings
from music21 import converter, articulations
from music21.musicxml.xmlToM21 import MusicXMLWarning

SOURCE_DIR = r"C:\Users\sklac\Desktop\PianoSetMXL"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEST_DIR = os.path.join(BASE_DIR, "PianoSetMXL")

def remove_all_fingerings(score):
    for n in score.recurse().notes:
        if n.articulations:
            n.articulations = [
                a for a in n.articulations
                if not isinstance(a, articulations.Fingering)
            ]

def has_fingering(score):
    for n in score.recurse().notes:
        if any(isinstance(a, articulations.Fingering) for a in n.articulations):
            return True
    return False

count = 0
modified = 0

for root, _, files in os.walk(SOURCE_DIR):
    for fname in files:
        if not fname.lower().endswith(".mxl"):
            continue

        path = os.path.join(root, fname)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", MusicXMLWarning)
                score = converter.parse(path, forceSource=True)

            if has_fingering(score):
                remove_all_fingerings(score)
                score.write("mxl", path)
                print(f"This file contains fingerings: {fname}")
                modified += 1

            count += 1
            if count % 1000 == 0:
                print(f"Scanned {count} files, modified {modified}")

        except Exception as e:
            print(f"Failed {fname}: {e}")

print(f"Done. Scanned {count}, modified {modified}.")
