# Feature Specification: TUI Detail Panel UX Overhaul

**Feature Branch**: `003-tui-detail-ux-overhaul`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "Detail panel live-preview on list navigation, keyboard-driven focus switching (Enter/Right → detail, Left → back to list, E → edit), highlighted field labels, arrow-key navigation in edit mode, direct participant display, three-column feedback lists (positive/negative/no feedback) with optional feedback messages, keepLabelParticipantsInSync toggle in creation, isPublic defaults to Nein, direct user addition with type-ahead suggestions, Tab to accept all suggestions, README modernization (remove old framework docs), and example config file."

## User Scenarios & Testing *(mandatory)*
### User Story 1 - Live Detail Preview on List Navigation (Priority: P1)

When a user navigates the appointment list with the Up/Down arrow keys, the detail panel immediately updates to show the currently highlighted appointment. This eliminates the extra step of confirming a selection and provides instant context.

**Why this priority**: This is the most fundamental interaction improvement — every user navigating appointments benefits from instant preview, making the entire TUI feel responsive.

**Independent Test**: Open the TUI with multiple appointments loaded, use Up/Down arrows in the list, and verify that the detail panel updates to reflect the highlighted appointment on every cursor movement.

**Acceptance Scenarios**:

1. **Given** the appointment list has focus and contains multiple appointments, **When** the user presses Up or Down arrow, **Then** the detail panel immediately updates to display the newly highlighted appointment's full details.
2. **Given** the detail panel is showing appointment A, **When** the user scrolls to appointment B with the arrow keys, **Then** the detail panel replaces A's content with B's content without any additional key press.
3. **Given** the list has only one appointment, **When** the user presses Up or Down, **Then** the detail panel remains stable and continues showing that appointment.

---

### User Story 2 - Keyboard-Driven Focus Switching (Priority: P1)

Users must be able to seamlessly move focus between the appointment list and the detail panel using keyboard shortcuts. Enter or Right arrow moves focus to the detail panel; Left arrow returns to the list. Pressing E from the list starts editing directly in the detail panel. When in the detail panel (read-only mode), Up/Down scrolls through the detail content and E enters edit mode. Leaving the detail panel while unsaved changes exist triggers a warning.

**Why this priority**: Mouse-free focus management is essential for efficient keyboard-first workflows — the core audience of a TUI.

**Independent Test**: Navigate from list to detail panel and back using only keyboard. Verify focus indicators, scroll behavior in the detail panel, direct edit entry from the list, and unsaved-changes warning.

**Acceptance Scenarios**:

1. **Given** focus is on the appointment list, **When** the user presses Enter or Right arrow, **Then** focus moves to the detail panel, the panel shows a visible focus indicator, and the user can scroll through detail content with Up/Down.
2. **Given** focus is on the detail panel in read-only mode, **When** the user presses Left arrow, **Then** focus returns to the appointment list at the same cursor position.
3. **Given** focus is on the appointment list with an appointment highlighted, **When** the user presses E, **Then** the detail panel enters edit mode for the displayed appointment and focus moves to the first editable field.
4. **Given** focus is on the detail panel in read-only mode, **When** the user presses E, **Then** the detail panel transitions to edit mode and focus moves to the first editable field.
5. **Given** the detail panel is in read-only mode with unsaved changes (edit was cancelled without saving), **When** the user presses Left arrow, **Then** an unsaved-changes warning dialog appears offering Save, Discard, or Cancel.
6. **Given** the detail panel is in edit mode, **When** the user presses Left or Right arrow, **Then** the cursor moves within the active text field (arrow keys do NOT trigger panel switching in edit mode).
7. **Given** the detail panel is in edit mode and the user wants to return to the list, **When** the user presses Escape, **Then** the panel returns to read-only mode, and the user can then press Left arrow to return to the list.

---

### User Story 3 - Highlighted Field Labels (Priority: P1)

All field description labels in the detail panel (e.g., "Name:", "Start:", "Labels:") are rendered with a highlight color matching the yellow separator line between list and detail panel. This makes scanning field names fast.

**Why this priority**: Visual readability directly reduces cognitive load and speeds up information retrieval — every user benefits on every screen view.

