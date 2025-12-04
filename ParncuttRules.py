from music21 import *
import numpy as np
from itertools import combinations
from FileConversion import file2Stream

"""Parncutt Functions:"""

def getParncuttDistances(fingeringA, fingeringB):
	sortedFingerings = sorted([fingeringA, fingeringB])
	fingeringIndex = sortedFingerings[0] * 2 + sortedFingerings[1] * 3

	if(fingeringA == 6 or fingeringB == 6 or fingeringA == fingeringB):
		return[0, 0, 0, 0, 0, 0]

	#for righthand ascending
	#minprac mincomf minrel maxrel maxcomf maxprac
	parncuttTable = {
		8: [-5, -3, 1, 5, 8, 10],
		11: [-4, -2, 3, 7, 10, 12],
		14: [-3, -1, 5, 9, 12, 14],
		17: [-1, 1, 7, 10, 13, 15],
		13: [1, 1, 1, 2, 3, 5],
		16: [1, 1, 3, 4, 5, 7],
		19: [2, 2, 5, 6, 8, 10],
		18: [1, 1, 1, 2, 2, 4],
		21: [1, 1, 3, 4, 5, 7],
		23: [1, 1, 1, 2, 3, 5]
	}

	return parncuttTable[fingeringIndex]


def ParnStretch(noteInterval, minComf, maxComf):
	if noteInterval < minComf:
		return min(2 * abs(minComf - noteInterval), 10)
	elif noteInterval > maxComf:
		return min(2 * abs(maxComf - noteInterval), 10)
	return 0


def ParnSpan(noteInterval, minRel, maxRel, noteBFingering, noteCFingering):
	# Small-span rule: per semitone less than minrel, 1 for includes thumb, 2 for not including thumb
	output = [0, 0]
	if abs(noteInterval) < abs(minRel):
		if noteCFingering[0] == 1 or noteBFingering[-1] == 1:
			output[0] += abs(minRel) - abs(noteInterval)
		else:
			output[0] += 2 * (abs(minRel) - abs(noteInterval))

	# Large-span rule: per semitone greater than maxrel, 1 for includes thumb, 2 for not including thumb
	if abs(noteInterval) > abs(maxRel):
		if noteCFingering[0] == 1 or noteBFingering[-1] == 1:
			output[1] += min(abs(noteInterval) - abs(maxRel), 5)
		else:
			output[1] += min(2 * (abs(noteInterval) - abs(maxRel)), 10)

	return output


def ParnPosChange(isLeftHand, noteInterval, noteA, noteAFingering, noteB, noteBFingering, noteC, noteCFingering):
	firstThirdIntervalParncuttDistances = getParncuttDistances(noteAFingering[-1], noteCFingering[0])
	firstThirdDescending = noteAFingering[-1] > noteCFingering[0]
	if (isLeftHand and not firstThirdDescending) or (not isLeftHand and firstThirdDescending):
		firstThirdIntervalParncuttDistances = [-item for item in firstThirdIntervalParncuttDistances]
		firstThirdIntervalParncuttDistances.reverse()
	firstThirdMaxComf = firstThirdIntervalParncuttDistances[4]
	firstThirdMinComf = firstThirdIntervalParncuttDistances[1]
	firstThirdInterval = interval.Interval(noteA.pitch, noteC.pitch).semitones

	posChange = False
	output = [0, 0]

	#PosChangeSize rule
	if abs(firstThirdInterval) < abs(firstThirdMinComf):
		posChange = True
		output[1] += abs(firstThirdMinComf) - abs(firstThirdInterval)

	if abs(firstThirdInterval) > abs(firstThirdMaxComf):
		posChange = True
		output[1] += abs(firstThirdInterval) - abs(firstThirdMaxComf)

	#PosChangeCount
	if posChange:
		if 1 in noteBFingering and (noteInterval * interval.Interval(noteA.pitch, noteB.pitch).semitones >= 0):
			output[0] += 2
		else:
			output[0] += 1

	return output


def ParnWeakFinger(noteCFingering):
	if 4 in noteCFingering or 5 in noteCFingering:
		return 1

	return 0


