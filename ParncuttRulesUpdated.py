from music21 import *
from music21 import note
import music21
import numpy as np
from itertools import combinations
from FileConversion import file2Stream
import copy

"""Parncutt Functions:"""

def getParncuttDistances(firstFingering, secondFingering):
	firstFingering = abs(firstFingering)
	secondFingering = abs(secondFingering)
	sortedFingerings = sorted([firstFingering, secondFingering])
	fingeringIndex = sortedFingerings[0] * 2 + sortedFingerings[1] * 3

	if(firstFingering not in range(1, 6) or secondFingering not in range (1,6) or firstFingering == secondFingering):
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
		return 2 * abs(maxComf - noteInterval)
	return 0


def ParnSpan(noteInterval, minRel, maxRel, secondNoteFingering, thirdNoteFingering, tableFlipped):
	# Small-span rule: per semitone less than minrel, 1 for includes thumb, 2 for not including thumb
	output = [0, 0]

	if noteInterval < minRel:
		if thirdNoteFingering[0] == 1 or secondNoteFingering[-1] == 1:
			output[0] += abs(minRel - noteInterval)
		else:
			output[0] += 2 * (abs(minRel - noteInterval))

	# Large-span rule: per semitone greater than maxrel, 1 for includes thumb, 2 for not including thumb
	if noteInterval > maxRel:
		if thirdNoteFingering[0] == 1 or secondNoteFingering[-1] == 1:
			output[1] += abs(noteInterval - maxRel)
		else:
			output[1] += 2 * (abs(noteInterval - maxRel))

	#if tableFlipped:
	#	output.reverse()

	return output