**Independent Test**: Open an appointment in the detail panel and verify that every field label uses the same yellow highlight color as the vertical separator border.

**Acceptance Scenarios**:

1. **Given** the detail panel displays an appointment in read-only mode, **When** the user looks at the panel, **Then** all field labels (Name, Beschreibung, Start, Ende, Labels, Öffentlich, Erinnerung, Benachrichtigung, Teilnehmer, Feedback) are rendered in the same yellow color as the vertical separator line.
2. **Given** the detail panel is in edit mode, **When** the user views the form, **Then** field labels retain their yellow highlight, clearly distinguishing them from editable input values.

---

### User Story 4 - Arrow Key Navigation in Edit Mode (Priority: P2)

While editing an appointment in the detail panel, the user can switch between input fields using not only Tab but also the Up/Down arrow keys. Up moves to the previous field, Down moves to the next field.

**Why this priority**: Arrow-key field navigation complements Tab and matches the mental model established in list navigation. Users do not need to learn a second pattern.

**Independent Test**: Enter edit mode, use Up/Down arrows to move between fields, and verify that cursor focus shifts correctly without losing entered data.

**Acceptance Scenarios**:

1. **Given** the detail panel is in edit mode with focus on a single-line field (EditInput), **When** the user presses Down arrow, **Then** focus moves to the next input field in document order.
2. **Given** the detail panel is in edit mode with focus on a single-line field, **When** the user presses Up arrow, **Then** focus moves to the previous input field.
3. **Given** focus is on the first field, **When** the user presses Up arrow, **Then** focus stays on the first field (no wrap-around).
4. **Given** focus is on the last field, **When** the user presses Down arrow, **Then** focus stays on the last field (no wrap-around).
5. **Given** data has been typed into a field, **When** the user presses Up or Down, **Then** the entered data is preserved in the field after focus moves away.
6. **Given** focus is on the multi-line Beschreibung field (TextArea) and the cursor is NOT on the last line, **When** the user presses Down arrow, **Then** the cursor moves to the next line within the TextArea (normal text navigation).
7. **Given** focus is on the Beschreibung field and the cursor IS on the last line, **When** the user presses Down arrow, **Then** focus moves to the next input field below.
8. **Given** focus is on the Beschreibung field and the cursor IS on the first line, **When** the user presses Up arrow, **Then** focus moves to the previous input field above.
9. **Given** focus is on the Beschreibung field and the cursor is NOT on the first line, **When** the user presses Up arrow, **Then** the cursor moves to the previous line within the TextArea (normal text navigation).

---

### User Story 5 - Direct Participant Display (Priority: P2)

The detail panel shows participants who were added directly to the appointment (not via label). These are participants whose labelID is 0 or null. Their names are displayed in a dedicated "Direkte Teilnehmer" section.

**Why this priority**: Users need visibility into who was explicitly added outside of label groups to understand the full participant picture.

**Independent Test**: View an appointment that has both label-assigned and directly-added participants, and verify that a "Direkte Teilnehmer" section lists only the directly added ones by name.

**Acceptance Scenarios**:

1. **Given** an appointment has participants with labelID = 0 or null, **When** the detail panel displays this appointment, **Then** a "Direkte Teilnehmer" section appears listing these participants by name.
2. **Given** an appointment has no directly added participants (all come from labels), **When** the detail panel displays, **Then** the "Direkte Teilnehmer" section is hidden.
3. **Given** an appointment has participants with and without label assignments, **When** displayed, **Then** only participants without a label assignment appear in the "Direkte Teilnehmer" section.

---

### User Story 6 - Participant Feedback Lists (Priority: P2)

The detail panel provides an expandable/collapsible section showing participants grouped into three lists: positive feedback (accepted), negative feedback (declined), and no feedback (pending). If a participant has a feedbackMessage, it is shown below their name. User names are resolved from the Users API.

**Why this priority**: Seeing who accepted, declined, or hasn't responded to an appointment is critical for planning and decision-making.

**Independent Test**: View an appointment with mixed participant feedback statuses. Verify three separate lists are shown with correct grouping and feedback messages displayed below names where present.

**Acceptance Scenarios**:

1. **Given** an appointment with participants who have positive, negative, and no-feedback statuses, **When** the detail panel shows the appointment, **Then** three labeled lists appear: "Zugesagt", "Abgesagt", and "Keine Rückmeldung" with participants sorted into the correct list.
2. **Given** a participant has a feedbackMessage, **When** their entry is shown in a feedback list, **Then** the feedbackMessage text appears directly below their name in a secondary/muted style.
3. **Given** a participant without a feedbackMessage, **When** their entry is shown, **Then** only their name appears with no empty line or placeholder.
4. **Given** all participants have the same feedback status (e.g., all accepted), **When** displayed, **Then** only the relevant list is shown and the other two lists are hidden or indicate zero entries.
5. **Given** a feedback list contains participants, **When** the user navigates to the feedback section, **Then** participant names are resolved to human-readable names (first name + surname) via the Users API.

---

### User Story 7 - Creation Defaults and New Fields (Priority: P2)

When creating a new appointment, the keepLabelParticipantsInSync option is exposed and defaults to Ja (true). The isPublic field defaults to Nein (false). These defaults match the most common organizational use case.

**Why this priority**: Correct defaults reduce errors — most appointments in this context are private and should keep label participants in sync.

**Independent Test**: Open the new-appointment form and verify that keepLabelParticipantsInSync shows "Ja" and isPublic shows "Nein" without any user action.

**Acceptance Scenarios**:

1. **Given** the user initiates appointment creation, **When** the creation form appears, **Then** keepLabelParticipantsInSync is set to "Ja" and isPublic is set to "Nein".
2. **Given** the creation form is open, **When** the user changes keepLabelParticipantsInSync to "Nein", **Then** the value is reflected in the created appointment payload.
3. **Given** the creation form is open, **When** the user changes isPublic to "Ja", **Then** the value is reflected in the created appointment payload.

---

### User Story 8 - Direct User Addition in Appointment Creation (Priority: P2)

When creating an appointment, users can add participants directly by name (not only via labels). A type-ahead suggestion field queries all available users in the organization and suggests matching names as the user types.

**Why this priority**: Not all participants are covered by labels. Direct user addition is essential for ad-hoc or cross-label appointments.

**Independent Test**: Start creating an appointment, begin typing a user name in the participants field, verify suggestions appear from the organization's user list, and confirm the selected user appears in the participant summary.

**Acceptance Scenarios**:

1. **Given** the appointment creation form is open, **When** the user starts typing in the "Teilnehmer" field, **Then** a suggestion list shows matching users from the organization (by name or surname).
2. **Given** a suggestion is shown, **When** the user presses Tab, **Then** the suggestion is accepted and the cursor moves to the end of the accepted text.
3. **Given** the user has added one participant, **When** they type a comma and begin typing another name, **Then** the suggestion applies only to the new token after the comma.
4. **Given** the user has selected multiple direct participants, **When** they save the appointment, **Then** the participants list in the payload includes the selected users with their user IDs.

---

### User Story 9 - Tab Accepts All Type-Ahead Suggestions (Priority: P1)

All type-ahead suggestion fields (labels, users) must accept the current suggestion when Tab is pressed. After accepting, the cursor must be positioned at the end of the accepted text.

**Why this priority**: Consistent Tab-accept behavior is a fundamental usability pattern across all suggestion fields — inconsistency creates confusion.

**Independent Test**: In any field with type-ahead (labels during editing, users during creation), type a partial match, press Tab, and verify the suggestion is accepted with the cursor at the end.

**Acceptance Scenarios**:

1. **Given** a label suggestion is showing in the label field, **When** the user presses Tab, **Then** the suggestion fills the field and the cursor sits at the end of the accepted value.
2. **Given** a user-name suggestion is showing in the participants field, **When** the user presses Tab, **Then** the suggestion fills the current token and the cursor sits at the end.
3. **Given** no suggestion is active, **When** the user presses Tab, **Then** focus moves to the next field as normal.

---

### User Story 10 - README Modernization (Priority: P3)

The README is updated to focus exclusively on the TUI-based workflow. All references to the old import framework (Mapper, Runner, Importer, CSV/Excel import, Token/UUID persistence, and related example code) are removed. The README describes installation, TUI startup, configuration, available keyboard shortcuts, and the supported workflows.

**Why this priority**: Documentation accuracy prevents confusion. The old framework is being deprecated and removed in the next release.