def Parn345(noteAFingering, noteBFingering, noteCFingering):
	if noteAFingering[-1] in [3, 4, 5] and set(noteBFingering) & set([3, 4, 5]) and \
		noteCFingering[0] in [3, 4, 5] and len(noteBFingering) == 1:
		return 1

	return 0


def Parn34(noteBFingering, noteCFingering):
	if 3 in noteBFingering and 4 in noteCFingering:
		return 1

	return 0


def Parn4OnBlack(noteB, noteBFingering, noteC, noteCFingering):
	if(noteBFingering[-1] == 3 and noteB.pitch.accidental is None and \
		noteCFingering[0] == 4 and noteC.pitch.accidental is not None) or \
		(noteBFingering[-1] == 4 and noteB.pitch.accidental is not None and \
		noteCFingering[0] == 3 and noteC.pitch.accidental is None):
		return 1

	return 0


def Parn1OnBlack(noteA, noteB, noteBFingering, noteC):
	output = 0
	if 1 in noteBFingering and noteB.pitch.accidental is not None:
		output += 1
	if noteC.pitch.accidental is None and noteBFingering[-1] == 1:
		output += 2
	if noteA is not None:
		if noteA.pitch.accidental is None and noteBFingering[0] == 1:
			output += 2

	return output


def Parn5OnBlack(noteA, noteB, noteBFingering, noteC):
	output = 0
	if 5 in noteBFingering and noteB.pitch.accidental is not None:
		if noteA is not None:
			if noteA.pitch.accidental is None and noteBFingering[-1] == 5:
				output += 2

		if noteC.pitch.accidental is None and noteBFingering[0] == 5:
			output += 2

	return output


def ParnThumbPassing(isLeftHand, noteInterval, noteB, noteBFingering, noteC, noteCFingering):
	output = 0
	if (1 in noteBFingering and isLeftHand and noteInterval > 0) or (1 in noteBFingering and not isLeftHand and noteInterval < 0):
		if (noteB.pitch.accidental is None and noteC.pitch.accidental is None) or \
			(noteB.pitch.accidental is not None and noteC.pitch.accidental is not None):
			output += 1
		elif noteB.pitch.accidental is not None and noteC.pitch.accidental is None:
			output += 3

	if (1 in noteCFingering and isLeftHand and noteInterval < 0) or (1 in noteCFingering and not isLeftHand and noteInterval > 0):
		if (noteB.pitch.accidental is None and noteC.pitch.accidental is None) or \
			(noteB.pitch.accidental is not None and noteC.pitch.accidental is not None):
			output += 1
		elif noteB.pitch.accidental is None and noteC.pitch.accidental is not None:
			output += 3

	return output

def getFingering(note):
	fingering = [6]
	for a in note.articulations:
		if isinstance(a, articulations.Fingering):
			fingering = a.fingerNumber
			#if greater than 5 then this is a substitution fingering and needs to be split
			#this substitute format is custom and part of the PIGconversion script
			if fingering > 5:
				fingering = [int(digit) for digit in str(fingering)]
			else:
				fingering = [fingering]
	return fingering


