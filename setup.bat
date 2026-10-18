@echo off
setlocal
title Sprachassistent Setup

if /i "%~1"=="--resume" goto run

echo Sprachassistent Setup
choice /C JN /M "Willst du das Setup durchfuehren?"
if errorlevel 2 exit /b 0

:run
echo.
echo Pruefe Python...

python --version >nul 2>&1
if not errorlevel 1 goto ollama

set "INSTALLER=%TEMP%\python-installer.exe"
echo Lade Python herunter...
curl -fL "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -o "%INSTALLER%"
if errorlevel 1 goto error

echo Installiere Python...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 goto error
del "%INSTALLER%" 2>nul

echo Starte Setup neu...
start "" "%~f0" --resume
exit /b 0

:ollama
echo Python Installiert
echo.
echo Pruefe Ollama...
where ollama >nul 2>&1
if not errorlevel 1 goto ollama_ready

set "OLLAMA_INSTALLER=%TEMP%\OllamaSetup.exe"
curl -fL "https://ollama.com/download/OllamaSetup.exe" -o "%OLLAMA_INSTALLER%"
if errorlevel 1 goto error

echo Starte die Ollama Installation ueber das geoeffnete Fenster
start /wait "" "%OLLAMA_INSTALLER%"
if errorlevel 1 goto error
del "%OLLAMA_INSTALLER%" 2>nul

set "PATH=%PATH%;%LOCALAPPDATA%\Programs\Ollama"

:ollama_ready
echo Ollama Installiert
set "OLLAMA_EXE="
for /f "delims=" %%I in ('where ollama 2^>nul') do (
    set "OLLAMA_EXE=%%I"
    goto ollama_found
)

:ollama_found
if not defined OLLAMA_EXE (
    echo Ollama wurde nicht gefunden.
    goto error
)

curl -fsS http://localhost:11434/api/tags >nul 2>&1
if not errorlevel 1 goto models

start "Ollama Server" /min "%OLLAMA_EXE%" serve
set /a attempts=0

:wait_server
timeout /t 2 /nobreak >nul
curl -fsS http://localhost:11434/api/tags >nul 2>&1
if not errorlevel 1 goto models
set /a attempts+=1
if %attempts% geq 30 goto error
goto wait_server

:models
echo.
echo Pruefe ob qwen2.5:1.5b-instruct vorhanden...
"%OLLAMA_EXE%" list | findstr /B /C:"qwen2.5:1.5b-instruct" >nul
if errorlevel 1 (
    echo qwen2.5:1.5b-instruct nicht vorhanden, lade herunter:
    "%OLLAMA_EXE%" pull qwen2.5:1.5b-instruct
    if errorlevel 1 goto error
) else (
    echo qwen2.5:1.5b-instructwen ist bereits vorhanden.
)

echo.
echo Pruefe ob gemma4:e4b...
"%OLLAMA_EXE%" list | findstr /B /C:"gemma4:e4b" >nul
if errorlevel 1 (
    echo gemma4:e4b nicht vorhanden, lade herunter:
    "%OLLAMA_EXE%" pull gemma4:e4b
    if errorlevel 1 goto error
) else (
    echo gemma4:e4b ist bereits vorhanden.
)

echo.
echo Starte Sprachassistent Setup...

if not exist "%~dp0Sprachassistent-Code\setup.py" (
    echo setup.py wurde nicht gefunden!
    goto error
)

python "%~dp0Sprachassistent-Code\setup.py"
if errorlevel 1 (
    echo Fehler beim Python Setup.
    pause
    exit /b 1
)

echo Setup erfolgreich abgeschlossen.
pause
exit /b 0

:error
echo.
echo Ein Fehler ist aufgetreten.
pause
exit /b 1
