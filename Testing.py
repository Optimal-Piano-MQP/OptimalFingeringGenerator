from Algorithm import dp
from FileConversion import file2Stream
from AppendFingerings import addFingeringToPart
from ParncuttRulesUpdated import getParncuttRuleScore, getInternalScore
import music21

step_test = ['C4', 'E4', 'D4', 'F4', 'E4', 'G4', 'F4', 'A4'] #step test (expected 12132435 or 13132435, for left 53423131 or 53423121)
cscale = ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 'C5'] #c scale test
fscale = ['F4', 'G4', 'A4', 'Bb4', 'C5', 'D5', 'E5', 'F5'] #f scale test
twinkle = ['C4', 'C4', 'G4', 'G4', 'A4', 'A4', 'G4', 'F4', 'F4', 'E4', 'E4', 'D4', 'D4', 'C4'] #twinkle twinkle test

# Chord testing
def chord_testing():
    score = file2Stream("music/chord_testing.musicxml")
    rh = score.parts[0]

    optimal = dp(rh, 0)[0]
    print(optimal.fingerings, optimal.score)
    fingering = optimal.fingerings
    # print(optimal.fingerings)
    addFingeringToPart(rh, fingering)

    score.write("musicxml", "chord_testing_out.musicxml")


# Canon in d
def canon_test():
    score = file2Stream("music/canon.musicxml")
    rh = score.parts[0]
    lh = score.parts[1]

    optimal_rh = dp(rh, 0)
    optimal_lh = dp(lh, 1)
    fingering_rh = optimal_rh[0].fingerings
    fingering_lh = optimal_lh[0].fingerings

    addFingeringToPart(rh, fingering_rh)
    addFingeringToPart(lh, fingering_lh)

    print("Right: ", optimal_rh[0].score, " Left: ", optimal_lh[0].score)
    print("Total score from dp: ", optimal_rh[0].score + optimal_lh[0].score)

    score.write("musicxml", "music/canon-out.musicxml")

    print("Total score from getParncuttRuleScore", sum(getParncuttRuleScore(file2Stream("music/canon-out.musicxml"))[0]))


# Test file
def test_file(filename):
    score = file2Stream(filename)
    score_out = getParncuttRuleScore(score)
    print(score_out)
    print("Total score: ", sum(score_out[0]))

def finger_file(filename, is_left_hand=False):
    score = file2Stream(filename)
    rh = score.parts[0]

    optimal = dp(rh, is_left_hand)[0]
    print(optimal.fingerings, optimal.score)
    fingering = optimal.fingerings
    # print(optimal.fingerings)
    addFingeringToPart(rh, fingering)

    score.write("musicxml", f"{filename}_out.musicxml")

def run_test(test, is_left_hand=False):
    part = music21.stream.Part()
    part.insert(0, music21.instrument.Piano())

    for n in range(len(test)):
        part.append(music21.note.Note(test[n], duration=music21.duration.Duration(1)))

    optimal = dp(part, is_left_hand)
    for entry in optimal:
        print(entry.fingerings, entry.score)

def score_test(test, fingering):
    score = music21.stream.Score()
    part = music21.stream.Part()
    part.insert(0, music21.instrument.Piano())

    for n in range(len(test)):
        part.append(music21.note.Note(test[n], duration=music21.duration.Duration(1)))

    addFingeringToPart(part, fingering)
    score.append(part)
    score_out = getParncuttRuleScore(score)
    print(score_out)
    print("Total score: ", sum(score_out[0]))

# chord_testing()
canon_test()
# test_file("canon-out.musicxml")
# test_file("three_chord.musicxml_out.musicxml")
# finger_file("music/cscale_optimal.musicxml")
# finger_file("music/chord_testing.musicxml", True)
# finger_file("music/notations_testing.musicxml")
# run_test(fscale, False)
# score_test(fscale, [[1], [2], [3], [3], [1], [2], [3], [4]])
# score_test(fscale, [[1], [1], [2], [2], [3], [4], [5], [5]])