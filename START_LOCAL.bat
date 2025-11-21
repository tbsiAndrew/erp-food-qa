@echo off
REM ============================================================
REM   ERP Food QA - Local Startup (No Docker Required)
REM ============================================================
echo.
echo Starting ERP Food QA Application (Local Mode)
echo ============================================================
echo.

call .venv\Scripts\activate

REM Create storage directories if they don't exist
if not exist "storage\images" mkdir storage\images
if not exist "storage" mkdir storage

REM Initialize database (SQLite)
echo Initializing SQLite database...
python -c "from app.db import DB; db = DB(); print('✅ Database initialized successfully')"

echo.
echo ✅ Image saving is ENABLED by default for /inspect endpoint
echo 📁 Images will be saved to: storage/images/
echo 🌐 View saved images at: http://localhost:8000/storage/images/
echo.
echo Starting FastAPI server on http://localhost:8000
echo API documentation available at http://localhost:8000/docs
echo.

REM Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
