import math
from copy import deepcopy
from ParncuttRulesHandling import getParncuttGivenNotesDP, getParncuttRuleScore, getInternalScore
import music21
from itertools import combinations
import numpy as np

music21.environment.UserSettings()['musescoreDirectPNGPath'] = "C:\\Program Files\\MuseScore 4\\bin\\MuseScore4.exe"

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

def outer_fingers_penalty(fingering):
    if(len(fingering) < 2):
        return 0
    
    score = 0

    if fingering[0] != 1:
        score += 1
    if fingering[-1] != 5:
        score += 1

    return score

def spacing_penalty(fingering):
    if(len(fingering) < 2):
        return 0
    
    score = 0
    max = 4

    for i in range(len(fingering) - 1):
        score += abs(fingering[i+1] - fingering[i])

    return max - score

# Use 2 subjective rules to determine which shape is best (higher score is better)
def breakTies(entries):
    # Single note
    if(len(entries[0].fingerings[0]) == 1):
        return entries[0]
    
    # Chords
    return max(
        entries,
        key=lambda e: (
            outer_fingers_score(e.fingerings[0]),
            spacing_score(e.fingerings[0])
        )
    )

# Generates the optimal chord shape for a standalone chord, not in context
def generateChordFingering(chord):
    if not chord.isChord:
        return [-9]
    
    chordSize = len(chord.pitches)
       
    # Assumption that this is always the optimal shape for a 5 finger chord on one hand
    if chordSize == 5:
        return [1, 2, 3, 4, 5]

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
    
    if(len(best_fingerings) > 1):
        optimal = breakTies(best_fingerings)
        return optimal
    
    return best_fingerings[0]

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

def setupTrivialNotes(notes, is_left_hand, doDP13):
    trivial_notes = [notes[-2], notes[-1]]
    entry_list = np.empty((5,5), dtype=object)

    # Setup trivial case: [[1,1],[1,2],[1,3]...],[[2,1],[2,2]...]...
    for i in range(5):
        for j in range(5):
            entry_list[i,j] = Entry([[i+1] ,[j+1]],
                                    [[trivial_notes[0]], [trivial_notes[1]]],
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[0], [i+1],
                                                              trivial_notes[1], [j+1],
                                                              None, None, doDP13)) +
                                    sum(getParncuttGivenNotesDP(is_left_hand, trivial_notes[1], [j+1],
                                                              None, None,
                                                              None, None, doDP13)))
  
    return entry_list

def next_valid_note(notes, start):
    i = start
    while i < len(notes):
        if not (notes[i].tie and notes[i].tie.type in ('continue', 'stop')):
            return i
        i += 1
    return None