def ParnPosChange(isLeftHand, noteInterval, firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	firstThirdIntervalParncuttDistances = getParncuttDistances(firstNoteFingering[-1], thirdNoteFingering[0])
	firstThirdDescending = firstNoteFingering[-1] > thirdNoteFingering[0]
	if (isLeftHand and not firstThirdDescending) or (not isLeftHand and firstThirdDescending):
		firstThirdIntervalParncuttDistances = [-item for item in firstThirdIntervalParncuttDistances]
		firstThirdIntervalParncuttDistances.reverse()
	firstThirdMaxPrac = firstThirdIntervalParncuttDistances[5]
	firstThirdMaxComf = firstThirdIntervalParncuttDistances[4]
	firstThirdMinComf = firstThirdIntervalParncuttDistances[1]
	firstThirdMinPrac = firstThirdIntervalParncuttDistances[0]
	firstThirdInterval = interval.Interval(firstNote.pitch, thirdNote.pitch).semitones

	posChange = False
	output = [0, 0]

	#PosChangeSize rule
	if firstThirdInterval < firstThirdMinComf:
		posChange = True
		output[1] += abs(firstThirdMinComf - firstThirdInterval)

	if firstThirdInterval > firstThirdMaxComf:
		posChange = True
		output[1] += abs(firstThirdInterval - firstThirdMaxComf)

	#PosChangeCount
	if posChange:
		if 1 in secondNoteFingering and (noteInterval * interval.Interval(firstNote.pitch, secondNote.pitch).semitones >= 0
								   and (firstThirdInterval > firstThirdMaxPrac or firstThirdInterval < firstThirdMinPrac)):
			output[0] += 2
		else:
			output[0] += 1

	return output


def ParnWeakFinger(thirdNoteFingering):
	if [4] == thirdNoteFingering or [5] == thirdNoteFingering:
		return 1

	return 0


def Parn345(firstNoteFingering, secondNoteFingering, thirdNoteFingering):
	if firstNoteFingering[-1] in [3, 4, 5] and set(secondNoteFingering) & set([3, 4, 5]) and \
		thirdNoteFingering[0] in [3, 4, 5] and len(secondNoteFingering) == 1:
		return 1

	return 0


def Parn34(secondNoteFingering, thirdNoteFingering):
	if 3 in secondNoteFingering and 4 in thirdNoteFingering:
		return 1

	return 0


def Parn4OnBlack(secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	secondNoteOnBlack = False
	thirdNoteOnBlack = False
	try:
		secondNoteOnBlack = secondNote.pitch.accidental is not None and secondNote.pitch.accidental.name != 'natural'
	except:
		secondNoteOnBlack = False

	try:
		thirdNoteOnBlack = thirdNote.pitch.accidental is not None and thirdNote.pitch.accidental.name != 'natural'
	except:
		thirdNoteOnBlack = False

	if(secondNoteFingering[-1] == 3 and not secondNoteOnBlack and \
		thirdNoteFingering[0] == 4 and thirdNoteOnBlack) or \
		(secondNoteFingering[-1] == 4 and secondNoteOnBlack and \
		thirdNoteFingering[0] == 3 and not thirdNoteOnBlack):
		return 1

	return 0


def Parn1OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote):
	output = 0

	if len(secondNoteFingering) == 0 and secondNote is not None:
		return output


	secondNoteOnBlack = False
	thirdNoteOnBlack = False
	firstNoteOnBlack = False
	try:
		secondNoteOnBlack = secondNote.pitch.accidental is not None and secondNote.pitch.accidental.name != 'natural'
	except:
		secondNoteOnBlack = False

	try:
		thirdNoteOnBlack = thirdNote.pitch.accidental is not None and thirdNote.pitch.accidental.name != 'natural'
	except:
		thirdNoteOnBlack = False

	try:
		firstNoteOnBlack = firstNote.pitch.accidental is not None and firstNote.pitch.accidental.name != 'natural'
	except:
		firstNoteOnBlack = False

	if 1 in secondNoteFingering and secondNoteOnBlack:
		output += 1

	if thirdNote is not None:
		if not thirdNoteOnBlack and secondNoteFingering[-1] == 1 and secondNoteOnBlack:
			output += 2

	if firstNote is not None:
		if not firstNoteOnBlack and secondNoteFingering[0] == 1 and secondNoteOnBlack:
			output += 2

	return output


def Parn5OnBlack(firstNote, secondNote, secondNoteFingering, thirdNote):
	output = 0

	if len(secondNoteFingering) == 0 and secondNote is not None:
		return output

	if 5 in secondNoteFingering and secondNote.pitch.accidental is not None:
		if(secondNote.pitch.accidental.name == 'natural'):
			return output

		# if firstNote is not None:
		# 	if firstNote.pitch.accidental is None and secondNoteFingering[0] == 5:
		# 		output += 2
		# 	elif firstNote.pitch.accidental.name == 'natural' and secondNoteFingering[0] == 5:
		# 		output += 2

		# if thirdNote is not None:
		# 	if thirdNote.pitch.accidental is None and secondNoteFingering[-1] == 5:
		# 		output += 2
		# 	elif thirdNote.pitch.accidental.name == 'natural' and secondNoteFingering[-1] == 5:
		# 		output += 2
		if firstNote is not None:
			if secondNoteFingering[0] == 5:
				acc = firstNote.pitch.accidental
				if acc is None or acc.name == 'natural':
					output += 2

		if thirdNote is not None:
			if secondNoteFingering[-1] == 5:
				acc = thirdNote.pitch.accidental
				if acc is None or acc.name == 'natural':
					output += 2

	return output


def ParnThumbPassing(isLeftHand, noteInterval, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	output = 0
	secondNoteOnBlack = False
	thirdNoteOnBlack = False
	try:
		secondNoteOnBlack = secondNote.pitch.accidental is not None and secondNote.pitch.accidental.name != 'natural'
	except:
		secondNoteOnBlack = False

	try:
		thirdNoteOnBlack = thirdNote.pitch.accidental is not None and thirdNote.pitch.accidental.name != 'natural'
	except:
		thirdNoteOnBlack = False


	if (1 in secondNoteFingering and isLeftHand and noteInterval > 0) or (1 in secondNoteFingering and not isLeftHand and noteInterval < 0):
		if secondNoteOnBlack == thirdNoteOnBlack:
			output += 1
		elif secondNoteOnBlack and not thirdNoteOnBlack:
			output += 3

	if (1 in thirdNoteFingering and isLeftHand and noteInterval < 0) or (1 in thirdNoteFingering and not isLeftHand and noteInterval > 0):
		if secondNoteOnBlack == thirdNoteOnBlack:
			output += 1
		elif not secondNoteOnBlack and thirdNoteOnBlack:
			output += 3

	return output

def getFingering(note, keepSign = False):
	fingering = []
	for a in note.articulations:
		if isinstance(a, articulations.Fingering):
			fingering = a.fingerNumber
			if not keepSign:
				fingering = abs(fingering)
			#if greater than 5 then this is a substitution fingering and needs to be split
			#this substitute format is custom and part of the PIGconversion script
			if int(fingering) > 5:
				fingering = [int(digit) for digit in str(fingering)]
			else:
				fingering = [int(fingering)]
	return fingering

def getFingeringChord(chord, keepSign = False):
	fingerings = []
	for a in chord.articulations:
		if isinstance(a, articulations.Fingering):
			allFingerings = str(a.fingerNumber).split('\n')
			# allFingerings = allFingerings.split('\n')
			for fingering in allFingerings:
				fingering = int(fingering)
				if not keepSign:
					fingering = abs(fingering)
				#if greater than 5 then this is a substitution fingering and needs to be split
				#this substitute format is custom and part of the PIGconversion script
				if int(fingering) > 5:
					fingering = [int(digit) for digit in str(fingering)]
				else:
					fingering = fingering

				fingerings.append(fingering)

	return fingerings

# Expects event as a [note/chord] object, fingerings as [1] or [1, 3]
def getInternalScore(event, fingerings, isLeftHand):
	internalScore = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	if len(event) < 2:
		return internalScore

	for pair in combinations(range(len(event)), 2):
		fingering1 = fingerings[pair[0]]
		fingering2 = fingerings[pair[1]]
				
		FingeringPairTableLine = getParncuttDistances(fingering1, fingering2)

		#convert the parncutt distances for lefthand and descending steps
		descending = fingering1 > fingering2
		tableFlipped = (isLeftHand and not descending) or (not isLeftHand and descending)
		if tableFlipped:
			FingeringPairTableLine = [-item for item in FingeringPairTableLine]
			FingeringPairTableLine.reverse()

		noteInterval = interval.Interval(event[pair[0]].pitch, event[pair[1]].pitch).semitones
		minComf = FingeringPairTableLine[1]
		minRel = FingeringPairTableLine[2]
		maxRel = FingeringPairTableLine[3]
		maxComf = FingeringPairTableLine[4]

		span =  ParnSpan(noteInterval, minRel, maxRel, [fingering1], [fingering2], tableFlipped)
		internalScore = np.array(internalScore) + np.array([ParnStretch(noteInterval, minComf, maxComf), span[0], span[1], 0, 0, 0, 0, 0, 0, 0, 0, 0])

	return internalScore

def normalizeScore(parts, isLeftHand):
	# Normalize piece by moving notes to the correct hand
	for part in parts:
		measureCounter = 1
		iterating = True
		while(iterating):
			nextMeasure = part.measure(measureCounter)
			if(nextMeasure is not None):
				for element in nextMeasure:
					if isinstance(element, music21.note.Note):
						fingering = getFingering(element, True)
						if(not isLeftHand and fingering[0] < 0 or isLeftHand and fingering[0] > 0):
							parent_stream = element.activeSite
							offset = element.offset
							parent_stream.remove(element)
							measureToAddTo = None
							if(isLeftHand):
								measureToAddTo = parts[0].measure(measureCounter)
							else:
								measureToAddTo = parts[1].measure(measureCounter)
							existingItems = measureToAddTo.getElementsByOffset(offset)
							for item in existingItems:
								itemToReplaceFound = False
								if isinstance(item, note.Rest):
									measureToAddTo.remove(item)
									measureToAddTo.insert(offset, element)
									itemToReplaceFound = True
								elif isinstance(item, note.Note):
									measureToAddTo.remove(item)
									existingNoteFingering = getFingering(item)
									elementFingering = getFingering(element)
									newChord = chord.Chord([item.pitch, element.pitch])
									newChord.articulations.append(articulations.Fingering(existingNoteFingering[0]))
									newChord.articulations.append(articulations.Fingering(elementFingering[0]))
									measureToAddTo.insert(offset, newChord)
									itemToReplaceFound = True
								elif isinstance(item, chord.Chord):
									measureToAddTo.remove(item)
									elementFingering = getFingering(element)
									item.add(element.pitch)
									item.articulations.append(articulations.Fingering(elementFingering[0]))
									measureToAddTo.insert(offset, item)
									itemToReplaceFound = True
							
							if itemToReplaceFound == False:
								measureToAddTo.insert(offset, element)

				measureCounter += 1
			else:
				iterating = False
				isLeftHand = not isLeftHand

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
		firstNote = None
		firstEventAllFingerings = [0]
		#middle note in sequence
		secondEvent = None
		secondEventAllFingerings = [0]
		#third note in sequence
		thirdNote = None
		thirdEventAllFingerings = [0]

		for thirdEvent in part.recurse().notes:
			if isinstance(thirdEvent, music21.harmony.Harmony):
				continue
			elif thirdEvent.isChord:
				thirdEventAllFingerings = getFingeringChord(thirdEvent)
				thirdEvent = thirdEvent.notes
			else:
				thirdEventAllFingerings = [getFingering(thirdEvent)]
				thirdEvent = [thirdEvent]
				

			#calculate internal scores for the chord
			internalScore = getInternalScore(thirdEvent, thirdEventAllFingerings, isLeftHand)
			scoreCount = np.array(scoreCount)
			scoreCount += internalScore

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
			
			for score in unnaggregatedScore:
				print(score)
				scoreCount += score

			# scoreCount = np.array(scoreCount) + np.array(aggregatedScore)

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
						firstNote = secondEvent[j] # Why second event here??
						unnaggregatedScore.append([0, 0, 0, 0, 0, 0, 0, 0, 0, Parn1OnBlack(firstNote, secondNote, secondNoteFingering, None), 
								Parn5OnBlack(firstNote, secondNote, secondNoteFingering, None), 0])
				else:
					unnaggregatedScore.append([0, 0, 0, 0, 0, 0, 0, 0, 0, Parn1OnBlack(None, secondNote, secondNoteFingering, None), 
								Parn5OnBlack(None, secondNote, secondNoteFingering, None), 0])
			
		aggregatedScore = np.max(np.array(unnaggregatedScore), axis=0)

		scoreCount = np.array(scoreCount) + np.array(aggregatedScore)


	return scoreCount, totalNotes

def chord_to_first_note(n):
    if n is None:
        return None
    if n.isChord:
        new_note = note.Note(n.pitches[0])
        new_note.duration = n.duration
        return new_note
	
    return n

def normalize_fingering(f):
    if f is None:
        return []

    if isinstance(f, list):
        if len(f) == 0:
            return []
        if all(isinstance(x, int) for x in f):
            return f
        if all(isinstance(x, list) and len(x) == 1 for x in f):
            return [x[0] for x in f]

    if isinstance(f, int):
        return [abs(f)]
	
    return []

def getParncuttGivenNotes(isLeftHand, firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	firstNoteFingering = normalize_fingering(firstNoteFingering)
	secondNoteFingering = normalize_fingering(secondNoteFingering)
	thirdNoteFingering = normalize_fingering(thirdNoteFingering)

	if secondNote is None:
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

	#print(firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering, sum(scoreCount), scoreCount)
  
	return scoreCount

# Notes should be the pure object, not in []. Fingerings should be in [] like [1], [1, 3, 5], etc
def getParncuttGivenNotesDP(isLeftHand, firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering):
	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

	firstNoteFingering = normalize_fingering(firstNoteFingering)
	secondNoteFingering = normalize_fingering(secondNoteFingering)
	thirdNoteFingering = normalize_fingering(thirdNoteFingering)

	if secondNote is None:
		scoreCount[5] += ParnWeakFinger(firstNoteFingering)
		#print(firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering, sum(scoreCount), scoreCount)
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
  
	#print(firstNote, firstNoteFingering, secondNote, secondNoteFingering, thirdNote, thirdNoteFingering, sum(scoreCount), scoreCount)

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
				#print(item)
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