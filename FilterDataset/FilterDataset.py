import os
import shutil
from music21 import converter, instrument, stream, midi
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = r"DIRECTORY"
DEST_DIR = os.path.join(BASE_DIR, "PianoSetMXL")
PIANO_NAMES = {"piano", "pno", "pianoforte", "klavier", "grand piano", "upright piano", "pipe organ"}

# Should be ~254077 pieces total, returned x pieces

def is_solo_piano(score: stream.Score):
    parts = score.parts
    if len(parts) != 2:
        print(f"Parts should be 2, but it's {len(parts)}")
        return False
    
    for i, part in enumerate(parts):
        inst_list = part.getInstruments(returnDefault=False)
        if not inst_list or not inst_list[0]:
            print(f"Part {i} has no instrument")
            return False

        inst = inst_list[0]
        name = (inst.instrumentName or inst.partName or "").lower()
        
        if not any(p in name for p in PIANO_NAMES):
            print(f"Part {i} should be piano, but it's {name}")
            return False

    return True

def destination_subfolder(filename, base_folder):
    # Stable hash, first two hex digits -> 256 subfolders
    h = hashlib.sha1(filename.encode()).hexdigest()[:2]
    sub = os.path.join(base_folder, h)
    os.makedirs(sub, exist_ok=True)
    return sub

def filter_solo_piano():
    os.makedirs(DEST_DIR, exist_ok=True)
    count = 0

    for root, dirs, files in os.walk(SOURCE_DIR):
        print(f"Current folder: {root}")
        for filename in files:
            if not filename.lower().endswith(".mxl"):
                continue

            filepath = os.path.join(root, filename)

            try:
                score = converter.parse(filepath, forceSource=True)
            except Exception as e:
                print(f" Cound not parse: {e}")
                continue

            if is_solo_piano(score):
                subdir = destination_subfolder(filename, DEST_DIR)
                dest = os.path.join(subdir, filename)
                shutil.copy(filepath, dest)
            else:
                print(f"Not solo piano. File discarded")

            count = count + 1
            del score

    print("")
    print(f"Total parsed: {count}")


if __name__ == "__main__":
    filter_solo_piano()