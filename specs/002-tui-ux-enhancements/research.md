# Research: TUI UX Enhancements

**Date**: 2026-03-23 | **Status**: Complete

## R-201: Reminder Lead-Time Limits

**Decision**: Enforce reminder durations between 0 and 10 080 minutes (exactly seven days) as defined in the appointment OpenAPI schema, and surface inline validation/warnings when the user exceeds that range.

**Rationale**: The `reminder` field in the appointment definition specifies `minimum: 0` and `maximum: 10080`, so any client-side UI should prevent values outside that window before hitting the API. Surfacing the limit in the UI avoids trial-and-error saves and matches the user's request to "be patient about this limit" by explaining the precise constraint.

**Alternatives Considered**:
- *Keep speculative 4-week limit from spec assumptions* — rejected once the actual API contract confirmed 10 080 minutes ([api-docs/appointment.openapi.json#L742-L781](api-docs/appointment.openapi.json#L742-L781)).
- *Rely on server-side validation only* — rejected because it would force a save-attempt round trip for every mistake.

---

## R-202: Keyboard Focus Routing for Filters

**Decision**: Add explicit focus helpers on `FilterBar` that target the existing `Input` widgets (`#start-date`, `#end-date`, `#search-input`) and wire new bindings in `GroupAlarmApp`/`MainScreen` (`ctrl+/` for start-date, `ctrl+shift+/` for end-date, `ctrl+f` for search). Navigation between filter controls will reuse Textual's `focus_next()` and `focus_previous()` patterns plus `Input.focus()` for deterministic placement.

**Rationale**: `FilterBar` already exposes IDs for each relevant `Input` and demonstrates the pattern in `focus_search()` (see [cli/widgets/filter_bar.py#L118-L168](cli/widgets/filter_bar.py#L118-L168)). Extending the same approach keeps the codebase consistent and lets arrow keys/tabbing move between widgets without inventing a new navigation layer. Textual's widgets are inherently focusable, so the work reduces to adding handlers that call `.focus()`.

**Alternatives Considered**:
- *Custom focus manager widget* — unnecessary; Textual already manages focus order when widgets are arranged inside a container.
- *Global key listener that inspects `self.focused`* — heavier than needed and harder to test than targeted helper methods.

---

## R-203: Label Autocomplete Source of Truth

**Decision**: Use `LabelService.labels` (loaded once per session) as the suggestion dataset for both the filter bar and the edit-form label entry. The autocomplete will accept free text but validate each token against `LabelService.get_by_id()/get_name()` to warn when an unknown label is entered.

**Rationale**: `LabelService.load()` caches all labels for the organization and exposes both list and lookup helpers (see [cli/services/label_service.py#L8-L46](cli/services/label_service.py#L8-L46)). This ensures suggestions include labels even if they are not part of the current appointment list — addressing the user's complaint that they "are gone now." Leveraging the cached dictionary also makes warnings instantaneous without extra API calls.

**Alternatives Considered**:
- *Derive labels from the currently loaded appointments* — current behavior; fails when labels exist but no matching appointments are in view.
- *Fetch labels on every keystroke* — unnecessary latency and API load; the dataset is static during a session.

---

## R-204: German Date/Time Formatting in Detail Views

**Decision**: Standardize all displayed timestamps (list columns and detail panel) on the `dd.mm.yyyy HH:MM` format while keeping internal storage in timezone-aware `datetime` objects. Rendering uses `strftime("%d.%m.%Y %H:%M")`, and edit-mode inputs split date/time fields so users can type each component separately.

**Rationale**: The current detail panel formatter (`_fmt_dt`) emits `"%Y-%m-%d %H:%M"` ([cli/widgets/detail_panel.py#L62-L90](cli/widgets/detail_panel.py#L62-L90)), which contradicts the user's request and German locale expectations. Adjusting the format string plus inserting spacing blocks after each section satisfies the readability requirement without touching backend payloads. The appointment list shares the same util via `_fmt_dt` in [cli/widgets/appointment_list.py#L23-L52](cli/widgets/appointment_list.py#L23-L52), so reusing the helper maintains consistency.

**Alternatives Considered**:
- *Locale-aware formatting via `locale` module* — brittle in Windows terminals and would introduce implicit state; explicit format strings are predictable.
- *Leaving list timestamps as-is* — rejected because the requirement calls out "All dates" including list rows.

---

## R-205: Filter Label Availability vs. Appointment Subset

**Decision**: Keep the filter bar populated with the full label directory from `LabelService` and visually distinguish labels that currently have zero matching appointments instead of removing them. `MainScreen._update_filter_labels` will merge the cached label list with the active results instead of intersecting.

**Rationale**: The present implementation rebuilds the label buttons from whatever labels appear in the current appointment window ([cli/screens/main_screen.py#L145-L176](cli/screens/main_screen.py#L145-L176)), causing time filter/search controls to disappear when no appointments are loaded. By decoupling the filter bar from the active result set and showing disabled/zero-count states, operators always see consistent controls and can expand filters back out.

**Alternatives Considered**:
- *Keep hiding unused labels* — violates the user's expectation that filters should stay visible regardless of the current list contents.
- *Add a second API call every time filters change* — redundant because we already cache the entire label directory at app startup.
