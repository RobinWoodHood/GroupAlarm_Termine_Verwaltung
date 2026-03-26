# Quickstart: GroupAlarm TUI

## Prerequisites

- Python ≥ 3.11
- GroupAlarm Personal Access Token

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. **Set your API key** (one-time, in your shell profile):

   ```bash
   # Linux/macOS
   export GROUPALARM_API_KEY="your-personal-access-token"

   # Windows PowerShell
   $env:GROUPALARM_API_KEY = "your-personal-access-token"
   ```

2. **First launch** — the tool will prompt for your Organization ID and create `.groupalarm.toml`:

   ```bash
   python groupalarm_cli.py
   ```

3. **Optional**: Edit `.groupalarm.toml` to set defaults:

   ```toml
   [general]
   organization_id = 12345
   timezone = "Europe/Berlin"

   [defaults]
   date_range_days = 30
   default_appointment_duration_hours = 4
   label_ids = []             # empty = show all labels
   ```

## Usage

```bash
# Normal launch
python groupalarm_cli.py

# Override org ID for this session
python groupalarm_cli.py --org-id 67890

# Dry-run mode (no server mutations)
python groupalarm_cli.py --dry-run

# Verbose logging (DEBUG level to groupalarm_cli.log)
python groupalarm_cli.py --verbose
```

## Key Bindings

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate list |
| Enter | Select appointment |
| / | Filter |
| Ctrl+F | Search appointments |
| e | Edit mode |
| n | New appointment |
| d | Delete appointment |
| x | Export to Excel |
| s | Save (with confirmation) |
| Esc | Cancel / back |
| ? | Help overlay |
| q | Quit (with unsaved changes check) |

## Workflow Examples

### Browse & filter
Launch → list loads → press `/` → select labels → set date range → browse filtered list.

### Edit an appointment
Select appointment → press `e` → modify fields → press `s` → review diff in confirmation → confirm.

### Export for offline editing
Apply filters → press `x` → enter file path → `.xlsx` created → edit in Excel → re-import with existing `Runner`.

### Delete an appointment
Select appointment → press `d` → confirmation shows name & warning → confirm → removed.

## Running Tests

```bash
pytest -q
```