'''def dp(part, is_left_hand, doDP13 = False):
    notes = part.flatten().notes

    # Setup trivial case: [[1,1],[1,2],[1,3]...],[[2,1],[2,2]...]...
    # entry_list = setupTrivialNotes(notes, is_left_hand, doDP13)
    entry_list = np.empty((5,5), dtype=object)
    entry_list[0,0] = Entry([], [], 0)
    
    for n in range(len(notes)-1, -1, -1):
        note_to_add = notes[n]

        if note_to_add.tie and note_to_add.tie.type in ('continue', 'stop'):
            continue

        if note_to_add.isChord: 
            curr_notes = list(note_to_add.notes) # [<note1>, <note2>, etc]
        else: 
            curr_notes = [note_to_add] # [<note_obj>]

        # prev note
        prev_idx = next_valid_note(notes, n + 1)
        if prev_idx is not None:
            prev_note_length = (
                len(notes[prev_idx].notes)
                if notes[prev_idx].isChord
                else 1
            )
        else:
            prev_note_length = 0

        # prev prev note
        prev_prev_idx = next_valid_note(notes, prev_idx + 1) if prev_idx is not None else None
        if prev_prev_idx is not None:
            prev_prev_note_length = (
                len(notes[prev_prev_idx].notes)
                if notes[prev_prev_idx].isChord
                else 1
            )
        else:
            prev_prev_note_length = 0



        # All possible fingerings for note / chord.
        candidates = generateCandidates(note_to_add, is_left_hand)
        new_entry_list = np.empty((5,5), dtype=object)

        # Iterate through all possible fingerings for the note
        for candidate in candidates: # candidate could be [1] or [1, 3, 5]
            final_finger = candidate[-1] - 1

            # Iterate through all previous optimal fingerings
            for i in range(5):
                e = []
                
                # Calculate new entry with new note and fingering added
                for j in range(5):
                    base_entry = entry_list[i, j]
                    if base_entry is None:
                        continue

                    # Chord
                    if(len(curr_notes) > 1):
                        internal = getInternalScore(curr_notes, candidate, is_left_hand)
                        internal = sum(internal)
                      
                        # Extended rules beyond parncutt. Comment out for pure parncutt
                        #internal += outer_fingers_penalty(candidate)
                        #internal += spacing_penalty(candidate)

                        #print(internal, curr_notes, candidate)

                        temp_entry = Entry(
                            base_entry.fingerings,
                            base_entry.notes,
                            base_entry.score + internal
                        )

                        scoreMaximumsPerStep = []
                        scoreFromLastStep = temp_entry.score
                        for f, (finger, note) in enumerate(zip(candidate, curr_notes)):
                            score, maxScores = calculateScore(is_left_hand, [finger], [note], temp_entry, prev_note_length, prev_prev_note_length, f, doDP13)
                            scoreMaximumsPerStep.append(maxScores)
                            #print(score, candidate, curr_notes)

                            temp_entry = Entry(
                                [[finger]] + temp_entry.fingerings,
                                [[note]] + temp_entry.notes,
                                score
                            )
                        scoreMaximums = np.max(np.array(scoreMaximumsPerStep), axis=0)
                        temp_entry.score = scoreFromLastStep + sum(scoreMaximums)
                        e.append(temp_entry)
                            
                    # Single note
                    else:
                        score, maxScores = calculateScore(is_left_hand, candidate, curr_notes, entry_list[i,j], prev_note_length, prev_prev_note_length, 0, doDP13)
                        e.append(Entry(
                            [candidate] + entry_list[i,j].fingerings,
                            [curr_notes] + entry_list[i,j].notes,
                            score
                        ))

                if not e:
                    continue

                # Take the minimum of calculated scores for new optimal entry
                
                #for entry in e:
                 #   print(entry.score, entry.notes, entry.fingerings)

                best_candidate = min(e, key=lambda x: x.score)
                existing = new_entry_list[final_finger, i]
                #print(best_candidate.score, best_candidate.fingerings)

                if existing is None or best_candidate.score < existing.score:
                    new_entry_list[final_finger, i] = best_candidate

        entry_list = new_entry_list

    # Iterate through resulting array of entries to find optimal fingering
    best = None
    for entry in entry_list.flat:
        if(entry != None):
            if best == None or entry.score < best[0].score:
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

# Expects curr_fingering to be [1]. curr_note should be [<note_obj>]
def calculateScore(is_left_hand, curr_fingering, curr_note, entry, prev_note_length, prev_prev_note_length, idx_in_chord, doDP13):
    same_fingering_penalty = 0
    # if entry.fingerings[0] == new_finger:
    #    same_fingering_penalty = 2 #if you change this value, also change it for the calculations of the trivial cases

    total = entry.score + same_fingering_penalty
    tempScore = []
    maxScores = []

    if(prev_prev_note_length == 0):
        if(prev_note_length == 0):
            output = getParncuttGivenNotesDP(is_left_hand, curr_note[0], curr_fingering,
                                                              None, None,    # prev notes
                                                              None, None, doDP13)  # prev prev notes
            tempScore.append(output)
            #total += sum(output)
        else:
            for j in range(prev_note_length):
                output = getParncuttGivenNotesDP(
                    is_left_hand, curr_note[0], curr_fingering,
                    entry.notes[0 + j + idx_in_chord][0], entry.fingerings[0 + j + idx_in_chord],   # prev notes
                    None, None,
                    doDP13# prev prev notes
                )
                tempScore.append(output)
                #total += sum(output)
                # print(j)

    # Get score from every note of prev note/chord and prev prev note/chord
    for i in range(prev_prev_note_length):
        for j in range(prev_note_length):
            output = getParncuttGivenNotesDP(
                is_left_hand, curr_note[0], curr_fingering,
                entry.notes[0 + j + idx_in_chord][0], entry.fingerings[0 + j + idx_in_chord],   # prev notes
                entry.notes[prev_note_length + i + idx_in_chord][0], entry.fingerings[prev_note_length + i + idx_in_chord] # prev prev notes
                , doDP13
            )
            #print(f"{output} \t {curr_note[0].pitch}\t {entry.notes[0 + j + idx_in_chord][0].pitch} \t {entry.notes[prev_note_length + i + idx_in_chord][0].pitch} \t {curr_fingering} \t {entry.fingerings}")
            tempScore.append(output)
            #total += sum(output)
    #print()
    #print(tempScore)
    if len(tempScore) >= 1:
        maxScores = np.max(np.array(tempScore), axis=0)
        #print(maxScores, curr_note, entry.notes,"\n")
        total += np.sum(maxScores)

    return total, maxScores'''

def dp(part, is_left_hand, doDP13 = False):
    notes = part.flatten().notes

    # Setup trivial case: [[1,1],[1,2],[1,3]...],[[2,1],[2,2]...]...
    # entry_list = setupTrivialNotes(notes, is_left_hand)
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

    #if is_left_hand:
     #   for entry in best:
      #      entry.fingerings = [
       #         [f * -1 for f in fingering]
        #        for fingering in entry.fingerings
         #   ]
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
    total += np.sum(aggregatedScores)

    return total