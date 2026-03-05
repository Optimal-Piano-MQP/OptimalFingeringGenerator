import os
from pathlib import Path
from music21 import *
from ParncuttRuleFunctions import *

def getCommonFileNames(dir1, dir2):
	dir1Files = set()
	dir1Ext = ""
	dir1Path = Path(dir1)
	for f in dir1Path.iterdir():
		if(f.suffix == ".txt"):
			continue

		if dir1Ext == "":
			dir1Ext = f.suffix

		dir1Files.add(f.stem)

	dir2Files = set()
	dir2Ext = ""
	dir2Path = Path(dir2)
	for f in dir2Path.iterdir():
		if(f.suffix == ".txt"):
			continue

		if dir2Ext == "":
			dir2Ext = f.suffix

		dir2Files.add(f.stem)

	#print(dir1Files, dir2Files)
	dir1Files = [file.replace('_output', '') for file in dir1Files]
	dir2Files = [file.replace('_output_dp13', '') for file in dir2Files]
	#print(dir1Files, dir2Files)
	commonFiles = [file.replace('_output', '') for file in dir1Files if (file in dir2Files or file.replace('_output_dp13', '') in dir2Files or file + '_output_dp13' in dir2Files)]
	#commonFiles = list(dir1Files.intersection(dir2Files))
	#print(commonFiles)
	return [dir1Ext, dir2Ext, commonFiles]

def compareAccuracyAgainstPIG(dir):
	PIGPath = "./FingeringFiles"
	output = []
	dirPath = Path(dir)
	for f in dirPath.iterdir():
		if(f.suffix not in ['.musicxml', '.xml']):
			continue

		fileNumber = f.stem[0:3]
		fingeringFiles = []
		for root, _, files in os.walk(PIGPath):
			for file in files:
				if fileNumber in file:
					fingeringFiles.append(os.path.join(root, file))

		accuracys = []
		for fingeringFile in fingeringFiles:
			accuracys.append(compareAccuracyBetweenFiles(fingeringFile, f, isPIG1=True))

		output.append([max(accuracys), fileNumber])
		print(f"{max(accuracys)}, {f}")

	output.sort(key=lambda x:x[0])
	return output


def compareAccuracyBetweenDirectories(dir1, dir2):
	accuracyOutputs = []
	commonFiles = getCommonFileNames(dir1, dir2)
	dir1Ext = commonFiles[0]
	dir2Ext = commonFiles[1]
	commonFiles = commonFiles[2]
	filesChecked = 0.0
	totalFiles = len(commonFiles)
	
	for f in commonFiles:
		dir1FPath = os.path.join(dir1, f + "_output" + dir1Ext)
		dir2FPath = os.path.join(dir2, f + "_output_dp13" + dir2Ext)
		fAccuracy = compareAccuracyBetweenFiles(dir1FPath, dir2FPath)
		filesChecked += 1
		print(f"{filesChecked / totalFiles:.2%}, {fAccuracy}, {f}")
		accuracyOutputs.append([fAccuracy, f])

	accuracyOutputs.sort(key=lambda x:x[0])
	return accuracyOutputs

def file2Stream(fname, isPIG=False):
	path_obj = Path(fname)
	file = path_obj.stem
	suffix = path_obj.suffix

	if(isPIG):
		return convertPIGtoMusic21(fname)

	try:
		score = converter.parse(fname)
		return score
	except:
		try:
			fileSansOutput = file.replace('_output', '')
			score = converter.parse(os.path.join(path_obj.parent, fileSansOutput + suffix))
			return score
		except:
			fileWithOutput = file + '_output'
			score = converter.parse(os.path.join(path_obj.parent, fileWithOutput + suffix))
			return score


def compareAccuracyBetweenFiles(file1, file2, isPIG1=False, isPIG2=False):
	score1 = file2Stream(file1, isPIG1)
	score2 = file2Stream(file2, isPIG2)
	score1Parts = score1.recurse().parts
	score2Parts = score2.recurse().parts
	notesTheSame = 0.0
	totalNotes = 0.0

	for score1Part, score2Part in zip(score1Parts, score2Parts):
		score1Notes = score1Part.flatten().notes
		score2Notes = score2Part.flatten().notes
		totalNotes += len(score1Notes)

		for note1, note2 in zip(score1Notes, score2Notes):
			try:
				if note1.isNote:
					if(set(getFingering(note1)) == set(getFingering(note2))):
						notesTheSame += 1
				elif note1.isChord:
					if(set(getFingeringChord(note1)) == set(getFingeringChord(note2))):
						notesTheSame += 1
			except Exception as e:
				print(e, file1, note1, note2, getFingering(note1), getFingering(note2))

	return notesTheSame / totalNotes

dir1 = "./PDMXOutput"
dir2 = "./PDMXOutputDP13"
output = compareAccuracyBetweenDirectories(dir1, dir2)
#with open(f"PIGaccuracyOutput_PianoPlayer_Random.txt", "w") as f:
#	for line in output:
#		f.write(f"{line[0]},\t{line[1]}\n")
#	f.close()
#print(output)
accuracyTotal = 0
for accuracy in output:
	accuracyTotal += accuracy[0]

print(f"{accuracyTotal/len(output):.2%} average accuracy over {len(output)} files")
#print(len(output))

#output = compareAccuracyAgainstPIG("./Output_PianoPlayer/PIG_Output_PianoPlayer")
#with open(f"PIGaccuracyOutput_PianoPlayer.txt", "w") as f:
#	for line in output:
#		f.write(f"{line[0]},\t{line[1]}\n")
#	f.close()