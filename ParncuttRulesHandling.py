from music21 import *
from music21 import note
import music21
import numpy as np
from itertools import combinations
from FileConversion import file2Stream
import copy
from ParncuttRuleFunctions import *

"""Parncutt Functions:"""

def getParncuttRuleScore(inputStream):

	score = copy.deepcopy(inputStream)

	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	totalNotes = 0
	parts = score.recurse().parts
	isLeftHand = False

	normalizeScore(parts, isLeftHand)

	isLeftHand = True

	for part in parts:
		totalNotes += len(part.recurse().notes)

		isLeftHand = not isLeftHand
		#first note in sequence
		firstEvent = None
		firstEventAllFingerings = [0]
		#middle note in sequence
		secondEvent = None
		secondEventAllFingerings = [0]
		#third note in sequence
		thirdEvent = None
		thirdEventAllFingerings = [0]

		events = []

		# remove non-scored notes like ends of ties
		for n in part.recurse().notes:
			if isinstance(n, music21.harmony.Harmony):
				continue
			if n.tie and n.tie.type in ('continue', 'stop'):
				continue
			events.append(n)

		for thirdEvent in events:
			if thirdEvent.isChord:
				thirdEventAllFingerings = getFingeringChord(thirdEvent)
				thirdEvent = thirdEvent.notes
			else:
				thirdEventAllFingerings = [getFingering(thirdEvent)]
				thirdEvent = [thirdEvent]
				

			#calculate internal scores for the chord
			internalScore = getInternalScore(thirdEvent, thirdEventAllFingerings, isLeftHand)
			scoreCount = np.array(scoreCount)
			scoreCount = scoreCount + np.array(internalScore)

			unnaggregatedScore = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
			for i in range(len(thirdEvent)):
				thirdNoteFingering = thirdEventAllFingerings[i]
				thirdNote = thirdEvent[i]
				if secondEvent is not None:
					for j in range(len(secondEvent)):
						secondNoteFingering = secondEventAllFingerings[j]
						secondNote = secondEvent[j]
						if firstEvent is not None:
							for k in range(len(firstEvent)):
								firstNote = firstEvent[k]
								firstNoteFingering = firstEventAllFingerings[k]
								unnaggregatedScore.append(getParncuttGivenNotes(isLeftHand, firstNote, 
														firstNoteFingering, secondNote, secondNoteFingering, 
														thirdNote, thirdNoteFingering))
						else:
							unnaggregatedScore.append(getParncuttGivenNotes(isLeftHand, None, None, 
													   secondNote, secondNoteFingering, 
													   thirdNote, thirdNoteFingering))
				else:
					unnaggregatedScore.append(getParncuttGivenNotes(isLeftHand, None, None, 
													   None, None, 
													   thirdNote, thirdNoteFingering))
			

			aggregatedScore = np.max(np.array(unnaggregatedScore), axis=0)

			scoreCount = np.array(scoreCount) + np.array(aggregatedScore)

			firstEvent = secondEvent
			firstEventAllFingerings = secondEventAllFingerings
			secondEvent = thirdEvent
			secondEventAllFingerings = thirdEventAllFingerings

		#at the end of the piece, extra steps are needed to do the last two sets. IE last two notes and then last note
		thirdEvent = None
		unnaggregatedScore = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
		if secondEvent is not None:
			for i in range(len(secondEvent)):
				secondNote = secondEvent[i]
				secondNoteFingering = secondEventAllFingerings[i]
				if firstEvent is not None:
					for j in range(len(firstEvent)):
						firstNote = firstEvent[j]
						unnaggregatedScore.append([0, 0, 0, 0, 0, 0, 0, 0, 0, Parn1OnBlack(firstNote, secondNote, [secondNoteFingering], None), 
								Parn5OnBlack(firstNote, secondNote, [secondNoteFingering], None), 0])
				else:
					unnaggregatedScore.append([0, 0, 0, 0, 0, 0, 0, 0, 0, Parn1OnBlack(None, secondNote, [secondNoteFingering], None), 
								Parn5OnBlack(None, secondNote, [secondNoteFingering], None), 0])
			
		aggregatedScore = np.max(np.array(unnaggregatedScore), axis=0)

		scoreCount = np.array(scoreCount) + np.array(aggregatedScore)

	return scoreCount, totalNotes

