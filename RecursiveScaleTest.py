import math
from copy import deepcopy
from ParncuttRulesUpdated import getParncuttGivenNotesDP, getParncuttRuleScore, getInternalScore
import music21
from itertools import combinations
import numpy as np

music21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"

#scale = ['C4', 'E4', 'D4', 'F4', 'E4', 'G4', 'F4', 'A4'] #step test (expected 12132435 or 13132435, for left 53423131 or 53423121)
#scale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'] #c scale test
scale = ['F4', 'G4', 'A4', 'Bb4', 'C5', 'D5', 'E5', 'F5'] #f scale test
#scale = ['C4', 'C4', 'G4', 'G4', 'A4', 'A4', 'G4', 'F4', 'F4', 'E4', 'E4', 'D4', 'D4', 'C4'] #twinkle twinkle test

class Entry:
    # fingerings in format: [[1], [2], [1, 3, 5], [5], ...] where each element is a list
    # monophonic is a list of length 1, chords are a list of the length of the chord

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
def bruteForce(notes, isLeftHand):
    results = []
    GenerateFingerings([0] * len(notes), 1, notes, isLeftHand, results)

    best = results[0][1]
    best_fingerings = []

    for r in results:
        s = r[1]
        if s == best:
            best_fingerings.append(r)
        elif s < best:
            best = s
            best_fingerings = [r]

    return best_fingerings

def GenerateFingerings(fingerings, num, notes, isLeftHand, results):
    for i in range(1,6):
        fingerings[num-1] = i
        if num < len(notes):
            GenerateFingerings(fingerings, num+1, notes, isLeftHand, results)
        else:
            # print(fingerings)
            piece = music21.stream.Score()
            part = music21.stream.Part()
            part.insert(0, music21.instrument.Piano())
            if isLeftHand:
                piece.append(part)
                part = music21.stream.Part()
                part.insert(0, music21.instrument.Piano())
                for n in range(len(notes)):
                    note = music21.note.Note(notes[n], duration=music21.duration.Duration(1))
                    note.articulations.append(music21.articulations.Fingering(fingerings[n]))
                    part.append(note)
            else:
                for n in range(len(notes)):
                    note = music21.note.Note(notes[n], duration=music21.duration.Duration(1))
                    note.articulations.append(music21.articulations.Fingering(fingerings[n]))
                    part.append(note)
            piece.append(part)

            results.append((deepcopy(fingerings), sum(getParncuttRuleScore(piece)[0])))

    return

def ascending_fingerings(num_notes):
    return list(combinations(range(1, 6), num_notes))

def outer_fingers_score(fingering):
    score = 0

    if fingering[0] == 1:
        score += 1
    if fingering[-1] == 5:
        score += 1

    return score

def spacing_score(fingering):
    score = 0

    for i in range(len(fingering) - 1):
        score += abs(fingering[i+1] - fingering[i])

    return score

# Use 2 subjective rules to determine which shape is best (higher score is better)
def breakTies(entries):
    # Single note
    # print(entries[0].fingerings[0])
    if(len(entries[0].fingerings[0]) == 1):
        # print("SINGLE!")
        return entries[0]
    
    # Chords
    return max(
        entries,
        key=lambda e: (
            outer_fingers_score(e.fingerings[0]),
            spacing_score(e.fingerings[0])
        )
    )
# def breakChordTies(fingerings):
#     return max(
#         fingerings,
#         key=lambda f: (
#             outer_fingers_score(f),
#             spacing_score(f)
#         )
#     )

# Generates the optimal chord shape for a standalone chord, not in context
def generateChordFingering(chord):
    if not chord.isChord:
        return [-9]
    
    chordSize = len(chord.pitches)
       
    # Assumption that this is always the optimal shape for a 5 finger chord on one hand
    if chordSize == 5:
        return [1, 2, 3, 4, 5]

    # print("CHORD OF SIZE: ", chordSize)
    f_combinations = ascending_fingerings(chordSize)

    best_score = None
    best_fingerings = []

    for comb in f_combinations:
        fingering_as_lists = [[f] for f in comb]
        internalScore = sum(getInternalScore(chord, fingering_as_lists, 0))

        if best_score is None or internalScore < best_score:
            best_score = internalScore
            best_fingerings = [list(comb)]
        elif internalScore == best_score:
            best_fingerings.append(list(comb))
        # print(comb, internalScore)
    
    if(len(best_fingerings) > 1):
        optimal = breakTies(best_fingerings)
        # print("TIE WINNER: ", optimal)
        return optimal
    
    return best_fingerings[0]

