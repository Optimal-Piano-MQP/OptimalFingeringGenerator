from music21 import *
import numpy as np
from pathlib import Path

def file2Stream(fname):
	path_obj = Path(fname)
	file_extension = path_obj.suffix
	#print(f"Extension using pathlib.Path.suffix: {file_extension}")

	if(file_extension == '.txt'):
		return convertPIGtoMusic21(fname)
		#return PIG2Stream(fname)

	return converter.parse(fname)

def convertPIGtoMusic21(filePath):
	with open(filePath, 'r') as file:
		fileContent = file.read()

	#create the score object with left and right hand parts
	score = stream.Score()

	right_hand = stream.Part()
	right_hand.id = 'RightHand'
	right_hand.append(instrument.Piano())
	right_hand.append(clef.TrebleClef())

	left_hand = stream.Part()
	left_hand.id = 'LeftHand'
	left_hand.append(instrument.Piano())
	left_hand.append(clef.BassClef())

	#split the file into the line components, removing first and last lines
	contentSplitByLine = fileContent.split('\n')
	contentSplitByLine.pop(0)
	contentSplitByLine.pop(len(contentSplitByLine) - 1)

	#keep track of the time stamp of the end of the last note to check for rests
	RHLastOffset = 0
	RHLastOnset = 0
	LHLastOffset = 0
	LHLastOnset = 0

	#convert each line into a note object and insert in correct location
	chordNotes = []
	for line in contentSplitByLine:
		lineSplitByTab = line.split('\t')

		#create new note object and assign pitch value
		nextNote = note.Note(lineSplitByTab[3])

		#Problem: PIG denotes notes in terms of physical seconds between play events
		#no clue how to convert

		#extract the currentFingering
		currentFingering = lineSplitByTab[7]
		if '_' in currentFingering:
			#these are the currentFingerings that are notated for a finger switch
			substitutedFingering = currentFingering.split('_')
			try:
				substitutedFingering = [abs(int(item)) for item in substitutedFingering]
				substitutedFingeringConcat = int(str(substitutedFingering[0]) + str(substitutedFingering[1]))
				nextNote.articulations.append(articulations.Fingering(substitutedFingeringConcat))
			except Exception as e:
				nextNote.articulations.append(articulations.Fingering(abs(int(substitutedFingering[0]))))
		else:
			currentFingering = articulations.Fingering(abs(int(currentFingering)))
		nextNote.articulations.append(currentFingering)

		#add to correct hand part at the offset
		if(lineSplitByTab[6] == '0'):
			#print(chordNotes, nextNote, RHLastOnset, lineSplitByTab[1])
			#if(float(lineSplitByTab[1]) - RHLastOnset < .0001):
				#chordNotes.append(nextNote)
			#else:
				#if len(chordNotes) > 1:
					#right_hand.append(chord.Chord(chordNotes))
				#elif len(chordNotes) == 1:
					#right_hand.append(chordNotes[0])
			#chordNotes = [nextNote]
			right_hand.append(nextNote)
			RHLastOffset = float(lineSplitByTab[2])
			RHLastOnset = float(lineSplitByTab[1])

		else:
			#if(float(lineSplitByTab[1]) - LHLastOffset > .1):
				#left_hand.append(note.Rest())
			#left_hand.insert(offset, nextNote)
			left_hand.append(nextNote)
			LHLastOffset = float(lineSplitByTab[2])

	score.insert(0, right_hand)
	score.insert(0, left_hand)

	#create file for visual check of system
	return score

"""Parncutt Functions:"""

def getParncuttDistances(fingeringA, fingeringB):
	sortedFingerings = sorted([fingeringA, fingeringB])
	fingeringIndex = sortedFingerings[0] * 2 + sortedFingerings[1] * 3

	if(fingeringA == fingeringB):
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
		return 2 * abs(minComf - noteInterval)
	elif noteInterval > maxComf:
		return 2 * abs(maxComf - noteInterval)
	
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
			output[1] += abs(noteInterval) - abs(maxRel)
		else:
			output[1] += 2 * (abs(noteInterval) - abs(maxRel))
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


