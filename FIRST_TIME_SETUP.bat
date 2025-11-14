@echo off
REM ============================================================
REM   QUICK START - First Time Setup
REM ============================================================
echo.
echo ============================================================
echo   ERP Food QA - First Time Setup
echo ============================================================
echo.
echo This will:
echo  1. Install Python dependencies
echo  2. Initialize the database
echo  3. Create storage directories
echo  4. Test the setup
echo  5. Start the application
echo.
pause

REM Install dependencies
echo.
echo [1/5] Installing Python dependencies...
echo ============================================================
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Failed to install dependencies
    echo Please check your Python installation and try again
    pause
    exit /b 1
)

REM Initialize database
echo.
echo [2/5] Initializing database...
echo ============================================================
python -c "from app.db import DB; db = DB(); print('✅ Database initialized')"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Failed to initialize database
    pause
    exit /b 1
)

REM Create storage directories
echo.
echo [3/5] Creating storage directories...
echo ============================================================
if not exist "storage\images" mkdir storage\images
echo ✅ Storage directories created

REM Test setup
echo.
echo [4/5] Testing setup...
echo ============================================================
python test_local_setup.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️  Some tests failed, but you can still try running the application
    pause
)

REM Start application
echo.
echo [5/5] Starting application...
echo ============================================================
echo.
echo ✅ Setup complete!
echo.
echo Access the application at:
echo  - API Docs:  http://localhost:8000/docs
echo  - Dashboard: http://localhost:8000/
echo.
echo Press Ctrl+C to stop the server
echo.
pause

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
