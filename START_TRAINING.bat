@echo off
REM Quick start script for YOLOv8 training
REM Uses the virtual environment automatically

echo ============================================================
echo YOLOv8 Bread Quality Training - Quick Start
echo ============================================================
echo.

REM Activate venv and run training
".venv\Scripts\python.exe" train_yolo_bread.py %*

echo.
echo ============================================================
echo Training Complete!
echo ============================================================
pause