def getParncuttRuleScore(score):
	#TODO:
	#Fix rests
	#look for extentions to these rules in other papers
	#normalization???? currently value/#notesInPiece

	scoreCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
	totalNotes = 0
	parts = score.parts.stream().iter()
	for part in parts:
		totalNotes += len(part.notes)

		isLeftHand = (part.clef.name == clef.BassClef().name)
		noteA = None
		noteAFingering = None
		noteB = None
		noteBFingering = None
		noteCFingering = None

		for noteC in part.notes:
			if hasattr(noteC, 'articulations'):
				for a in noteC.articulations:
					if isinstance(a, articulations.Fingering):
						noteCFingering = a.fingerNumber
						if noteCFingering > 5:
							noteCFingering = [int(digit) for digit in str(noteCFingering)]
						else:
							noteCFingering = [noteCFingering]

			scoreCount = np.array(scoreCount) + np.array(getParncuttGivenNotes(isLeftHand, noteA, noteAFingering, noteB, noteBFingering, noteC, noteCFingering))

			noteA = noteB
			noteAFingering = noteBFingering
			noteB = noteC
			noteBFingering = noteCFingering

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

	# Rule 2: Small-span rule: per semitone less than minrel, 1 for includes thumb, 2 for not including thumb
	# Rule 3: Large-span rule: per semitone greater than maxrel, 1 for includes thumb, 2 for not including thumb
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


"""Run Parncutt on all PIG Files"""

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


#RunTime 10/24/25: ~3:30

#RunTime 10/25/25: ~3:30
#Avg and Maximum values
#Stretch:         range: 037-1: 0   031-1: 1722   avg:  264.983
#SmallSpan:       range: 143-1: 9   031-1: 2061   avg:  230.428
#LargeSpan:       range: 037-1: 63  031-1: 4048   avg:  621.338
#PosChangeCount:  not coded
#PosChangeSize:   not coded
#WeakFinger:      range: 037-1: 14  034-4: 592    avg:  95.940
#3-4-5:           range: 065-1: 0   001-1: 84     avg:  18.154
#3-4:             range: 016-3: 0   031-1: 60     avg:  7.201
#4OnBlack:        range: 012-4: 0   031-1: 45     avg:  2.853
#1OnBlack:        range: 001-1: 0   034-4: 1098   avg:  75.164
#5OnBlack:        range: 012-3: 0   034-4: 276    avg:  30.736
#ThumbPass:       not coded

#10/27/25 Normalized (value/#notesInPiece)
#Stretch       : min: 037-1: 0.000   max: 143-1: 7.655   avg: 0.838
#SmallSpan     : min: 028-3: 0.081   max: 107-1: 1.476   avg: 0.724
#LargeSpan     : min: 012-1: 0.345   max: 143-1: 7.397   avg: 1.922
#PosChangeCount: min: 042-1: 0.361   max: 090-1: 0.864   avg: 0.610
#PosChangeSize : min: 042-1: 1.637   max: 108-1: 7.966   avg: 3.213
#WeakFinger    : min: 042-1: 0.144   max: 085-1: 0.482   avg: 0.298
#3-4-5         : min: 065-1: 0.000   max: 013-1: 0.269   avg: 0.059
#3-4           : min: 016-3: 0.000   max: 044-1: 0.092   avg: 0.023
#4OnBlack      : min: 012-4: 0.000   max: 089-1: 0.071   avg: 0.009
#1OnBlack      : min: 001-1: 0.000   max: 091-1: 0.580   avg: 0.230
#5OnBlack      : min: 012-3: 0.000   max: 046-1: 0.372   avg: 0.093
#ThumbPassing  : min: 005-2: 0.000   max: 090-1: 0.288   avg: 0.023

#10/28/25 Moved to GitHub
#Runtime: about 10 seconds at most
#Values are the same as above, which was the hope
#Stretch       : min: 037-1: 0.000   max: 143-1: 7.655   avg: 0.838
#SmallSpan     : min: 028-3: 0.081   max: 107-1: 1.476   avg: 0.724
#LargeSpan     : min: 012-1: 0.345   max: 143-1: 7.397   avg: 1.922
#PosChangeCount: min: 042-1: 0.361   max: 090-1: 0.864   avg: 0.610
#PosChangeSize : min: 042-1: 1.637   max: 108-1: 7.966   avg: 3.213
#WeakFinger    : min: 042-1: 0.144   max: 085-1: 0.482   avg: 0.298
#3-4-5         : min: 065-1: 0.000   max: 013-1: 0.269   avg: 0.059
#3-4           : min: 016-3: 0.000   max: 044-1: 0.092   avg: 0.023
#4OnBlack      : min: 012-4: 0.000   max: 089-1: 0.071   avg: 0.009
#1OnBlack      : min: 074-2: 0.250   max: 142-2: 1.424   avg: 0.742
#5OnBlack      : min: 012-3: 0.000   max: 046-1: 0.372   avg: 0.094
#ThumbPassing  : min: 005-2: 0.000   max: 090-1: 0.288   avg: 0.023

