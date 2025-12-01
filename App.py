from ParncuttRules import allParncutt, generateRandomFingerings, getParncuttRuleScore, plotParncuttData
from FileConversion import file2Stream
from music21 import *
from flask import Flask, render_template_string, request
from jupyterlab.handlers.error_handler import TEMPLATE
from werkzeug.utils import secure_filename
import os
import numpy as np

#Required librarys: Music21, Flask, jupyterlab, 

#CMD to convert scorepdfs to mxml using audiveris
#Run from inside the dir with the pdf files
#FOR %i IN (*) DO "C:\Program Files\Audiveris\audiveris.exe" -batch -export -output "PATH/TO/OUTPUT" %i

"""Run Parncutt on all PIG Files"""
#beethoven-fur-elise-bagatelle-no-25-woo-59.musicxml
#musicxml file with no fingerings
#score = generateRandomFingerings(file2Stream("beethoven-fur-elise-bagatelle-no-25-woo-59.musicxml"))
#score.write("musicxml", "musicXMLTestingOutput.xml")
#print(getParncuttRuleScore(file2Stream("musicXMLTestingOutput.xml")))
#print(getParncuttRuleScore(score))

#allParncuttScore, allParncuttScoresNormalized = allParncutt()
#plotParncuttData(allParncuttScoresNormalized)

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Music File Upload</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        input[type=file], input[type=submit] { margin-top: 1em; }
        table { border-collapse: collapse; margin-top: 2em; }
        td, th { border: 1px solid #aaa; padding: 0.5em; text-align: center; }
    </style>
</head>
<body>
    <h1>Upload Musicxml, xml, or txt File(s) for Parncutt Scoring</h1>
    
    {% if filenames %}
        <h2>Uploaded Files</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Filename</th>
                <th>Total Notes</th>
                <th>Scores</th>
            </tr>
            {% for name, total, score_list in zip(filenames, total_notes, scores) %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ name }}</td>
                <td>{{ total }}</td>
                <td>{{ score_list }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" multiple required>
        <input type="submit" value="Upload & Analyze">
    </form>
</body>
</html>
"""

@app.route("/", methods = ["GET", "POST"])
def upload_file():
    all_scores = [] # list of scores
    all_totals = []
    all_scores_normalized = []
    filenames = []

    if request.method == "POST":
        files = request.files.getlist("file")

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                try:
                    ######THIS IS WHERE WE NEED THE ALGORITHM, CURRENTLY RANDOM
                    score = generateRandomFingerings(file2Stream(filepath))
                    score_counts, total_notes  = getParncuttRuleScore(score)

                    all_scores.append([int(x) for x in score_counts])
                    all_totals.append(total_notes)
                    all_scores_normalized.append([float(item / total_notes) for item in score_counts])
                    filenames.append(filename)


                except Exception as e:
                    return f"<h3>Error processing file {e}</h3>"

    return render_template_string(
        TEMPLATE,
        scores = all_scores,
        total_notes = all_totals,
        filenames = filenames,
        zip = zip
    )

if __name__ == "__main__":
    app.run(debug=True)

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

#11/2/25 Added Chords (no aggregation)
#Stretch       : min: 050-2: 0.029   max: 108-1: 121.586   avg: 7.553
#SmallSpan     : min: 080-1: 0.084   max: 102-1: 14.125   avg: 2.494
#LargeSpan     : min: 001-2: 0.690   max: 108-1: 108.560   avg: 11.899
#PosChangeCount: min: 042-1: 0.362   max: 108-1: 9.871   avg: 2.304
#PosChangeSize : min: 042-1: 1.643   max: 108-1: 73.034   avg: 13.675
#WeakFinger    : min: 042-1: 0.145   max: 108-1: 5.164   avg: 1.194
#3-4-5         : min: 080-1: 0.000   max: 108-1: 1.664   avg: 0.311
#3-4           : min: 040-1: 0.000   max: 145-1: 0.444   avg: 0.074
#4OnBlack      : min: 012-4: 0.000   max: 145-1: 0.371   avg: 0.033
#1OnBlack      : min: 074-2: 0.251   max: 012-6: 12.649   avg: 2.530
#5OnBlack      : min: 012-3: 0.000   max: 102-1: 4.172   avg: 0.436
#ThumbPassing  : min: 005-2: 0.000   max: 090-1: 3.077   avg: 0.104

#11/2/25 Added chord aggregation
#Stretch       : min: 050-2: 0.029   max: 108-1: 18.707   avg: 1.952
#SmallSpan     : min: 080-1: 0.084   max: 102-1: 2.977   avg: 1.230
#LargeSpan     : min: 001-2: 0.690   max: 108-1: 24.767   avg: 3.978
#PosChangeCount: min: 042-1: 0.362   max: 026-1: 1.336   avg: 0.816
#PosChangeSize : min: 042-1: 1.643   max: 108-1: 13.716   avg: 5.131
#WeakFinger    : min: 042-1: 0.145   max: 108-1: 0.845   avg: 0.411
#3-4-5         : min: 080-1: 0.000   max: 102-1: 0.648   avg: 0.214
#3-4           : min: 040-1: 0.000   max: 088-1: 0.172   avg: 0.048
#4OnBlack      : min: 012-4: 0.000   max: 145-1: 0.129   avg: 0.020
#1OnBlack      : min: 074-2: 0.251   max: 021-1: 2.855   avg: 1.165
#5OnBlack      : min: 012-3: 0.000   max: 102-1: 1.141   avg: 0.190
#ThumbPassing  : min: 005-2: 0.000   max: 090-1: 0.944   avg: 0.053