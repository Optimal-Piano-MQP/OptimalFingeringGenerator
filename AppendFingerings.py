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
    notes = part.flatten().notes
    num_notes = len(notes)
    j = 0

    for i in range(num_notes):
        note = notes[i]
        if note.tie and note.tie.type in ('continue', 'stop'):
            j += 1
            continue

        if note.isNote:
            note.articulations.append(articulations.Fingering(fingering[i - j][0]))

        elif note.isChord:
            for k in range(0, len(note.pitches)):
                note.articulations.append(articulations.Fingering(fingering[i - j][k]))