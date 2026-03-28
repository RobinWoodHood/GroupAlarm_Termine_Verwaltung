# Data Model: TUI Detail Panel UX Overhaul

**Feature**: 003-tui-detail-ux-overhaul  
**Date**: 2026-03-28  
**Source**: Feature spec + API schemas (`appointment.openapi.json`, `users.openapi.json`)

## Entities

### Appointment (existing — extended for display)

The core scheduling entity. Already defined in `framework/appointment.py` as a dataclass.

| Field | Type | Description |
|---|---|---|
| id | int \| None | Server-assigned appointment ID |
| name | str | Appointment title |
| description | str | Free-text description (may contain GA-IMPORTER tokens) |
| startDate | datetime | Start time (UTC internally, Europe/Berlin for display) |
| endDate | datetime | End time |
| organizationID | int | Owning organization |
| labelIDs | list[int] | Associated label IDs |
| isPublic | bool | Whether exported to public iCal. **Default changes to False in create mode** |
| keepLabelParticipantsInSync | bool | Auto-sync label members to participants. **Newly exposed in create/edit form** |
| reminder | int \| None | Minutes before start for push notification (0–10080) |
| notificationDate | datetime \| None | When to send invitation notification |
| feedbackDeadline | datetime \| None | After this time, feedback no longer accepted |
| timezone | str | IANA timezone for DST (default "UTC") |
| participants | list[AppointmentParticipant] | Invited users (see below) |
| recurrence | dict \| None | Recurrence pattern (existing, not changed) |

### AppointmentParticipant (new typed representation)

Currently stored as `List[Dict[str, Any]]` in the Appointment dataclass. This feature adds a structured representation for display purposes.

| Field | Type | Description |
|---|---|---|
| userID | int | The invited user's ID |
| labelID | int \| None | If set, participant was added via this label. If 0 or None, participant was added directly |
| feedback | int | Feedback status: 0 = no feedback, 1 = accepted, 2 = declined |
| feedbackMessage | str | Optional text message attached to feedback |
| appointmentID | int | The appointment this participation belongs to |
| startDate | str \| None | For recurring appointments: specific occurrence |

**Derived classifications**:
- **Direct participant**: `labelID` is 0 or None
- **Label participant**: `labelID` > 0

**Feedback grouping**:
- **Zugesagt (accepted)**: `feedback == 1`
- **Abgesagt (declined)**: `feedback == 2`
- **Keine Rückmeldung (pending)**: `feedback == 0`

### OrganizationUser (new — from Users API)

Represents a member of the organization. Used for:
1. Resolving participant IDs to human names
2. Type-ahead suggestions when adding direct participants

| Field | Type | Description |
|---|---|---|
| id | int | User ID (matches `AppointmentParticipant.userID`) |
| name | str | First name |
| surname | str | Last name / family name |
| email | str | Email address |
| pending | bool | Whether invitation is still pending |

**Display name**: `"{name} {surname}"`

### AppConfig (existing — documented for example config)

Application configuration loaded from `.groupalarm.toml`.

| Field | TOML Key | Type | Default | Description |
|---|---|---|---|---|
| organization_id | general.organization_id | int \| None | None | GroupAlarm organization ID |
| timezone | general.timezone | str | "Europe/Berlin" | Display timezone (IANA) |
| date_range_days | defaults.date_range_days | int | 30 | Default appointment range to load |
| default_label_ids | defaults.label_ids | list[int] | [] | Pre-selected label filter IDs |
| default_appointment_duration_hours | defaults.appointment_duration_hours | int | 4 | Duration for new appointments |

## Relationships

```
Organization (1) ──── (*) OrganizationUser
Organization (1) ──── (*) Appointment
Appointment  (1) ──── (*) AppointmentParticipant
OrganizationUser (1) ──── (*) AppointmentParticipant  [via userID]
Label (1) ──── (*) AppointmentParticipant  [via labelID, 0 = direct]
```

## State Transitions

### Detail Panel Focus States

```
LIST_FOCUSED ──[Enter/Right]──> DETAIL_READ_ONLY
DETAIL_READ_ONLY ──[Left]──> LIST_FOCUSED  (triggers UnsavedChangesDialog if dirty)
DETAIL_READ_ONLY ──[E]──> DETAIL_EDIT_MODE
LIST_FOCUSED ──[E]──> DETAIL_EDIT_MODE
DETAIL_EDIT_MODE ──[Ctrl+S]──> Confirm → DETAIL_READ_ONLY
DETAIL_EDIT_MODE ──[Escape]──> DETAIL_READ_ONLY  (Left/Right stay in edit mode for text cursor)
DETAIL_READ_ONLY ──[Left, if dirty]──> UnsavedChangesDialog → (Save|Discard → LIST_FOCUSED | Cancel → DETAIL_READ_ONLY)
```

### Feedback Status Values

```
0 (NO_FEEDBACK) → "Keine Rückmeldung" group
1 (ACCEPTED)    → "Zugesagt" group
2 (DECLINED)    → "Abgesagt" group
```

## Validation Rules

| Entity | Rule |
|---|---|
| Appointment.name | Required, non-empty |
| Appointment.startDate | Must be a valid datetime |
| Appointment.endDate | Must be after startDate |
| Appointment.organizationID | Required, positive integer |
| Appointment.isPublic | Boolean (Ja/Nein in UI) |
| Appointment.keepLabelParticipantsInSync | Boolean (Ja/Nein in UI) |
| Appointment.reminder | 0–10080 minutes if set |
| Participant user input | Must resolve to a valid OrganizationUser.id |
| Label input | Must resolve to a valid label name from the directory |
