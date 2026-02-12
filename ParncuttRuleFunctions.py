from music21 import *
from music21 import note
import music21
import numpy as np
from itertools import combinations
from FileConversion import file2Stream
import copy

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

def RepeatFingering(noteInterval, firstNoteFingering, secondNoteFingering):
	if noteInterval != 0 and firstNoteFingering[0] == secondNoteFingering[0]:
		return 2
	return 0

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
						if element.tie and element.tie.type in ('continue', 'stop'):
							continue
						fingering = getFingering(element, True)
						if not fingering:
							continue
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