def getParncuttRuleScore(score):
	#TODO:
	#Fix rests
	#Fix chords
	#look for extentions to these rules in other papers

	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	totalNotes = 0
	parts = score.recurse().parts
	isLeftHand = True

	for part in parts:
		totalNotes += len(part.recurse().notes)

		isLeftHand = not isLeftHand
		#first note in sequence
		eventA = None
		noteAFingering = [0]
		#middle note in sequence
		eventB = None
		noteBFingering = [0]
		#third note in sequence
		noteCFingering = [0]

		for eventC in part.recurse().notes:
			if eventC.isChord:
				eventC = eventC.notes
			else:
				eventC = [eventC]

			internalScore = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
			for pair in combinations(eventC, 2):
				fingering1 = getFingering(pair[0])
				fingering2 = getFingering(pair[1])
				
				FingeringPairTableLine = getParncuttDistances(fingering1[-1], fingering2[0])

				#convert the parncutt distances for lefthand and descending steps
				descending = fingering1[-1] > fingering2[0]
				if (isLeftHand and not descending) or (not isLeftHand and descending):
					FingeringPairTableLine = [-item for item in FingeringPairTableLine]
					FingeringPairTableLine.reverse()

				noteInterval = interval.Interval(pair[0].pitch, pair[1].pitch).semitones
				minComf = FingeringPairTableLine[1]
				minRel = FingeringPairTableLine[2]
				maxRel = FingeringPairTableLine[3]
				maxComf = FingeringPairTableLine[4]

				span =  ParnSpan(noteInterval, minRel, maxRel, fingering1, fingering2)
				internalScore = np.array(internalScore) + np.array([ParnStretch(noteInterval, minComf, maxComf), span[0], span[1], 0, 0, 0, 0, 0, 0, 0, 0, 0])

			scoreCount = np.array(scoreCount) + np.array(internalScore)

			unnaggregatedScore = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
			for noteC in eventC:
				noteCFingering = getFingering(noteC)
				if eventB is not None:
					for noteB in eventB:
						noteBFingering = getFingering(noteB)
						if eventA is not None:
							for noteA in eventA:
								noteAFingering = getFingering(noteA)
								unnaggregatedScore.append(getParncuttGivenNotes(isLeftHand, noteA, noteAFingering, noteB, noteBFingering, noteC, noteCFingering))
						else:
							unnaggregatedScore.append(getParncuttGivenNotes(isLeftHand, None, None, noteB, noteBFingering, noteC, noteCFingering))
			
			#print(unnaggregatedScore)
			aggregatedScore = np.max(np.array(unnaggregatedScore), axis=0)
			#print(aggregatedScore, "\n")

			scoreCount = np.array(scoreCount) + np.array(aggregatedScore)

			eventA = eventB
			eventB = eventC

	return scoreCount, totalNotes


def getParncuttGivenNotes(isLeftHand, noteA, noteAFingering, noteB, noteBFingering, noteC, noteCFingering):
	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	if noteB is None or (noteBFingering[-1] == noteCFingering[0]):
		return scoreCount

	FingeringPairTableLine = getParncuttDistances(noteBFingering[-1], noteCFingering[0])


	#convert the parncutt distances for lefthand and descending steps
	descending = noteBFingering[-1] > noteCFingering[0]
	if (isLeftHand and not descending) or (not isLeftHand and descending):
		FingeringPairTableLine = [-item for item in FingeringPairTableLine]
		FingeringPairTableLine.reverse()


	noteInterval = interval.Interval(noteB.pitch, noteC.pitch).semitones
	minPrac = FingeringPairTableLine[0]
	minComf = FingeringPairTableLine[1]
	minRel = FingeringPairTableLine[2]
	maxRel = FingeringPairTableLine[3]
	maxComf = FingeringPairTableLine[4]
	maxPrac = FingeringPairTableLine[5]

	# Rule 1: Stretch rule: 2 points per semitone above maxcomf or below mincomf
	scoreCount[0] += ParnStretch(noteInterval, minComf, maxComf)

	# Rule 2: Small-span rule: per semitone less than minrel, 1 for includes thumb, 2 otherwise
	# Rule 3: Large-span rule: per semitone greater than maxrel, 1 for includes thumb, 2 otherwise
	spanCount = ParnSpan(noteInterval, minRel, maxRel, noteBFingering, noteCFingering)
	scoreCount[1] += spanCount[0]
	scoreCount[2] += spanCount[1]

	# Rule 4: Position-change-count rule
	#2 points per full hand position change
	#1 point per half change
	#hand change occurs when the 1st and 3rd note of a 3 note group span more
	#than maxcomf of less than mincomf for those two notes
	#full change all three of the following are true:
		#the second note is the thumb
		#second pitch is between 1st and 3rd
		#interval between 1st and 3rd is too big or small
	#all other changes are half changes

	# Rule 5: Position-change-size rule
	#if the 1st and 3rd notes of a three note group and greater than maxcomf
	#or less than mincomf, assign the interval over/under as points
	if noteA is not None:
		posChangeCount = ParnPosChange(isLeftHand, noteInterval, noteA, \
			noteAFingering, noteB, noteBFingering, noteC, noteCFingering)
		scoreCount[3] += posChangeCount[0]
		scoreCount[4] += posChangeCount[1]
  

	# Rule 6: Weak-finger rule: 1 point for using 4 or 5
	scoreCount[5] += ParnWeakFinger(noteCFingering)

	# Rule 7: 3-4-5 rule: 1 point if three notes all use 3,4, or 5
	if noteA is not None:
		scoreCount[6] += Parn345(noteAFingering, noteBFingering, noteCFingering)
	

	# Rule 8: 3-4 rule: 1 point if 3 is followed by 4
	scoreCount[7] += Parn34(noteBFingering, noteCFingering)

	# Rule 9: 4 on black rule: 1 point if 3 is on white and 4 on black in either order
	scoreCount[8] += Parn4OnBlack(noteB, noteBFingering, noteC, noteCFingering)
  

	# Rule 10: 1 on black rule: 1 point for 1 on black, further 2 if next note is white, 
	# further 2 if note before is white
	scoreCount[9] += Parn1OnBlack(noteA, noteB, noteBFingering, noteC)

	# Rule 11: 5 on black rule: if 5 on black and proceeding note is white 2 points, 
	# if following note is white 2 points
	scoreCount[10] += Parn5OnBlack(noteA, noteB, noteBFingering, noteC)


	# Rule 12: 1 passing rule: when the thumb passes over or under, 1 point if same level,
	#  3 if lower note is not thumb and on white and the upper note is on black and thumb
	scoreCount[11] += ParnThumbPassing(isLeftHand, noteInterval, noteB, noteBFingering, noteC, noteCFingering)
  
	return scoreCount

