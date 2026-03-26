# Full-Breadth Requirements Quality Checklist

**Purpose**: Author self-review before task generation â€” validate completeness, clarity, and consistency across all domains  
**Created**: 2026-03-22  
**Depth**: Standard  
**Audience**: Author (pre-tasks gate)  
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md)

## Requirement Completeness

- [X] CHK001 - Are loading/progress indicator requirements defined for the initial appointment fetch on startup? [Completeness, Gap] Only for bigger things. 
- [X] CHK002 - Are requirements specified for what the detail panel displays when no appointment is selected? [Completeness, Gap] Maybe informations and a how to. But then it should be possible to show this help again. Only if this is no extra effort. 
- [X] CHK003 - Are participant field display and editing constraints explicitly documented (read-only vs editable, display format)? [Completeness, Spec Â§FR-007] We mostly use Labels only. But if we would add participants, we need the name instead of the ID.
- [X] CHK004 - Are requirements defined for how labelIDs are presented during editing (ID list vs selectable label picker with names/colors)? [Completeness, Spec Â§FR-007] I dont want to see the LabelID. I want to see the name and maybe the color. And I want to be able to select from the available labels with typeahead search.
- [X] CHK005 - Are requirements specified for the file path prompt during export (default filename pattern, directory, overwrite behavior)? [Completeness, Spec Â§FR-011] The default filename should be appointments_YYYY-MM-DD.xlsx in the current directory. If the file already exists, we should prompt the user to confirm overwriting it. We could also offer an option to automatically generate a unique filename by appending a timestamp or a counter.
- [X] CHK006 - Are requirements defined for refreshing the appointment list after a successful create, update, or delete? [Completeness, Gap] Yes directly after the mutation, we should refresh the list to reflect the changes. This could be done by re-fetching the appointments from the API or by locally updating the list based on the mutation response.
- [X] CHK007 - Are the sensible defaults for new appointment creation explicitly specified (start=now+1h, end=now+2h, etc.)? [Completeness, Spec Â§US4-AS1] A typical default lenght of an appointment is 4 h and should be defined in the toml.
- [X] CHK008 - Are requirements defined for how the `--dry-run` flag is visually communicated in the TUI (banner, indicator)? [Completeness, Spec Â§FR-018] The dry run should be captured by displaying the planned changes in a different color (e.g., yellow) and showing a banner at the top of the screen that says "Dry Run Mode: No changes will be sent to the server". We could also add a tooltip or a help message that explains what dry run mode does and how to exit it.
- [X] CHK009 - Are sort order requirements defined for the appointment list (by date, name, or configurable)? [Completeness, Gap] No, but we might need a search function. The sort order should be by start date ascending by default, but we could also allow the user to sort by name or other fields. This could be implemented as a toggle or a dropdown in the UI.
- [X] CHK010 - Are requirements specified for the first-launch org ID prompt UX (input widget, validation, cancel behavior)? [Completeness, Spec Â§FR-021]

## Requirement Clarity

- [X] CHK011 - Is "scrollable, filterable list" quantified â€” are maximum visible rows, column widths, or truncation rules defined? [Clarity, Spec Â§FR-002] This should depend on the terminal size. We should define a minimum terminal size for the TUI to work properly, and if the terminal is smaller than that, we should display a warning and suggest resizing it. For the list, we could show a maximum of 10 rows at a time, with pagination or scrolling to access more. Column widths could be fixed or adjustable by the user, and we could truncate long text with ellipses and show the full text in a tooltip or detail panel when selected.
- [X] CHK012 - Is "visually highlighted" for unsaved changes defined with specific styling (color, border, icon)? [Clarity, Spec Â§US2-AS2] We could use a different background color (e.g., light red) for fields that have unsaved changes, and we could also add an icon (e.g., a pencil or an asterisk) next to the field label to indicate that it has been modified. Additionally, we could show a summary of unsaved changes in the footer or a sidebar, and provide a way to quickly jump to the modified fields.
- [X] CHK013 - Is the "human-readable summary" format for confirmation dialogs specified (plain text diff, table, side-by-side)? [Clarity, Spec Â§FR-008] For updates, we could show a side-by-side comparison of the original and modified values in a table format, with changed fields highlighted. For creates, we could show a summary of the new appointment details in a clear, structured format. For deletes, we could show a warning message with the appointment name and a confirmation prompt. In all cases, we should use clear language and formatting to make it easy for the user to understand what they are confirming.
- [X] CHK014 - Is "sensible default" for the export file path quantified with a specific pattern (e.g., `appointments_YYYY-MM-DD.xlsx`)? [Clarity, Spec Â§US3-AS1]
- [X] CHK015 - Is "descriptive error and setup instructions" for missing API key defined with specific content? [Clarity, Spec Â§FR-001]
- [X] CHK016 - Are the label filter interaction mechanics specified â€” multi-select checkboxes, toggle list, or dropdown? [Clarity, Spec Â§FR-003] What ist best for TUI? Maybe a toggle list with the label names and colors, where the user can navigate with the arrow keys and select/deselect with spacebar. We could also allow typeahead search to quickly find labels in case there are many.
- [X] CHK017 - Is "gracefully degrades" for small terminal sizes defined with specific breakpoints or minimum dimensions? [Clarity, Spec Edge Cases]

