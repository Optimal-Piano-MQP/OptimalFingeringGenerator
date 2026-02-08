from RecursiveScaleTest import dp
from FileConversion import file2Stream
from AppendFingerings import addFingeringToPart
from ParncuttRulesUpdated import getParncuttRuleScore

# Chord testing

score = file2Stream("chord_testing.musicxml")
rh = score.parts[0]

optimal = dp(rh, 0)[0]
print(optimal.fingerings, optimal.score)
fingering = optimal.fingerings
# print(optimal.fingerings)
addFingeringToPart(rh, fingering)

score.write("musicxml", "chord_testing_out.musicxml")


# Canon in d

# score = file2Stream("canon-in-d.musicxml")
# rh = score.parts[0]
# lh = score.parts[1]

# optimal_rh = dp(rh, 0)
# optimal_lh = dp(lh, 1)
# fingering_rh = optimal_rh[0].fingerings
# fingering_lh = optimal_lh[0].fingerings

# addFingeringToPart(rh, fingering_rh)
# addFingeringToPart(lh, fingering_lh)

# score.write("musicxml", "canon-in-d-out.musicxml")

# print(getParncuttRuleScore(score))


# Test file

# score = file2Stream("cscale_optimal.musicxml")
# print(getParncuttRuleScore(score))