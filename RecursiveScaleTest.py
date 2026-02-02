import math
from copy import deepcopy
from ParncuttRulesUpdated import getParncuttGivenNotesDP, getParncuttRuleScore
import music21
import numpy as np

music21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"

#scale = ['C4', 'E4', 'D4', 'F4', 'E4', 'G4', 'F4', 'A4'] #step test (expected 12132435 or 13132435, for left 53423131 or 53423121)
#scale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'] #c scale test
scale = ['F4', 'G4', 'A4', 'Bb4', 'C5', 'D5', 'E5', 'F5'] #f scale test
#scale = ['C4', 'C4', 'G4', 'G4', 'A4', 'A4', 'G4', 'F4', 'F4', 'E4', 'E4', 'D4', 'D4', 'C4'] #twinkle twinkle test
#scale = ['C4', 'E4', 'G4']

class Entry:
    fingerings = []
    notes = []
    score = 0

    def __init__(self, fingerings, notes, score):
        self.fingerings = fingerings
        self.notes = notes
        self.score = score

    def __lt__(self, other):
        if not isinstance(other, Entry):
            return NotImplemented
        return self.score < other.score

    def __str__(self):
        note_strings = [n.nameWithOctave for n in self.notes]
        return str(f"{self.fingerings}\n{note_strings}\n{self.score}")

# notes: List of note pitches    Example: ['C4', 'D4', 'E4']
def bruteForce(notes):
    results = GenerateFingerings([0] * len(notes), 1, notes)

    best = math.inf

    for r in results:
        s = sum(r[1])
        if s < best:
            best = s

    best_fingerings = []

    for r in results:
        if sum(r[1]) == best:
            best_fingerings.append(r)

    return best_fingerings

def GenerateFingerings(fingerings, num, notes):
    results = []
    for i in range(1,6):
        fingerings[num-1] = i
        if num < len(notes):
            GenerateFingerings(fingerings, num+1, notes)
        else:
            print(fingerings)
            piece = music21.stream.Score()
            part = music21.stream.Part()
            part.insert(0, music21.instrument.Piano())
            for n in range(len(notes)):
                note = music21.note.Note(notes[n], duration=music21.duration.Duration(1))
                note.articulations.append(music21.articulations.Fingering(fingerings[n]))
                part.append(note)
            piece.append(part)

            results.append((deepcopy(fingerings), getParncuttRuleScore(piece)[0]))

    return results

def dp(part, is_left_hand):
    notes = part.flatten().notes
    trivial_notes = [notes[-2], notes[-1]]
    entry_list = np.ndarray([5,5], dtype=Entry)

    # Setup trivial case: [[1,1],[1,2],[1,3]...],[[2,1],[2,2]...]...
    for i in range(5):
        for j in range(5):
            entry_list[i,j] = Entry([i+1,j+1],
                                    trivial_notes,
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[0], [i+1],
                                                              trivial_notes[1], [j+1],
                                                              None, None)) +
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[1], [j+1],
                                                              None, None,
                                                              None, None)))
            #if i == j:
             #   entry_list[i, j].score += 2 #if you change this value, also change same_finger_penalty in calculateScore()
    # Find optimal fingering
    for n in range(len(notes)-3, -1, -1):
        note_to_add = notes[n]
        if note_to_add.isChord:
            continue
        new_entry_list = np.ndarray([5,5], dtype=Entry)
        # Iterate through all possible fingerings for the note
        for k in range(5):
            fingering_to_eval = k+1
            # Iterate through all previous optimal fingerings
            for i in range(5):
                e = []
                for j in range(5):
                    # Calculate new entry with new note and fingering added
                    e.append(Entry([fingering_to_eval] + entry_list[i,j].fingerings,
                                   [note_to_add] + entry_list[i,j].notes,
                                   calculateScore(is_left_hand, fingering_to_eval, note_to_add, entry_list[i,j])))
                # Take the minimum of calculated scores for new optimal entry
                new_entry_list[k, i] = min(e)

        entry_list = new_entry_list

    # Iterate through resulting array of entries to find optimal fingering
    best = entry_list[0,0]
    for entry in entry_list.flat:
        print(entry)
        if entry.score < best.score:
            best = entry

    if is_left_hand:
        best.fingerings = [fingering * -1 for fingering in best.fingerings]
    return best


def calculateScore(is_left_hand, new_finger, new_note, entry):
    same_fingering_penalty = 0
    #if entry.fingerings[0] == new_finger:
     #   same_fingering_penalty = 2 #if you change this value, also change it for the calculations of the trivial cases
        
    return (sum(getParncuttGivenNotesDP(is_left_hand,new_note,[new_finger],
                              entry.notes[0],[entry.fingerings[0]],
                              entry.notes[1],[entry.fingerings[1]]))
     + entry.score + same_fingering_penalty)


piece = music21.stream.Score()
part = music21.stream.Part()
part.insert(0, music21.instrument.Piano())

for n in range(len(scale)):
    part.append(music21.note.Note(scale[n], duration=music21.duration.Duration(1)))

optimal = dp(part, 0)
print(optimal)
#optimal = dp(part, 1)
#print(optimal)