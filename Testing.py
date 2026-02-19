from Algorithm import *
from FileConversion import file2Stream
from AppendFingerings import *
from ParncuttRulesHandling import getParncuttRuleScore, getInternalScore
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
def canon_test(doDP13=False):
    score = file2Stream("music/canon.musicxml")
    rh = score.parts[0]
    lh = score.parts[1]

    optimal_rh = dp(rh, 0, doDP13)
    optimal_lh = dp(lh, 1, doDP13)
    fingering_rh = optimal_rh[0].fingerings
    fingering_lh = optimal_lh[0].fingerings

    addFingeringToPart(rh, fingering_rh)
    addFingeringToPart(lh, fingering_lh)

    score.write("musicxml", "music/canon_out2.musicxml")

    print("Right: ", optimal_rh[0].score, " Left: ", optimal_lh[0].score)
    print("Total score from dp: ", optimal_rh[0].score + optimal_lh[0].score)

    print("Total score from getParncuttRuleScore", sum(getParncuttRuleScore(file2Stream("music/canon_out2.musicxml"))[0]))

# Test file
def test_file(filename):
    score = file2Stream(filename)
    score_out = getParncuttRuleScore(score)
    print(score_out[0])
    print("Total score: ", sum(score_out[0]))

def finger_file(filename, is_left_hand=False, doDP13=False):
    score = file2Stream(filename)
    rh = score.parts[0]

    optimal = dp(rh, is_left_hand, doDP13)[0]
    #print(optimal.fingerings)
    print(optimal.score, optimal.scoreArray)
    fingering = optimal.fingerings
    addFingeringToPart(rh, fingering)

    score.write("musicxml", f"{filename}_out.musicxml")

def finger_file_two_hands(filename, output_path = None, doDP13 = False):
    score = file2Stream(filename)
    parts = score.recurse().parts
    rh = parts[0].chordify()
    lh = parts[1].chordify()

    optimal = dp(rh, False, doDP13)[0]
    optimal_lh = dp(lh, True, doDP13)[0]
    #print(optimal.fingerings)
    print(optimal.score, optimal_lh.score, optimal.score + optimal_lh.score)
    print(optimal.scoreArray + optimal_lh.scoreArray)
    fingering = optimal.fingerings
    fingering_lh = optimal_lh.fingerings
    #print(fingering, fingering_lh)
    addFingeringToPart(rh, fingering)
    addFingeringToPart(lh, fingering_lh)

    newScore = music21.stream.Score()
    newScore.append(rh)
    newScore.append(lh)

    if output_path is None:
        newScore.write("musicxml", f"{filename}_out.musicxml")
    else:
        newScore.write("musicxml", output_path)

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
#print("canon")
#canon_test()
#canon_test(doDP13=True) #WILL RESULT IS MISSMATCH SCORE OUTPUTS

#finger_file("music/canon_firstPage_right.musicxml")
#test_file("music/canon_firstPage_right.musicxml_out.musicxml")

#finger_file("music/canon_Page23_right.musicxml")
#test_file("music/canon_Page23_right.musicxml_out.musicxml")


#print("c scale")
#finger_file("music/cscale_optimal.musicxml")
#test_file("music/cscale_optimal.musicxml")

#print("basic chord")
#finger_file("music/basic_chord.musicxml")
#test_file("music/basic_chord.musicxml_out.musicxml")
finger_file_two_hands("music/QmaVcZykfUKBTQc9CsJk7ywKbq24nkYvLm65X7enktzgzv.mxl")
finger_file_two_hands("music/canon.musicxml")
test_file("music/QmaVcZykfUKBTQc9CsJk7ywKbq24nkYvLm65X7enktzgzv.mxl_out.musicxml")
test_file("music/canon.musicxml_out.musicxml")

#finger_file_two_hands("music/voicesTesting.musicxml") #no voices
#test_file("music/voicesTesting.musicxml_out.musicxml") 
#finger_file_two_hands("music/voicesTesting2.musicxml") #voices
#test_file("music/voicesTesting2.musicxml_out.musicxml")

#print("three chord")
#finger_file("music/three_chord.musicxml")
#test_file("music/three_chord.musicxml_out.musicxml")

#finger_file("music/Chord_test2.musicxml")
#test_file("music/Chord_test2.musicxml_out.musicxml")

#finger_file("music/Chord_test3.musicxml")
#test_file("music/Chord_test3.musicxml_out.musicxml")

#finger_file("music/Chord_test4.musicxml")
#test_file("music/Chord_test4.musicxml_out.musicxml")

# run_test(fscale)
# score_test(fscale, [[1], [2], [3], [3], [1], [2], [3], [4]])
# score_test(fscale, [[1], [1], [2], [2], [3], [4], [5], [5]])

import os

def fingerFullDirectory(input_dir, output_dir, output_dir_dp13):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir_dp13, exist_ok=True),

    count = 0
    errors = 0
    total = sum([len(files) for r, d, files in os.walk(input_dir)])

    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            input_path = os.path.join(root, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_output")
            output_path_dp13 = os.path.join(output_dir_dp13, f"{os.path.splitext(filename)[0]}_output_dp13")
            
            try:
                print(f"{count / total:.2%} Processing: ", filename)
                print("\tProcessing DP")
                finger_file_two_hands(input_path, output_path)
                print("\tProcessing DP13")
                finger_file_two_hands(input_path, output_path_dp13, True)
                count += 1
                #print(output_path)
            except:
                errors += 1

    print(f"Total file: {total}\nTotal run: {count}\nTotal errors: {errors}")

#fingerFullDirectory("C:/Users/Kanix/Downloads/PDMXInput", "C:/Users/Kanix/Downloads/PDMXOutput", "C:/Users/Kanix/Downloads/PDMXOutputDP13")