from music21 import articulations

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

def addFingeringToPart(part, fingering):
    notes = part.recurse().notes
    num_notes = len(notes)
    i = len(fingering) - 1
    j = 1

    while i >= 0:
        cur_note = notes[num_notes - j]

        if cur_note.tie and cur_note.tie.type in ('continue', 'stop'):
            j += 1
            continue

        if cur_note.isNote:
            cur_note.articulations.append(articulations.Fingering(fingering[i][0]))
            j += 1
            i -= 1

        elif cur_note.isChord:
            for k in range (0, len(cur_note.pitches)):
                cur_note.articulations.append(articulations.Fingering(fingering[i][k]))
            i -= 1
            j += 1