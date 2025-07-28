@echo off
REM Run the Persona-Driven Document Intelligence on all collections

echo ========================================================
echo     Persona-Driven Document Intelligence Processor 
echo             Processing All Collections
echo ========================================================
echo.

REM Get directory of this script
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%"

REM Create models directory if it doesn't exist
if not exist "models" mkdir models

REM Process all collections with the main script
echo Processing all collections...
python main.py --base_dir .
echo.

echo All collections processed successfully!
echo ========================================================

pause
