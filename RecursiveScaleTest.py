import math
from copy import deepcopy
from ParncuttRules import getParncuttRuleScore
import music21

music21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"

results = []
scale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5']

def GenerateFingerings(fingerings, num):
    for i in range(1,6):
        fingerings[num-1] = i
        if num < len(scale):
            GenerateFingerings(fingerings, num+1)
        else:
            print(fingerings)
            piece = music21.stream.Score()
            part = music21.stream.Part()
            part.insert(0, music21.instrument.Piano())
            for n in range(len(scale)):
                note = music21.note.Note(scale[n], duration=music21.duration.Duration(1))
                note.articulations.append(music21.articulations.Fingering(fingerings[n]))
                part.append(note)
            piece.append(part)

            results.append((deepcopy(fingerings), getParncuttRuleScore(piece)[0]))

    return

GenerateFingerings([0,0,0,0,0,0,0,0], 1)

best = math.inf

for r in results:
    s = sum(r[1])
    if s < best:
        best = s

best_fingerings = []

for r in results:
    if sum(r[1]) == best:
        best_fingerings.append(r)

print(best_fingerings)




