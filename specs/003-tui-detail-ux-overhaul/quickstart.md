# Quickstart: TUI Detail Panel UX Overhaul

**Feature**: 003-tui-detail-ux-overhaul  
**Date**: 2026-03-28

## Prerequisites

- Python ≥ 3.11
- Virtual environment activated (`.venv`)
- Dependencies: `pip install -r requirements.txt`
- Environment variable: `GROUPALARM_API_KEY` set to a valid Personal-Access-Token
- Configuration: copy `.groupalarm.example.toml` → `.groupalarm.toml` and set `organization_id`

## Start the TUI

```bash
python groupalarm_cli.py
```

Or with dry-run mode (no server writes):
```bash
python groupalarm_cli.py --dry-run
```

## Verify New Features

### 1. Live Detail Preview

1. The appointment list loads on the left
2. Press **Up/Down** arrow keys in the list
3. The detail panel on the right updates instantly to show the highlighted appointment

### 2. Focus Switching

1. Press **Right arrow** or **Enter** → focus moves to the detail panel
2. Press **Up/Down** → scroll through detail content
3. Press **Left arrow** → focus returns to the list (only in read-only mode)
4. Press **E** from the list → detail panel enters edit mode directly

### 3. Field Label Colors

- All field labels (Name:, Start:, Labels:, etc.) display in yellow (matching the separator line)

### 4. Edit Mode Navigation

1. Press **E** to enter edit mode
2. Use **Left/Right** arrows to navigate the text cursor within a field
3. Use **Up/Down** arrows to move between input fields (on single-line fields)
4. In the multi-line Beschreibung field: **Up/Down** navigate lines; Down on the **last line** or Up on the **first line** moves to the adjacent field
5. Use **Tab** to move forward (or accept a suggestion)
6. Use **Escape** to leave edit mode (returns to read-only — then Left returns to list)
7. Use **Ctrl+S** to save

### 5. Participants and Feedback

1. Select an appointment with participants
2. See "Direkte Teilnehmer" section (if any directly added participants)
3. See feedback lists: Zugesagt / Abgesagt / Keine Rückmeldung
4. Feedback messages appear below participant names where present

### 6. Create Appointment with New Defaults

1. Press **N** to create a new appointment
2. Verify: "Öffentlich" defaults to "Nein"
3. Verify: "Label-Sync" defaults to "Ja"
4. In "Teilnehmer" field, type a name → see suggestions from org users
5. Press **Tab** to accept a suggestion

### 7. Example Config

1. Check that `.groupalarm.example.toml` exists in the repo root
2. Copy it to `.groupalarm.toml`, set your `organization_id`
3. Restart the TUI — verify settings take effect

## Run Tests

```bash
pytest -q
```

All new features have corresponding unit tests.
