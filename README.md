# OptimalFingeringGenerator

This program automatically generates ergonomic and efficient piano fingerings for uploaded scores.

It uses dynamic programming to optimize the **Parncutt Score**, based on the model described in:
*Richard Parncutt – "An Ergonomic Model of Keyboard Fingering for Melodic Fragments"*

This program was released alongside a research paper, titled: Optimal Piano Fingering Using Dynamic Programming and Physiological Constraints

## To Run:
1. Clone (download) this repository onto your machine
2. Make sure Python is installed on your machine, or else the program won't run
3. Make sure MuseScore4 is installed on your machine, or else the program won't run
    - If you are receiving errors upon running after installing MuseScore, edit the following line in App.py (line 16) to match your system:
    - MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
4. Run the program in one of the following ways:
    - Opening OptimalFingeringGenerator in an IDE (such as VSCode) and running App.py
    - Navigating to OptimalFingeringGenerator in the terminal and entering: python App.py
5. The following lines should appear. Open the http link from "Running on http://xxx.x.x.x:xxxx" in your browser
     * Serving Flask app 'App'
     * Debug mode: on
    WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
     * Running on http://xxx.x.x.x:xxxx
    Press CTRL+C to quit
     * Restarting with stat
     * Debugger is active!
     * Debugger PIN: xxx-xxx-xxx
6. Use the user interface to upload a file and generate fingerings

File formats:
Input  : .xml .mxl .musicxml
Output : .xml .pdf

## Contents:
- Analysis Folder          : Code and results from our algorithm against other programs
- Archive Folder           : Archived code that isn't in use
- FilterDataset Folder     : Code to filter out the solo piano pieces from PDMX
- uploads Folder           : All files uploaded to the program

- Algorithm.py             : Algorithm code to determine fingerings
- App.py                   : User interface
- AppendFingerings.py      : Code to add generated fingerings back to the original score
- FileConversion.py        : Code for file conversions
- ParncuttRuleFunctions.py : Piano fingering rules as described by Richard Parncutt
- ParncuttRulesHandling.py : Code for receiving the Parncutt score for a piece or selected notes