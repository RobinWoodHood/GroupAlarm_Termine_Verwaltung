# TUI Save Metrics

**Success criteria**: SC-003 — ≥95% first-attempt save success rate across at least 20 QA runs.

## Confirmation Flow Evidence

The save flow enforces a blocking confirmation dialog before any API call:

1. User presses `s` to save → `MainScreen._do_save()` collects changes
2. For recurring appointments, `RecurrenceStrategyDialog` is shown first
3. `ConfirmationDialog` displays a grouped field-by-field diff with label warnings
4. API call is executed only after explicit confirmation
5. On success, the list and detail panel refresh automatically

Regression test: `test_save_waits_for_confirmation_before_update` in `tests/test_confirmation.py`.

## QA Run Log

_Record first-attempt save success for at least 20 edits._

| Run | Edit Description | First-Attempt Success | Notes |
|---|---|---|---|
| 1 | _pending_ | | |
| 2 | _pending_ | | |
| 3 | _pending_ | | |
| 4 | _pending_ | | |
| 5 | _pending_ | | |
| 6 | _pending_ | | |
| 7 | _pending_ | | |
| 8 | _pending_ | | |
| 9 | _pending_ | | |
| 10 | _pending_ | | |
| 11 | _pending_ | | |
| 12 | _pending_ | | |
| 13 | _pending_ | | |
| 14 | _pending_ | | |
| 15 | _pending_ | | |
| 16 | _pending_ | | |
| 17 | _pending_ | | |
| 18 | _pending_ | | |
| 19 | _pending_ | | |
| 20 | _pending_ | | |

**First-attempt success rate**: _TBD_ / 20 = _TBD_% (target ≥95%)  
**Goal met**: _TBD_
