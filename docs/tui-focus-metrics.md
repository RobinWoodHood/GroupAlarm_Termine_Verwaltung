# TUI Focus Transition Metrics

**Success criteria**: SC-001 — Each focus transition completes in <1 s.  
**Measured via**: `test_focus_transition_timing_under_one_second` in `tests/test_app.py`.

## Automated Benchmark Results

| Transition | Target | Status |
|---|---|---|
| list → detail | <1 s | PASS |
| detail → list | <1 s | PASS |
| list → filter (Ctrl+/) | <1 s | PASS |
| filter → search (Ctrl+F) | <1 s | PASS |
| search → list (Esc) | <1 s | PASS |

## SC-005: Consecutive Keyboard-Only Quickstart Runs

_Record five consecutive runs of Scenario A from `specs/002-tui-ux-enhancements/quickstart.md`._

| Run | Focus Issues | Notes |
|---|---|---|
| 1 | _pending_ | |
| 2 | _pending_ | |
| 3 | _pending_ | |
| 4 | _pending_ | |
| 5 | _pending_ | |

**Overall**: _To be completed during manual acceptance testing._
