@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo.
echo ========================================
echo GroupAlarm Terminverwaltung - Installation
echo ========================================
echo.

REM Create virtual environment
echo [1/4] Erstelle Python-Umgebung...
python -m venv .venv
if errorlevel 1 (
    echo FEHLER: Python-Umgebung konnte nicht erstellt werden.
    echo Bitte stelle sicher, dass Python 3.11+ installiert ist.
    pause
    exit /b 1
)

REM Activate virtual environment
call .\.venv\Scripts\activate
if errorlevel 1 (
    echo FEHLER: Virtuelle Umgebung konnte nicht aktiviert werden.
    pause
    exit /b 1
)

REM Install requirements
echo [2/4] Installiere Python-Pakete...
pip install -r requirements.txt
if errorlevel 1 (
    echo FEHLER: Python-Pakete konnten nicht installiert werden.
    pause
    exit /b 1
)

REM Copy config template if it doesn't exist
echo [3/4] Erstelle Konfigurationsdatei...
if not exist .groupalarm.toml (
    if exist .groupalarm.example.toml (
        copy .groupalarm.example.toml .groupalarm.toml
        echo Konfigurationsdatei .groupalarm.toml erstellt.
    ) else (
        echo WARNUNG: .groupalarm.example.toml nicht gefunden.
    )
) else (
    echo Konfigurationsdatei existiert bereits.
)

REM Get API key from user
echo [4/4] Konfiguriere API-Zugang...
echo.
set /p API_KEY="Gebe deinen GroupAlarm API-Token ein (oder druecke Enter zum Ueberspringen): "

if not "!API_KEY!"=="" (
    REM Set environment variable for current session
    set GROUPALARM_API_KEY=!API_KEY!
    
    REM Set persistent environment variable for future sessions
    setx GROUPALARM_API_KEY "!API_KEY!" >nul
    
    echo.
    echo API-Token wurde gespeichert!
) else (
    echo.
    echo API-Token wird spaeter benoetigt. Du kannst ihn in der Umgebungsvariable
    echo GROUPALARM_API_KEY setzen oder beim Start des Tools eingeben.
)

echo.
set /p ORG_ID="Gebe deine Organization-ID ein (oder druecke Enter zum Ueberspringen): "

if not "!ORG_ID!"=="" (
    REM Update .groupalarm.toml with organization_id
    if exist .groupalarm.toml (
        powershell -Command "^
            (Get-Content '.groupalarm.toml') -replace 'organization_id\s*=\s*\d+', 'organization_id = !ORG_ID!' | Set-Content '.groupalarm.toml'
        "
        echo Organization-ID wurde in .groupalarm.toml gespeichert!
    )
) else (
    echo.
    echo Organization-ID wird spaeter benoetigt. Du kannst sie in der Datei
    echo '.groupalarm.toml' eintragen.
)

echo.
echo ========================================
echo Installation abgeschlossen!
echo ========================================
echo.
echo Naechste Schritte:
echo 1. Das Tool ist bereit zum Starten
echo 2. Starte das Tool mit 'start.bat' oder 'GroupAlarm TUI.bat.lnk'
echo.
pause