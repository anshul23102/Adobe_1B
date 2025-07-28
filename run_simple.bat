@echo off
REM Run the Persona-Driven Document Intelligence processor
echo =========================================================
echo        Persona-Driven Document Intelligence
echo =========================================================
echo.

REM Ensure we're in the correct directory
cd %~dp0

REM Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in your PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Run for all collections by default
echo Processing all collections...
python main.py --base_dir .

echo.
echo =========================================================
echo Processing complete! Results saved to each collection directory.
echo =========================================================
pause
