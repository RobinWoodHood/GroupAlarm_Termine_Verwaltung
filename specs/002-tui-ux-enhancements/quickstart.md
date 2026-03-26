# Quickstart: Keyboard Navigation & Edit Confirmation

**Feature**: 002-tui-ux-enhancements  
**Updated**: 2026-03-23

## Prerequisites

- Python 3.11 environment with `textual` dependencies installed via `pip install -r requirements.txt`.
- `GROUPALARM_API_KEY` exported (dummy token is fine when running in offline/test mode).
- Sample data loaded via `python example_usage.py --seed` **or** the fixtures in `tests/data/tui_sample.json`.
- Run `python groupalarm_cli.py --dry-run` so no remote mutations occur during the walkthrough.

## Scenario A: Keyboard Navigation Between Panes (US1)

1. Launch the CLI (`python groupalarm_cli.py --dry-run`). The split view shows the appointment list on the left, detail panel on the right, and the filter bar at the bottom.
2. Press `→` to move focus from the list into the detail panel; press `←` to return. The highlighted arrow affordance should follow focus without changing the selected row.
3. Press `Ctrl + /` to focus the start-date filter. Observe that the label section instantly expands from the five-toggle preview into the full directory.
4. While the filter bar is focused, press `Tab` (or `↓`) repeatedly to cycle through start date → end date (`Ctrl + Shift + /`) → search (`Ctrl + F`) → label toggles. Zero-match labels show a muted `0` badge plus the "Keine Treffer" helper chip but remain focusable.
5. Press `Esc` to leave the filter bar; it collapses back to the five-toggle preview with the `+N weitere` helper until focus re-enters.

**Pass Criteria**
- No mouse interaction is required at any point.
- The currently selected appointment remains highlighted when switching panes.
- Shortcut-triggered focus always expands the full label directory.

## Scenario B: Editing With Diff Confirmation (US2)

1. From the detail panel, press `E` (or the mapped key) to enter edit mode for the highlighted appointment.
2. Update the schedule:
   - Move to **Start** date/time using `↓` and enter `02.04.2026 09:00`.
   - Set **End** to `02.04.2026 11:00`.
   - Change the **Reminder** to `45` minutes (ensure it stays within the 0–10 080 minute guardrail).
3. Add labels: type `Lageerkundung` and `Übung` separated by Enter. If you enter an unknown label (e.g., `Foo`), a warning banner appears until it is removed or confirmed.
4. Press `Ctrl + S` (or click **Speichern**). A diff preview modal lists every field change grouped by section. Confirm the update to persist the record and automatically refresh the list + detail panels.
5. Re-open the appointment to ensure the German-formatted timestamps (`dd.mm.yyyy HH:MM`) reflect the new values.

**Pass Criteria**
- Inline validation warns if start > end or reminder limits are exceeded.
- Unknown labels surface a non-blocking warning before confirmation.
- The confirmation dialog blocks the save until explicitly accepted and shows each changed field.

## Scenario C: Manual Acceptance Checklist (Polish Phase)

1. Run through Scenario A and record the five focus transitions in `docs/tui-focus-metrics.md` (target <1 s per transition, SC-001/SC-005 evidence).
2. Repeat Scenario B for at least 20 edits, logging first-attempt save rate in `docs/tui-save-metrics.md` (target ≥95%, SC-003).
3. Capture operator feedback on readability (SC-004) using the survey template in `docs/tui-survey.md` once the UI polish is complete.

## Troubleshooting Tips

- If shortcuts stop working, rerun `pytest tests/test_app.py -k shortcuts` to ensure T008/T010 are still wired correctly.
- When filter labels no longer expand, check the `FilterControls` state in `cli/widgets/filter_bar.py` and rerun `pytest tests/test_filter_bar.py -k preview` (T009).
- Reminder validation errors typically originate from `framework/appointment.py`; ensure T006/T040 helpers are imported wherever reminders are edited.
