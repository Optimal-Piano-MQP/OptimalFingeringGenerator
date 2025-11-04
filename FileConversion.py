from music21 import *
from pathlib import Path

def file2Stream(fname):
	path_obj = Path(fname)
	file_extension = path_obj.suffix
	#print(f"Extension using pathlib.Path.suffix: {file_extension}")

	if(file_extension == '.txt'):
		return convertPIGtoMusic21(fname)
		#return PIG2Stream(fname)

	print("parsing using", file_extension)
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
	RHLastOnset = 0
	LHLastOnset = 0

	#convert each line into a note object and insert in correct location
	chordNotesRH = []
	chordNotesLH = []
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
				#Some substitution fingerings are formatted improperly, like 4_ , with no second note
				nextNote.articulations.append(articulations.Fingering(abs(int(substitutedFingering[0]))))
		else:
			currentFingering = articulations.Fingering(abs(int(currentFingering)))
			nextNote.articulations.append(currentFingering)

		#add to correct hand part at the offset
		if(lineSplitByTab[6] == '0'):
			#print(chordNotes, nextNote, RHLastOnset, lineSplitByTab[1])
			if(float(lineSplitByTab[1]) - RHLastOnset < .0001):
				chordNotesRH.append(nextNote)
			else:
				if len(chordNotesRH) > 1:
					newChord = chord.Chord(chordNotesRH)
					for item in newChord.notes:
						if hasattr(item, 'articulations'):
							for a in item.articulations:
								if isinstance(a, articulations.Fingering):
									newChord.articulations.append(a)
					right_hand.append(newChord)
				elif len(chordNotesRH) == 1:
					right_hand.append(chordNotesRH[0])
				chordNotesRH = [nextNote]
			RHLastOnset = float(lineSplitByTab[1])

		else:
			if(float(lineSplitByTab[1]) - LHLastOnset < .0001):
				chordNotesLH.append(nextNote)
			else:
				if len(chordNotesLH) > 1:
					newChord = chord.Chord(chordNotesLH)
					for item in newChord.notes:
						if hasattr(item, 'articulations'):
							for a in item.articulations:
								if isinstance(a, articulations.Fingering):
									newChord.articulations.append(a)
					left_hand.append(newChord)
				elif len(chordNotesLH) == 1:
					left_hand.append(chordNotesLH[0])
				chordNotesLH = [nextNote]
			LHLastOnset = float(lineSplitByTab[1])


	if len(chordNotesRH) > 1:
		newChord = chord.Chord(chordNotesRH)
		for item in newChord.notes:
			if hasattr(item, 'articulations'):
				for a in item.articulations:
					if isinstance(a, articulations.Fingering):
						newChord.articulations.append(a)
		right_hand.append(newChord)
		
	if len(chordNotesLH) > 1:
		newChord = chord.Chord(chordNotesLH)
		for item in newChord.notes:
			if hasattr(item, 'articulations'):
				for a in item.articulations:
					if isinstance(a, articulations.Fingering):
						newChord.articulations.append(a)
		left_hand.append(newChord)

	score.insert(0, right_hand)
	score.insert(0, left_hand)

	return score

"""PIG2Stream function taken from PianoPlayer for testing and observation"""

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