# Generates all possible combinations of fingerings with the given note(s)
# Single note is [[1], [2], [3], [4], [5]]
# Chord could be [[1, 3, 5], [1, 2, 4], etc]
def generateCandidates(notes):
    if(notes.isNote):
        return [[f] for f in range(1, 6)]
    
    chordSize = len(notes)

    if chordSize == 1:
        return [[f] for f in range(1, 6)]

    if chordSize == 5:
        return [[1, 2, 3, 4, 5]]

    return [
        [f for f in comb]
        for comb in combinations(range(1, 6), chordSize)
    ]

def setupTrivialNotes(notes, is_left_hand):
    trivial_notes = [notes[-2], notes[-1]]
    entry_list = np.empty((5,5), dtype=object)

    # Setup trivial case: [[1,1],[1,2],[1,3]...],[[2,1],[2,2]...]...
    for i in range(5):
        for j in range(5):
            entry_list[i,j] = Entry([[i+1] ,[j+1]],
                                    [[trivial_notes[0]], [trivial_notes[1]]],
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[0], [i+1],
                                                              trivial_notes[1], [j+1],
                                                              None, None)) +
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[1], [j+1],
                                                              None, None,
                                                              None, None)))
            # if i == j:
            #     entry_list[i, j].score += 2 #if you change this value, also change same_finger_penalty in calculateScore()

    return entry_list

def dp(part, is_left_hand):
    notes = part.flatten().notes
    entry_list = setupTrivialNotes(notes, is_left_hand)
    
    for n in range(len(notes)-3, -1, -1):
        note_to_add = notes[n]

        if note_to_add.isChord: 
            curr_notes = list(note_to_add.notes) # [<note1>, <note2>, etc]
        else: 
            curr_notes = [note_to_add] # [<note_obj>]

        # All possible fingerings for note / chord.
        candidates = generateCandidates(note_to_add)
        print("CANDIDATES: ", candidates)
        new_entry_list = np.empty((5,5), dtype=object)

        # Iterate through all possible fingerings for the note
        for candidate in candidates: # candidate could be [1] or [1, 3, 5]
            # Iterate through all previous optimal fingerings
            for i in range(5):
                e = []
                for j in range(5):
                    # Calculate new entry with new note and fingering added
                    # print(curr_notes)
                    e.append(Entry(
                                [candidate] + entry_list[i,j].fingerings,
                                [curr_notes] + entry_list[i,j].notes,
                                calculateScore(is_left_hand, candidate, curr_notes, entry_list[i,j])
                            ))
                    # print(e[0].fingerings)
                # Take the minimum of calculated scores for new optimal entry
                # print("CURR CANDIDATE: ", candidate)
                new_entry_list[candidate[0] - 1, i] = min(e, key=lambda x: x.score)
                # print(new_entry_list[candidate, i].fingerings)
                # print(new_entry_list[k, i].fingerings)

        entry_list = new_entry_list

    # Iterate through resulting array of entries to find optimal fingering
    best = [entry_list[0,0]]
    for entry in entry_list.flat:
        if entry.score < best[0].score:
            best = [entry]
        elif entry.score == best[0].score:
            best.append(entry)

    if is_left_hand:
        for entry in best:
            entry.fingerings = [
                [f * -1 for f in fingering]
                for fingering in entry.fingerings
            ]
    return best

def calculateScore(is_left_hand, curr_fingerings, curr_notes, entry):
    same_fingering_penalty = 0
    # if entry.fingerings[0] == new_finger:
    #    same_fingering_penalty = 2 #if you change this value, also change it for the calculations of the trivial cases
    total = entry.score

    total += sum(getInternalScore(curr_notes, curr_fingerings, is_left_hand))
    rule_vectors = []

    # print(entry.notes)
    # print(entry.fingerings)

    prev_notes = entry.notes[0]
    prev_fingerings = entry.fingerings[0]

    prevprev_notes = entry.notes[1]
    prevprev_fingerings = entry.fingerings[1]

    return (sum(getParncuttGivenNotesDP(is_left_hand, curr_notes[0], curr_fingerings,
                              prev_notes[0], prev_fingerings,
                              prevprev_notes[0], prevprev_fingerings))
     + entry.score + same_fingering_penalty)

    # for c_note, c_f in zip(curr_notes, curr_fingerings):
    #     for p_note, p_f in zip(prev_notes, prev_fingerings):
    #         if prevprev_notes:
    #             for pp_note, pp_f in zip(prevprev_notes, prevprev_fingerings):
    #                 rule_vectors.append(
    #                     getParncuttGivenNotesDP(
    #                         is_left_hand,
    #                         pp_note, [pp_f],
    #                         p_note,  [p_f],
    #                         c_note,  [c_f]
    #                     )
    #                 )
    #         else:
    #             rule_vectors.append(
    #                 getParncuttGivenNotesDP(
    #                     is_left_hand,
    #                     None, None,
    #                     p_note, [p_f],
    #                     c_note, [c_f]
    #                 )
    #             )

    # aggregated = np.max(rule_vectors, axis=0)
    # total += sum(aggregated)

    # return total