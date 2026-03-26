# Contract: CLI Application

**Scope**: `cli/app.py` — Textual App entry point and `groupalarm_cli.py` launcher

## CLI Entry Point

**Command**:
```bash
python groupalarm_cli.py [--org-id ORG_ID] [--dry-run] [--verbose]
```

**Arguments**:
| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| --org-id | int | No | from config | Override organization ID for this session |
| --dry-run | flag | No | False | Prevent all server mutations, log payloads |
| --verbose | flag | No | False | Enable DEBUG-level logging for troubleshooting |

**Environment Variables**:
| Variable | Required | Description |
|----------|----------|-------------|
| GROUPALARM_API_KEY | Yes | Personal Access Token for GroupAlarm API |

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Normal exit |
| 1 | Missing API key or fatal configuration error |

---

## Key Bindings (Main Screen)

| Key | Action | Context |
|-----|--------|---------|
| ↑/↓ | Navigate appointment list | List focused |
| Enter | Select appointment → open detail | List focused |
| / | Focus filter bar | Any |
| Ctrl+F | Search appointments by name/description | Any |
| e | Enter edit mode | Detail panel focused |
| n | Create new appointment | Any |
| d | Delete selected appointment | Appointment selected |
| x | Export filtered list to Excel | Any |
| s | Save changes (triggers confirmation) | Edit mode |
| Escape | Cancel edit / close panel / clear filter | Context-dependent |
| ? | Open help overlay | Any |
| q | Quit application (with unsaved changes guard) | Any |
| r | Refresh appointment list from API | Any |

---

## Screen Flow

```
Launch
  ├─ API key missing? → Error screen → Exit(1)
  ├─ No config / no org ID? → Setup prompt → Save config (file perms 600) → Main screen
  └─ Config OK → Main screen
       ├─ [DRY-RUN BANNER if --dry-run active]
       ├─ Appointment list (left panel)
       │    ├─ Filter bar (top: labels toggle list + date range + search)
       │    └─ Scrollable list (name [truncated], dates, labels [by name+color])
       ├─ Detail panel (right panel)
       │    ├─ No selection → Help/how-to overview
       │    ├─ Read-only view (all fields + recurrence in human-readable form)
       │    └─ Edit mode (editable fields, modified fields highlighted with color + asterisk)
       ├─ [s] Save → Confirmation dialog (side-by-side diff for updates)
       │    ├─ Confirm → API call (UI locked + loading indicator) → Success → Refresh list
       │    └─ Cancel → Return to edit mode
       ├─ [n] New → Detail form (defaults from config: duration 4h) → [s] Save → Confirm → Create → Refresh
       ├─ [d] Delete → Confirmation dialog (name + warning)
       │    ├─ Recurring? → Strategy selector first
       │    ├─ Confirm → API call → Success → Refresh list
       │    └─ Cancel → Return
       ├─ [x] Export → File path prompt (default: appointments_YYYY-MM-DD.xlsx) → Overwrite check → Export
       ├─ [?] Help → Modal overlay with all bindings
       ├─ [←/Esc with unsaved changes] → Save/Discard/Cancel prompt
       ├─ [Ctrl+C] → Cancel in-flight API call → Return to stable state
       └─ [q] Quit → Unsaved changes guard → Exit(0)
```
