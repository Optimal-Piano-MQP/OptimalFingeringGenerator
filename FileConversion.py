from music21 import *
from pathlib import Path

def file2Stream(fname):
	path_obj = Path(fname)
	file_extension = path_obj.suffix

	if(file_extension == '.txt'):
		return convertPIGtoMusic21(fname)

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