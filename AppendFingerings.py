from music21 import articulations

#for fingerings in form [[1], [2], [3]]
'''def addFingeringToPart(part, fingering):
    notes = part.recurse().notes
    num_notes = len(notes)
    i = len(fingering) - 1
    j = 1

    while i >= 0:
        cur_note = notes[num_notes-j]

        if cur_note.tie and cur_note.tie.type in ('continue', 'stop'):
            j += 1
            continue

        if cur_note.isNote:
            cur_note.articulations.append(articulations.Fingering(fingering[i][0]))
            j += 1
            i -= 1

        elif cur_note.isChord:
            for k in range (0, len(cur_note.pitches)):
                cur_note.articulations.append(articulations.Fingering(fingering[i][0]))
                i -= 1
            j += 1'''

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

        if note.tie and note.tie.type in ('continue', 'stop'):
            if note.isChord:
                if note.pitches == notes[i - 1].pitches:
                    j += 1
                    continue
            else:
                if note.pitch in notes[i - 1].pitches:
                    j += 1
                    continue

        f = fingering[i - j]

        if chord.tie and chord.tie.type in ('continue', 'stop'):
            indexes = [chord.pitches.index(pitch) for pitch in note.pitches]
            f = [f[index] for index in indexes]


        #if note.isNote:
        #    note.articulations.append(articulations.Fingering(f[0]))

        #elif note.isChord:
        f.reverse()
        count = 0
        chordFingering = []
        for k in range(0, len(f)):
            if note.isChord:
                if len(chordFingering) == 0:
                    chordFingering = f[k:k+len(note.pitches)]
                    chordFingering.reverse()

                note.articulations.append(articulations.Fingering(chordFingering[count]))
                count += 1
                if count == len(note.pitches):
                    count = 0
                    chordFingering = []
                    n += 1
                    if i + n < num_notes:
                        note = notes[i + n]
            else:
                note.articulations.append(articulations.Fingering(f[k]))
                n = min(n + 1, num_notes - 1)
                if i + n < num_notes:
                    note = notes[i + n]

        n -= 1