# Contract: Detail Panel Widget

**Feature**: 003-tui-detail-ux-overhaul  
**Module**: `cli/widgets/detail_panel.py` — `DetailPanel`

## Navigation Contract

### Read-Only Mode

When the detail panel has focus in read-only mode:

| Key | Action |
|---|---|
| Up/Down | Scroll detail content vertically |
| E | Enter edit mode, focus first editable field |
| Left | Return focus to list (triggers unsaved-changes dialog if changes were made during a previous edit session) |

### Edit Mode

When the detail panel is in edit mode:

| Key | Action (on EditInput fields) |
|---|---|
| Left/Right | Navigate text cursor within the active input field (NO panel switching) |
| Up | Move focus to previous input field (no wrap at first field) |
| Down | Move focus to next input field (no wrap at last field) |
| Tab | Accept active suggestion (if any) placing cursor at end, else move to next field |
| Escape | Cancel edit mode, return to read-only (then Left returns to list) |
| Ctrl+S | Save (triggers confirmation dialog) |

| Key | Action (on TextArea — Beschreibung field) |
|---|---|
| Left/Right | Navigate text cursor within the field |
| Up | Move to previous line; if cursor is on the **first line**, move focus to previous field |
| Down | Move to next line; if cursor is on the **last line**, move focus to next field |
| Tab | Move focus to next field |
| Escape | Cancel edit mode, return to read-only |
| Ctrl+S | Save (triggers confirmation dialog) |

## Display Contract

### Field Labels

All field labels in both read-only and edit modes use CSS color `$accent` (yellow in default theme) for visual consistency with the detail panel border.

**CSS class**: `.field-label { color: $accent; }`

### Read-Only Sections

The detail panel renders the following sections in order:

1. **Grunddaten**: Name, Beschreibung
2. **Zeitplan**: Start, Ende
3. **Labels**: Comma-separated label names
4. **Optionen**: Öffentlich, Label-Sync
5. **Benachrichtigungen**: Erinnerung, Benachrichtigungsdatum
6. **Direkte Teilnehmer**: List of directly added participants (hidden if none)
7. **Feedback**: Three sub-lists — Zugesagt, Abgesagt, Keine Rückmeldung (hidden if no participants)

### Participant Feedback Display

Each feedback sub-list shows:
```
[Zugesagt] (3)
  Max Mustermann
  Erika Musterfrau
    "Komme gerne!"
  Hans Schmidt

[Abgesagt] (1)
  Lisa Müller
    "Bin im Urlaub"

[Keine Rückmeldung] (2)
  Peter Weber
  Anna Fischer
```

- Participant names: resolved via `UserService.get_display_name(userID)`
- Feedback messages: displayed below name in dim/secondary style
- Empty groups: hidden entirely

### Edit Form Fields

In create/edit mode, the form includes all existing fields plus:

| Field ID | Label | Input Type | Default (Create) |
|---|---|---|---|
| name | Name: | EditInput | "" |
| description | Beschreibung: | TextArea | "" |
| startDate | Start: | EditInput | Next full hour |
| endDate | Ende: | EditInput | Start + 4h |
| labels | Labels: | EditInput (with LabelSuggester) | "" |
| participants | Teilnehmer: | EditInput (with UserSuggester) | "" |
| isPublic | Öffentlich: | EditInput (Ja/Nein) | **"Nein"** |
| keepLabelParticipantsInSync | Label-Sync: | EditInput (Ja/Nein) | **"Ja"** |
| reminder | Erinnerung: | EditInput | "" |
| notificationDate | Benachrichtigung: | EditInput | "" |
