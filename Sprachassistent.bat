@echo off
setlocal

echo Starte Sprachassistent (Sprachassistent-Code\sprachassistent.py)

if not exist "%~dp0sprachassistentenv\Scripts\python.exe" goto venv_fehlt

"%~dp0sprachassistentenv\Scripts\python.exe" "%~dp0Sprachassistent-Code\sprachassistent.py"

echo Sprachassistent beendet, Fenster kann geschlossen werden.

pause
endlocal
exit /b 1

:venv_fehlt
echo Fuehre das Setup (setup.bat) aus, bevor du den Sprachassistenten startest.
pause
endlocal
exit /b 1