**Independent Test**: Read the README and verify it contains no references to Mapper, Runner, Importer, CSV/Excel import patterns, or the old `example_usage.py` workflow. Verify that TUI startup instructions and keyboard shortcuts are documented.

**Acceptance Scenarios**:

1. **Given** the README exists, **When** a user reads it, **Then** there are no mentions of Mapper, Runner, CSVImporter, ExcelImporter, Token/UUID, or `example_usage.py`.
2. **Given** the README exists, **When** a user reads the "Schnellstart" section, **Then** it describes starting the TUI via `groupalarm_cli.py` and basic configuration via `.groupalarm.toml`.
3. **Given** the README exists, **When** a user reads it, **Then** keyboard shortcuts for navigation, editing, filtering, and creation are documented.

---

### User Story 11 - Example Configuration File (Priority: P3)

A `.groupalarm.example.toml` file is provided in the repository root showing all available configuration options with comments and sensible example values.

**Why this priority**: An example config lowers the barrier to onboarding and documents all available options.

**Independent Test**: Verify that `.groupalarm.example.toml` exists, can be parsed by a TOML parser, and contains all configuration keys used by the application.

**Acceptance Scenarios**:

1. **Given** the repository is freshly cloned, **When** the user looks at the root directory, **Then** `.groupalarm.example.toml` is present with all configurable keys documented.
2. **Given** the example config, **When** the user copies it to `.groupalarm.toml` and adjusts values, **Then** the TUI starts correctly with those settings.

---

### Edge Cases

- What happens when the Users API is unreachable and participant names cannot be resolved? The feedback lists display user IDs as fallback with a warning notification.
- What happens when an appointment has no participants at all? The feedback and direct-participant sections are hidden entirely.
- What happens when the user presses E while the detail panel is already in edit mode? Nothing — the action is ignored.
- What happens when the user navigates the list while the detail panel is in edit mode with unsaved changes? An unsaved-changes warning dialog appears.
- What happens when a type-ahead suggestion field has zero matches? No suggestion is shown and Tab moves focus to the next field.
- How does the system handle an appointment with more than 50 participants in the feedback lists? All participants are listed; the feedback section is scrollable.
- What happens when keepLabelParticipantsInSync is Nein and label members change? Participants are not automatically updated — only manual label participant snapshots are used.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The detail panel MUST update its content whenever the highlighted row in the appointment list changes (Up/Down arrow navigation).
- **FR-002**: Pressing Enter or Right arrow in the appointment list MUST move focus to the detail panel.
- **FR-003**: Pressing Left arrow in the detail panel **in read-only mode** MUST return focus to the appointment list at the same cursor position.
- **FR-003a**: In edit mode, Left and Right arrow keys MUST navigate the text cursor within the active input field and MUST NOT trigger panel switching or any navigation action.
- **FR-003b**: To return to the list from edit mode, the user MUST first press Escape (returning to read-only mode) and then press Left arrow.
- **FR-004**: Pressing E in the appointment list MUST enter edit mode in the detail panel and move focus to the first editable field.
- **FR-005**: Pressing E in the detail panel (read-only) MUST enter edit mode and move focus to the first editable field.
- **FR-006**: A navigation attempt away from the detail panel (Left arrow in read-only mode) with unsaved changes MUST trigger an unsaved-changes warning dialog (Save / Discard / Cancel).
- **FR-007**: In read-only mode, all field labels (Name, Beschreibung, Start, Ende, Labels, Öffentlich, Erinnerung, Benachrichtigung, etc.) MUST be rendered in the same yellow color as the vertical separator between list and detail panel.
- **FR-008**: In edit mode, field labels MUST retain the yellow highlight color.
- **FR-009**: In edit mode, Up/Down arrow keys MUST move focus between single-line input fields (EditInput) in addition to Tab.
- **FR-009a**: In the multi-line Beschreibung field (TextArea), Up/Down arrow keys MUST navigate lines within the text. Down MUST move focus to the next field only when the cursor is on the last line. Up MUST move focus to the previous field only when the cursor is on the first line.
- **FR-010**: Up arrow on the first field MUST NOT wrap to the last field; Down arrow on the last field MUST NOT wrap to the first field.
- **FR-011**: The detail panel MUST display a "Direkte Teilnehmer" section listing participants whose labelID is 0 or null.
- **FR-012**: The "Direkte Teilnehmer" section MUST be hidden when no directly added participants exist.
- **FR-013**: The detail panel MUST display participant feedback in three lists: "Zugesagt" (positive), "Abgesagt" (negative), and "Keine Rückmeldung" (no feedback).
- **FR-014**: Each participant's feedbackMessage, if present, MUST be displayed below the participant's name in a secondary style.
- **FR-015**: Participant names in feedback and direct-participant lists MUST be resolved to human-readable names (first name + surname) via the Users API.
- **FR-016**: If the Users API is unreachable, participant entries MUST fall back to displaying user IDs with a visible warning.
- **FR-017**: Appointment creation MUST expose a keepLabelParticipantsInSync field defaulting to Ja (true).
- **FR-018**: Appointment creation MUST set isPublic to Nein (false) by default.
- **FR-019**: Appointment creation MUST provide a "Teilnehmer" field with type-ahead suggestions from all users in the organization.
- **FR-020**: The organization user list for suggestions MUST be fetched from the Users API (GET /users with organization parameter).
- **FR-021**: All type-ahead suggestion fields MUST accept the current suggestion when Tab is pressed.
- **FR-022**: After accepting a suggestion via Tab, the cursor MUST be positioned at the end of the accepted text.
- **FR-023**: The README MUST be rewritten to focus on TUI-based workflows, removing all references to the old import framework (Mapper, Runner, Importer, CSV/Excel patterns, Token/UUID persistence).
- **FR-024**: An example configuration file (`.groupalarm.example.toml`) MUST be provided in the repository root with all available configuration keys documented.
- **FR-025**: The comma-separated participants field MUST apply type-ahead suggestions only to the current token being typed (after the last comma).