## Requirement Consistency

- [X] CHK018 - Are timezone handling requirements consistent between display (FR-019: configured TZ), export (data-model: configured TZ), and API payloads (UTC)? [Consistency, Spec Â§FR-019] I dont know. Does the api need UTC? If so, we should convert the appointment times to UTC before sending them to the API, and convert them back to the configured timezone for display and export. We should also clearly document this behavior in the UI and the documentation, so that users understand how timezones are handled and can avoid confusion when working with appointments across different timezones.
- [X] CHK019 - Does the Appointment.timezone field default ("UTC" in data-model) conflict with the display timezone default ("Europe/Berlin" in config)? [Consistency, Spec Â§FR-019 vs data-model] We should clarify whether the default timezone for new appointments should be UTC or the configured display timezone, and ensure that this is consistently applied across the UI, export, and API interactions.
- [X] CHK020 - Are confirmation dialog requirements consistent across all three mutation types (create shows payload, update shows diff, delete shows warning)? [Consistency, Spec Â§FR-008, Â§FR-009] 
- [X] CHK021 - Is the label data source consistent â€” FR-023 says "fetch from API" while FR-022 mentions "default filter labels (list of label IDs)" in config; are config IDs validated against API labels? [Consistency, Spec Â§FR-022 vs Â§FR-023] I dont know. We should ensure that the label IDs specified in the config for default filters are validated against the labels fetched from the API at startup, and if there are any discrepancies (e.g., missing or invalid label IDs), we should handle this gracefully by either ignoring the invalid IDs with a warning or prompting the user to update their config. Additionally, we should ensure that the label data is consistently sourced from the API for both filtering and display purposes, and that any changes to labels in the API are reflected in the TUI without requiring a restart.
- [X] CHK022 - Are key binding definitions consistent between the contracts (cli-application.md) and the spec's FR-017 description? [Consistency]

## Acceptance Criteria Quality

- [X] CHK023 - Can SC-001 ("find appointment within 30 seconds") be objectively measured in automated tests? [Measurability, Spec Â§SC-001]
- [X] CHK024 - Can SC-007 ("discover all actions without documentation") be objectively verified? [Measurability, Spec Â§SC-007]
- [X] CHK025 - Is SC-006 ("list within 5 seconds") measured from process start or after API response, and does it account for first-launch config prompts? [Measurability, Spec Â§SC-006]

## Scenario Coverage

- [X] CHK026 - Are requirements defined for what happens when the user navigates away from an unsaved edit (accidental data loss prevention)? [Coverage, Gap] I guess the user should be prompted to confirm discarding unsaved changes if they try to navigate away from the detail panel or quit the application while in edit mode. This could be implemented as a confirmation dialog that lists the unsaved changes and asks the user to either save, discard, or cancel the navigation action. This would help prevent accidental data loss and ensure that users are aware of their unsaved changes before leaving the edit context.
- [X] CHK027 - Are requirements specified for handling API rate limiting or 429 responses? [Coverage, Gap] I guess there is no API Limit. 
- [X] CHK028 - Are requirements defined for how the label filter behaves when the label API call fails? [Coverage, Exception Flow]
- [X] CHK029 - Are requirements specified for concurrent usage â€” what if the user triggers a new API call while a previous one is still in-flight? [Coverage, Gap] We should define a behavior for handling concurrent API calls, such as disabling the UI interactions that trigger API calls while a call is in-flight, and showing a loading indicator to inform the user that an operation is in progress. If the user attempts to trigger another API call while one is still in progress, we could either queue the new request to execute after the current one finishes or show a warning message that they need to wait until the current operation completes. This would help prevent
- [X] CHK030 - Are requirements defined for the behavior when the config file becomes corrupted or contains invalid TOML? [Coverage, Exception Flow] Clear error message. 

## Edge Case Coverage

- [X] CHK031 - Are requirements defined for appointments with empty or null optional fields (no description, no reminder, no labels)? [Edge Case, Gap] Should this not be done by the API?
- [X] CHK032 - Are requirements specified for extremely long appointment names or descriptions in the list view (truncation, wrapping)? [Edge Case, Gap] Is this not defined in the api-docs?
- [X] CHK033 - Are requirements defined for what happens when the exported Excel file path already exists (overwrite, prompt, error)? [Edge Case, Spec Â§FR-011]
- [X] CHK034 - Are requirements specified for appointments whose start/end dates span across timezone DST transitions? [Edge Case, Spec Â§FR-019]
- [X] CHK035 - Are requirements defined for the behavior when `default_label_ids` in config reference labels that no longer exist in the API? [Edge Case, Spec Â§FR-022]

## Non-Functional Requirements