def getParncuttGivenNotes(isLeftHand, firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	firstNoteFingering = normalize_fingering(firstNoteFingering)
	secondNoteFingering = normalize_fingering(secondNoteFingering)
	thirdNoteFingering = normalize_fingering(thirdNoteFingering)

	if secondNote is None:
		scoreCount[5] += ParnWeakFinger(thirdNoteFingering)
		return scoreCount

	if thirdNote is not None:
		if len(thirdNoteFingering) == 0:
			return scoreCount

	if secondNote is not None:
		if len(secondNoteFingering) == 0:
			return scoreCount

	if firstNote is not None:
		if len(firstNoteFingering) == 0:
			return scoreCount

	FingeringPairTableLine = getParncuttDistances(secondNoteFingering[-1], thirdNoteFingering[0])

	#convert the parncutt distances for lefthand and descending steps
	#descending steps are any where the first fingering is a higher numerical value than the second
	descending = secondNoteFingering[-1] > thirdNoteFingering[0]
	tableFlipped = (isLeftHand and not descending) or (not isLeftHand and descending)
	if tableFlipped:
		FingeringPairTableLine = [-item for item in FingeringPairTableLine]
		FingeringPairTableLine.reverse()


	noteInterval = interval.Interval(secondNote.pitch, thirdNote.pitch).semitones
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
	spanCount = ParnSpan(noteInterval, minRel, maxRel, secondNoteFingering, thirdNoteFingering, tableFlipped)
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
	if firstNote is not None:
		posChangeCount = ParnPosChange(isLeftHand, noteInterval, firstNote, \
			firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering)
		scoreCount[3] += posChangeCount[0]
		scoreCount[4] += posChangeCount[1]
  

	# Rule 6: Weak-finger rule: 1 point for using 4 or 5
	scoreCount[5] += ParnWeakFinger(thirdNoteFingering)

	# Rule 7: 3-4-5 rule: 1 point if three notes all use 3,4, or 5
	if firstNote is not None:
		scoreCount[6] += Parn345(firstNoteFingering, secondNoteFingering, thirdNoteFingering)
	

	# Rule 8: 3-4 rule: 1 point if 3 is followed by 4
	scoreCount[7] += Parn34(secondNoteFingering, thirdNoteFingering)

	# Rule 9: 4 on black rule: 1 point if 3 is on white and 4 on black in either order
	scoreCount[8] += Parn4OnBlack(secondNote, secondNoteFingering, thirdNote, thirdNoteFingering)
  

	# Rule 10: 1 on black rule: 1 point for 1 on black, further 2 if next note is white, 
	# further 2 if note before is white
	scoreCount[9] += Parn1OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote)

	# Rule 11: 5 on black rule: if 5 on black and proceeding note is white 2 points, 
	# if following note is white 2 points
	scoreCount[10] += Parn5OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote)


	# Rule 12: 1 passing rule: when the thumb passes over or under, 1 point if same level,
	#  3 if lower note is not thumb and on white and the upper note is on black and thumb
	scoreCount[11] += ParnThumbPassing(isLeftHand, noteInterval, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering)
  
	return scoreCount


def getParncuttGivenNotesDP(isLeftHand, firstNote, firstNoteFingering, secondNote, \
	secondNoteFingering, thirdNote, thirdNoteFingering, doDP13 = False):
	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	firstNoteFingering = normalize_fingering(firstNoteFingering)
	secondNoteFingering = normalize_fingering(secondNoteFingering)
	thirdNoteFingering = normalize_fingering(thirdNoteFingering)

	if secondNote is None:
		scoreCount[5] += ParnWeakFinger(firstNoteFingering)
		return scoreCount

	if thirdNote is not None:
		if len(thirdNoteFingering) == 0:
			return scoreCount

	if secondNote is not None:
		if len(secondNoteFingering) == 0:
			return scoreCount

	if firstNote is not None:
		if len(firstNoteFingering) == 0:
			return scoreCount


	FingeringPairTableLine = getParncuttDistances(firstNoteFingering[-1], secondNoteFingering[0])

	#convert the parncutt distances for lefthand and descending steps
	#descending steps are any where the first fingering is a higher numerical value than the second
	descending = firstNoteFingering[-1] > secondNoteFingering[0]
	tableFlipped = (isLeftHand and not descending) or (not isLeftHand and descending)
	if tableFlipped:
		FingeringPairTableLine = [-item for item in FingeringPairTableLine]
		FingeringPairTableLine.reverse()


	noteInterval = interval.Interval(firstNote.pitch, secondNote.pitch).semitones
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
	spanCount = ParnSpan(noteInterval, minRel, maxRel, firstNoteFingering, secondNoteFingering, tableFlipped)
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
	if thirdNote is not None:
		posChangeCount = ParnPosChange(isLeftHand, noteInterval, firstNote, \
			firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering)
		scoreCount[3] += posChangeCount[0]
		scoreCount[4] += posChangeCount[1]
  

	# Rule 6: Weak-finger rule: 1 point for using 4 or 5
	scoreCount[5] += ParnWeakFinger(firstNoteFingering)

	# Rule 7: 3-4-5 rule: 1 point if three notes all use 3,4, or 5
	if thirdNote is not None:
		scoreCount[6] += Parn345(firstNoteFingering, secondNoteFingering, thirdNoteFingering)
	

	# Rule 8: 3-4 rule: 1 point if 3 is followed by 4
	scoreCount[7] += Parn34(firstNoteFingering, secondNoteFingering)

	# Rule 9: 4 on black rule: 1 point if 3 is on white and 4 on black in either order
	scoreCount[8] += Parn4OnBlack(firstNote, firstNoteFingering, secondNote, secondNoteFingering)
  

	# Rule 10: 1 on black rule: 1 point for 1 on black, further 2 if next note is white, 
	# further 2 if note before is white
	scoreCount[9] += Parn1OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote)

	# Rule 11: 5 on black rule: if 5 on black and proceeding note is white 2 points, 
	# if following note is white 2 points
	scoreCount[10] += Parn5OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote)


	# Rule 12: 1 passing rule: when the thumb passes over or under, 1 point if same level,
	#  3 if lower note is not thumb and on white and the upper note is on black and thumb
	scoreCount[11] += ParnThumbPassing(isLeftHand, noteInterval, firstNote, firstNoteFingering, secondNote, secondNoteFingering)
  
	if doDP13:
		scoreCount[12] += RepeatFingering(noteInterval, firstNoteFingering, secondNoteFingering)

	return scoreCount

def generateRandomFingerings(score):
	import random
	for part in score.recurse().parts:
		for item in part.recurse().notes:
			fingeringCount = 0
			for a in item.articulations:
				if isinstance(a, articulations.Fingering):
					fingeringCount += 1

			if isinstance(item, music21.harmony.Harmony):
				continue
			elif item.isNote and fingeringCount == 0:
				item.articulations.append(articulations.Fingering(random.randint(1, 5)))
			elif item.isChord and fingeringCount < len(item.notes):
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