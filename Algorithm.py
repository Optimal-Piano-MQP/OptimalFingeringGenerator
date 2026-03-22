from ParncuttRulesHandling import getParncuttGivenNotesDP, getInternalScore
import music21
from itertools import combinations
import numpy as np

# music21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"

class Entry:
    # fingerings in format: [[1], [2], [1, 3, 5], [5], ...] where each element is a list
    # monophonic is a list of length 1, chords are a list of the length of the chord

    def __init__(self, fingerings, notes, score, scoreArray):
        self.fingerings = fingerings
        self.notes = notes
        self.score = score
        self.scoreArray = scoreArray

    def __lt__(self, other):
        if not isinstance(other, Entry):
            return NotImplemented
        return self.score < other.score

    def __str__(self):
        note_strings = [n.nameWithOctave for n in self.notes]
        return str(f"{self.fingerings}\n{note_strings}\n{self.score}")

# Generates all possible combinations of fingerings with the given note(s)
# Single note is [[1], [2], [3], [4], [5]]
# Chord could be [[1, 3, 5], [1, 2, 4], etc]
def generateCandidates(notes, is_left_hand):
    if(notes.isNote):
        return [[f] for f in range(1, 6)]
    
    chordSize = len(notes)
    candidates = []

    if chordSize > 5:
        return [[0] * chordSize]

    if is_left_hand:
        candidates = [[f for f in comb] for comb in combinations([5,4,3,2,1], chordSize)]
    else:
        candidates = [[f for f in comb] for comb in combinations([1,2,3,4,5], chordSize)]

    return candidates

def dp(part, is_left_hand, doDP13 = False):
    notes = part.flatten().notes
    entry_list = np.empty((5, 5), dtype=object)
    entry_list[0, 0] = Entry([], [], 0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    is_tied_note_pitches = None

    for n in range(len(notes) - 1, -1, -1):
        note_to_add = notes[n]

        if note_to_add.isChord:
            curr_notes = list(note_to_add.notes)  # [<note1>, <note2>, etc]
        else:
            curr_notes = [note_to_add]  # [<note_obj>]

        isTied = False
        if note_to_add.tie:
            if note_to_add.tie.type in ('continue', 'start'):
                if note_to_add.pitches == is_tied_note_pitches:
                    continue
                else:
                    is_tied_note_pitches = note_to_add.pitches
                    isTied = True
                    
            elif note_to_add.tie.type in ('stop'):
                is_tied_note_pitches = note_to_add.pitches

        # All possible fingerings for note / chord.
        candidates = generateCandidates(note_to_add, is_left_hand)
        new_entry_list = np.empty((len(candidates), entry_list.shape[0]), dtype=object)

        # Iterate through all possible fingerings for the note
        for c in range(len(candidates)):  # candidate could be [1] or [1, 3, 5]
            candidate = candidates[c]

            # Iterate through all previous optimal fingerings
            for i in range(entry_list.shape[0]):
                e = []
                

                # Calculate new entry with new note and fingering added
                for j in range(entry_list.shape[1]):
                    if entry_list[i, j] is None:
                        continue

                    if isTied:
                        previousPitches = [note.pitch for note in entry_list[i, j].notes[0]]
                        currentPitches = [note.pitch for note in curr_notes]
                        sharedPitches = [pitch for pitch in currentPitches if pitch in previousPitches]
                        currPitchIndex = []
                        prevPitchIndex = []
                        for pitch in sharedPitches:
                            currPitchIndex.append(currentPitches.index(pitch))
                            prevPitchIndex.append(previousPitches.index(pitch))

                        forcedFingerings = []
                        currentFingeringsAtForced = []
                        for fingeringIndex in currPitchIndex:
                            currentFingeringsAtForced.append(candidate[fingeringIndex])
                        for fingeringIndex in prevPitchIndex:
                            forcedFingerings.append(entry_list[i, j].fingerings[0][fingeringIndex])
                        
                        if forcedFingerings != currentFingeringsAtForced:
                            continue
                        

                    internal = 0
                    internalArray = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                    # Chord
                    if len(curr_notes) > 1:
                        internalArray = np.append(getInternalScore(curr_notes, candidate, is_left_hand), 0)
                        internal = sum(internalArray)
                        # Extended rules beyond parncutt. Comment out for pure parncutt
                        # internal += outer_fingers_penalty(candidate)
                        # internal += spacing_penalty(candidate)

                    scoreArray = calculateScore(is_left_hand, candidate, curr_notes, entry_list[i, j], doDP13)
                    score = sum(scoreArray)
                    e.append(Entry(
                        [candidate] + entry_list[i, j].fingerings,
                        [curr_notes] + entry_list[i, j].notes,
                        score + entry_list[i,j].score + internal,
                        np.array(scoreArray) + entry_list[i, j].scoreArray + np.array(internalArray)
                    ))

                if not e:
                    continue

                # Take the minimum of calculated scores for new optimal entry
                best_candidate = min(e)
                existing = new_entry_list[c, i]

                if existing is None or best_candidate < existing:
                    new_entry_list[c, i] = best_candidate

        entry_list = new_entry_list

    # Iterate through resulting array of entries to find optimal fingering
    best = None
    for entry in entry_list.flat:
        if (entry != None):
            if best == None or entry < best[0]:
                best = [entry]
            elif entry == best[0]:
                best.append(entry)

    return best

def calculateScore(is_left_hand, curr_fingerings, curr_notes, entry, doDP13):

    total = 0
    if len(entry.notes) == 0:
        prev_note_length = 0
    else:
        prev_notes = entry.notes[0]
        prev_fingerings = entry.fingerings[0]
        prev_note_length = len(prev_notes)

    if len(entry.notes) <= 1:
        prev_prev_note_length = 0
    else:
        prev_prev_notes = entry.notes[1]
        prev_prev_fingerings = entry.fingerings[1]
        prev_prev_note_length = len(prev_prev_notes)

    unaggregatedScores = []
    for i in range(len(curr_notes)):
        curr_note = curr_notes[i]
        curr_fingering = curr_fingerings[i]

        if prev_note_length != 0:
            for j in range(prev_note_length):
                prev_note = prev_notes[j]
                prev_fingering = prev_fingerings[j]

                if prev_prev_note_length != 0:
                    for k in range(prev_prev_note_length):
                        prev_prev_note = prev_prev_notes[k]
                        prev_prev_fingering = prev_prev_fingerings[k]

                        unaggregatedScores.append(getParncuttGivenNotesDP(
                            is_left_hand, curr_note, [curr_fingering],
                            prev_note, [prev_fingering],  # prev notes
                            prev_prev_note, [prev_prev_fingering],  # prev prev notes
                            doDP13
                    ))
                else:
                    unaggregatedScores.append(getParncuttGivenNotesDP(
                        is_left_hand, curr_note, [curr_fingering],
                        prev_note, [prev_fingering],  # prev notes
                        None, None,  # prev prev notes
                        doDP13
                    ))
        else:
            unaggregatedScores.append(getParncuttGivenNotesDP(
                is_left_hand, curr_note, [curr_fingering],
                None, None,  # prev notes
                None, None, doDP13))  # prev prev notes

    aggregatedScores = np.max(np.array(unaggregatedScores), axis=0)
    return(aggregatedScores)