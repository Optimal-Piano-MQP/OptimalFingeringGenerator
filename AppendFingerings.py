from music21 import articulations

#for fingerings in form [[1, 3, 5], [1]]
def addFingeringToPart(part, fingering):
    partChord = part.chordify()
    chords = partChord.flatten().notes
    notes = part.flatten().notes
    num_chords = len(chords)
    num_notes = len(notes)
    n = 0
    j = 0

    for i in range(num_chords):
        chord = chords[i]
        note = notes[i+n]

        if chord.tie and chord.tie.type in ('continue', 'stop'):
            if chord.isChord:
                if chord.pitches == chords[i - 1].pitches:
                    j += 1
                    continue
                elif len(chord.pitches) == 1 and chord.pitches[0] in chords[i - 1].pitches:
                    j += 1
                    continue

        f = fingering[i - j]

        if len(note.pitches) != len(chord.pitches):
            indexes = []
            tiedPitches = []
            for k in range(0, len(chord.pitches)):
                chordNote = chord.notes[k]
                if chordNote.tie and chordNote.tie.type in ('continue', 'stop'):
                    tiedPitches.append(chordNote.pitch)
                    continue

                indexes.append(k)

            for k in range(0, len(chord.pitches)):
                checkNote = notes[i+n+k]
                if len(checkNote.pitches) + k > len(chord.pitches):
                    break

                if checkNote.isChord:
                    for l in range(0, len(checkNote.pitches)):
                        if checkNote.notes[l].tie and checkNote.notes[l].tie.type in ('continue', 'stop'):
                            if checkNote.pitches[l] in tiedPitches:
                                indexes.append(chord.pitches.index(checkNote.pitches[l]))
                    k += len(checkNote.pitches) - 1

                else:
                    if checkNote.tie and checkNote.tie.type in ('continue', 'stop'):
                        if checkNote.pitches[0] in tiedPitches:
                            indexes.append(chord.pitches.index(checkNote.pitches[0]))
            indexes = list(set(indexes))
            indexes.sort()
            f = [f[index] for index in indexes]

        f.reverse()
        count = 0
        chordFingering = []
        for k in range(0, len(f)):
            if note.isChord:
                if len(chordFingering) == 0:
                    chordFingering = f[k:k + len(note.pitches)]
                    chordFingering.reverse()

                note.articulations.append(articulations.Fingering(chordFingering[count]))
                count += 1
                if count == len(note.pitches):
                    count = 0
                    n += 1
                    if i + n < num_notes:
                        note = notes[i + n]
            else:
                note.articulations.append(articulations.Fingering(f[k]))
                n = min(n + 1, num_notes - 1)
                if i + n < num_notes:
                    note = notes[i + n]

        n -= 1