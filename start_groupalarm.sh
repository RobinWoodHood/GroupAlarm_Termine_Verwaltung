#!/bin/bash

# Fehlerbehandlung
set -e

# Verzeichnis des Skripts ermitteln
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# In das Verzeichnis wechseln
cd "$SCRIPT_DIR"

# Virtuelle Umgebung aktivieren
if [ -f "./.venv13/bin/activate" ]; then
    source ./.venv13/bin/activate
else
    echo "Fehler: .venv13 nicht gefunden!"
    read -p "Drücke Enter zum Schließen..."
    exit 1
fi

# Python Skript ausführen
python ./groupalarm_cli.py

# Falls das Skript beendet wird, warte auf Enter
echo "Skript beendet."
read -p "Drücke Enter zum Schließen..."