def generateRandomFingerings(score):
	import random
	for part in score.recurse().parts:
		for item in part.recurse().notes:
			fingeringCount = 0
			for a in item.articulations:
				if isinstance(a, articulations.Fingering):
					fingeringCount += 1

			if item.isNote and fingeringCount == 0:
					item.articulations.append(articulations.Fingering(random.randint(1, 5)))
			if item.isChord and fingeringCount < len(item.notes):
				for i in range(fingeringCount, len(item.notes)):
					item.articulations.append(articulations.Fingering(random.randint(1, 5)))
	return score

def allParncutt():
	allParncuttScores = []
	allParncuttScoresNormalized = []
	for n in range(1, 151):
		for i in range(1, 8):
			inputString = f"PianoFingeringDataset_v1.2/FingeringFiles/{n:03}-{i}_fingering.txt"
			try:
				parncuttScore, totalNotes = getParncuttRuleScore(file2Stream(inputString))
				print(f"{n:03}-{i}", parncuttScore, totalNotes)
				allParncuttScores.append([f"{n:03}-{i}", parncuttScore])
				parncuttScoreNormalized = [item / totalNotes for item in parncuttScore]
				allParncuttScoresNormalized.append([f"{n:03}-{i}", parncuttScoreNormalized])
			except FileNotFoundError:
				pass

	return allParncuttScores, allParncuttScoresNormalized

"""Show data in tables using matplot"""

import matplotlib.pyplot as plt

def plotParncuttData(dataToPlot):
	rules = ["Stretch", "SmallSpan", "LargeSpan", "PosChangeCount", "PosChangeSize", "WeakFinger", "3-4-5", "3-4", "4OnBlack", "1OnBlack", "5OnBlack", "ThumbPassing"]

	x = .5 + np.arange(len(dataToPlot))
	for i in range(len(dataToPlot[0][1])):
		y = []
		xlabels = []
		for n in dataToPlot:
			y.append(n[1][i])
			xlabels.append(n[0])

		fig, ax = plt.subplots(figsize=(10, 5))
		ax.bar(x, y, width=.8, edgecolor="white", linewidth=0.7, align='center')
		ax.set_xticks(np.arange(len(x)), labels=xlabels)
		print(f"#{rules[i]:<14}: min: {xlabels[y.index(min(y))]}: {min(y):.3f}   max: {xlabels[y.index(max(y))]}: {max(y):.3f}   avg: {sum(y) / len(y):.3f}")

		plt.show()