import matplotlib.pyplot as plt

rules = ["Stretch", "SmallSpan", "LargeSpan", "PosChangeCount", "PosChangeSize", "WeakFinger", "3-4-5", "3-4", "4OnBlack", "1OnBlack", "5OnBlack", "ThumbPassing"]
dataToPlot = allParncuttScoresNormalized

# make data:
x = .5 + np.arange(len(dataToPlot))
for i in range(len(dataToPlot[0][1])):
	y = []
	xlabels = []
	for n in dataToPlot:
		y.append(n[1][i])
		xlabels.append(n[0])

	# plot
	fig, ax = plt.subplots(figsize=(10, 5))
	ax.bar(x, y, width=.8, edgecolor="white", linewidth=0.7, align='center')
	ax.set_xticks(np.arange(len(x)), labels=xlabels)
	print(f"#{rules[i]:<14}: min: {xlabels[y.index(min(y))]}: {min(y):.3f}   max: {xlabels[y.index(max(y))]}: {max(y):.3f}   avg: {sum(y) / len(y):.3f}")

	plt.show()

"""PIG2Stream function taken from PianoPlayer"""

# @title
def PIG2Stream(fname, beam=0, time_unit=.5, fixtempo=0):
	"""
	Convert a PIG text file to a music21 Stream object.
	time_unit must be multiple of 2.
	beam = 0, right hand
	beam = 1, left hand.
	"""
	from music21 import stream, note, chord
	from music21.articulations import Fingering
	import numpy as np

	f = open(fname, "r")
	lines = f.readlines()
	f.close()

	#work out note type from distribution of durations
	#triplets are squashed to the closest figure
	durations = []
	firstonset = 0
	blines=[]
	for l in lines:
		if l.startswith('//'): continue
		_, onset, offset, name, _, _, channel, _ = l.split()
		onset, offset = float(onset), float(offset)
		if beam != int(channel): continue
		if not firstonset:
			firstonset = onset
		if offset-onset<0.0001: continue
		durations.append(offset-onset)
		blines.append(l)
	durations = np.array(durations)
	logdurs = -np.log2(durations)
	mindur = np.min(logdurs)
	expos = (logdurs-mindur).astype(int)
	if np.max(expos) > 3:
		mindur = mindur + 1
	#print(durations, '\nexpos=',expos, '\nmindur=', mindur)

	sf = stream.Part()
	sf.id = beam

	# first rest
	if not fixtempo and firstonset:
		r = note.Rest()
		logdur = -np.log2(firstonset)
		r.duration.quarterLength = 1.0/time_unit/pow(2, int(logdur-mindur))
		sf.append(r)

	n = len(blines)
	for i in range(n):
		if blines[i].startswith('//'): continue
		_, onset, offset, name, _, _, _, finger = blines[i].split()
		onset, offset = float(onset), float(offset)
		name = name.replace('b', '-')

		chordnotes = [name]
		for j in range(1, 5):
			if i+j<n:
				noteid1, onset1, offset1, name1, _, _, _, finger1 = blines[i+j].split()
				onset1 = float(onset1)
				if onset1 == onset:
					name1 = name1.replace('b', '-')
					chordnotes.append(name1)

		if len(chordnotes)>1:
			an = chord.Chord(chordnotes)
		else:
			an = note.Note(name)
			if '_' not in finger:
				x = Fingering(abs(int(finger)))
				x.style.absoluteY = 20
			an.articulations.append(x)

		if fixtempo:
			an.duration.quarterLength = fixtempo
		else:
			logdur = -np.log2(offset - onset)
			an.duration.quarterLength = 1.0/time_unit/pow(2, int(logdur-mindur))
		#print('note/chord:', an, an.duration.quarterLength, an.duration.type, 't=',onset)

		sf.append(an)

		# rest up to the next
		if i+1<n:
			_, onset1, _, _, _, _, _, _ = blines[i+1].split()
			onset1 = float(onset1)
			if onset1 - offset > 0:
				r = note.Rest()
				if fixtempo:
					r.duration.quarterLength = fixtempo
				logdur = -np.log2(onset1 - offset)
				d = int(logdur-mindur)
				if d<4:
					r.duration.quarterLength = 1.0/time_unit/pow(2, d)
					sf.append(r)
	return sf