- [X] CHK036 - Are accessibility requirements defined for screen reader compatibility or high-contrast mode? [Coverage, Gap] No
- [X] CHK037 - Are logging requirements specified â€” what events are logged, at what level, and where (file vs stderr)? [Completeness, Gap] Yes, logging is important. Please add, that all important events (API calls, errors, user actions) should be logged to a file with appropriate log levels (INFO for successful operations, ERROR for failures). The logs should not contain sensitive information such as the API key. Additionally, we could consider adding an option for users to enable verbose logging for debugging purposes, which would include more detailed information about the application's internal state and API interactions.
- [X] CHK038 - Are requirements defined for graceful shutdown behavior (Ctrl+C during an API call, unsaved changes on quit)? [Coverage, Gap] This must be clearly defined. If the user presses Ctrl+C during an API call, we should attempt to gracefully cancel the ongoing operation and return to a stable state in the TUI. If there are unsaved changes when the user tries to quit the application, we should prompt them with a confirmation dialog that lists the unsaved changes and asks if they want to save, discard, or cancel quitting. This would help ensure that users do not lose their work accidentally and can exit the application safely even in the middle of operations.
- [X] CHK039 - Are memory/resource requirements defined for large appointment sets (500+ items in list)? [Coverage, Spec Â§Technical Context]

## Security & Credential Handling

- [X] CHK040 - Are requirements specified for API key masking in error stack traces from `requests` exceptions? [Coverage, Spec Â§FR-016] I dont know. We should ensure that if an API call fails and raises an exception, any error messages or stack traces that are logged or displayed to the user do not include the API key. This could be achieved by sanitizing the exception messages before logging or displaying them, and by configuring the logging system to exclude sensitive information. Additionally, we should review any third-party libraries (like `requests`) to ensure that they do not inadvertently log the API key in their error handling, and if necessary, implement custom error handling to prevent this.
- [X] CHK041 - Is the scope of "no API key in logs" defined â€” does it include Textual's debug log, Python's logging module, and crash dumps? [Clarity, Spec Â§FR-016] We should clarify that the requirement to not include the API key in logs applies to all forms of logging and error reporting within the application, including Textual's debug logs, any logs generated by Python's logging module, and any crash dumps or stack traces that may be produced in the event of an unhandled exception. This means that we need to implement a comprehensive approach to ensure that the API key is never included in any log output or error report, regardless of the source or context. This could involve sanitizing log messages, configuring logging handlers to exclude sensitive information, and implementing custom error handling to catch and sanitize exceptions before they are logged or displayed.
- [X] CHK042 - Are requirements defined for securing the `.groupalarm.toml` config file (file permissions, sensitive data exclusion)? [Coverage, Gap] We should specify that the `.groupalarm.toml` config file should be created with restrictive file permissions (e.g., 600 on Unix systems) to prevent unauthorized access. Additionally, we should ensure that this config file does not contain any sensitive data such as the API key, and only includes non-sensitive configuration options like the organization ID and display preferences. We could also provide guidance in the documentation on how users can secure their config file and avoid storing sensitive information in it.

## API Contract Coverage

- [X] CHK043 - Are error response handling requirements defined for all documented API error codes (400, 404, 500) across all endpoints? [Completeness, Gap]
- [X] CHK044 - Is the `time` query parameter requirement for `delete_appointment` with strategy "single"/"upcoming" documented in the spec (not just the contract)? [Completeness, Spec Â§FR-024]
- [X] CHK045 - Are requirements defined for how the TUI handles an appointment whose `recurrence` field is null vs absent in the API response? [Edge Case, Spec Â§FR-025]
- [X] CHK046 - Is the label API base URL assumption documented â€” does `list_labels` use the same base URL as appointments, or a different alarming API host? [Clarity, Gap] This should be defined in the docs. 

## Recurring Appointment Scope Boundary

- [X] CHK047 - Are requirements specified for what the detail panel shows when a recurring appointment's editable fields are modified â€” does the strategy selector appear before or after editing? [Coverage, Spec Â§FR-025]
- [X] CHK048 - Is it specified whether the appointment list refreshes or locally removes items after a "single occurrence" delete? [Coverage, Spec Â§FR-024] Refresh.
- [X] CHK049 - Are requirements defined for how the recurrence pattern is rendered in human-readable form (e.g., "Every 2 weeks on Mon, Wed")? [Clarity, Spec Â§FR-025]
- [X] CHK050 - Is the V1 scope boundary for recurring appointments communicated to the user in the TUI (hint text, disabled fields)? [Completeness, Spec Â§FR-025, Edge Cases]

## Dependencies & Assumptions

- [X] CHK051 - Is the assumption that "labels do not change during a session" validated â€” are requirements defined for a manual label refresh action? [Assumption, Spec Â§Assumptions] Yes. Label changes very rarely. We dont have to worry about this.
- [X] CHK052 - Is the dependency on the alarming API (`/labels` endpoint) for label fetching explicitly documented alongside the appointment API dependency? [Dependency, Gap] yes. In the api-docs.
- [X] CHK053 - Are requirements defined for minimum Python version enforcement at startup (error message if < 3.11)? [Dependency, Gap]