### Key Entities

- **Appointment**: Core scheduling entity with name, description, start/end dates, organization, labels, participants, isPublic, keepLabelParticipantsInSync, reminder, recurrence.
- **AppointmentParticipant**: A user invited to an appointment — attributes: userID, labelID (0/null if directly added), feedback status (integer: positive/negative/none), feedbackMessage (optional text).
- **User (Organization Member)**: A person in the organization — attributes: id, name, surname, email. Used for resolving participant names and for type-ahead in participant addition.
- **AppConfig**: Application configuration — attributes: organization_id, timezone, date_range_days, default_label_ids, default_appointment_duration_hours.

## Assumptions

- The GroupAlarm appointment API returns participants with their feedback status and feedbackMessage when fetching a single appointment (GET /appointment/{id}).
- Feedback status values follow: 0 = no feedback, 1 = positive (accepted), 2 = negative (declined). The exact integer mapping will be verified during implementation.
- The Users API (GET /users?organization=ID) returns all organization members and is accessible with the same Personal-Access-Token.
- The yellow color used for the separator line between list and detail panel is defined in the existing TCSS stylesheet and can be reused for field labels.
- The existing EditInput widget's Tab-accept behavior for suggestions will be extended to all new suggestion fields (user participants).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can navigate from the list to the detail panel and back using only keyboard shortcuts in under 1 second per transition.
- **SC-002**: The detail panel content updates within 200 milliseconds of each Up/Down keystroke in the list.
- **SC-003**: 100% of field labels in both read-only and edit modes use the defined highlight color.
- **SC-004**: Users can navigate all edit-mode fields using only Up/Down arrows without needing Tab.
- **SC-005**: Participant feedback is categorized correctly for appointments with mixed feedback statuses — zero misclassified entries.
- **SC-006**: Type-ahead suggestions appear within 300 milliseconds of the user typing in any suggestion-enabled field.
- **SC-007**: Tab-accept on suggestions works consistently across all suggestion fields (labels, users) with the cursor landing at the end of the accepted text.
- **SC-008**: New appointments are created with keepLabelParticipantsInSync = true and isPublic = false by default without any user action.
- **SC-009**: The README contains zero references to Mapper, Runner, Importer, CSV, Excel, or Token/UUID patterns after modernization.
- **SC-010**: The example configuration file is valid TOML and covers all configurable application settings.
