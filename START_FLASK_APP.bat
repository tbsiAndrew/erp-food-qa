@echo off
REM Activate the virtual environment
call .venv\Scripts\activate

REM Set camera index (change this to your DroidCam camera index)
REM To find your camera index: run the app and check console output
REM Common values: 0 (default), 1 (DroidCam), 2, 3, etc.
REM Leave commented to auto-detect
REM set CAMERA_INDEX=1

REM Run the Flask app
python web\app.py

REM Pause to keep the window open after execution
pause