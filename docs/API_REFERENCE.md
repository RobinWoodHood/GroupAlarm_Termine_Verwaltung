# Project API Reference

_Generated automatically on 2026-03-23 14:30 UTC._

Each section lists the classes and functions discovered per module. Methods are included under their respective classes.

## cli/app.py

### Classes

#### GroupAlarmApp

Interactive TUI for GroupAlarm appointment management.

##### Methods

- `__init__(self, client, config, org_id=None, dry_run=False, **kwargs)` — No docstring provided.
- `on_mount(self)` — No docstring provided.
- `action_focus_filter(self)` — No docstring provided.
- `action_search(self)` — No docstring provided.
- `action_new_appointment(self)` — No docstring provided.
- `action_delete_appointment(self)` — No docstring provided.
- `action_export(self)` — No docstring provided.
- `action_help(self)` — No docstring provided.
- `action_refresh(self)` — No docstring provided.
- `action_quit(self)` — Quit with unsaved changes guard.

## cli/screens/help_screen.py

### Classes

#### HelpScreen

Modal overlay showing all available key bindings.

##### Methods

- `compose(self)` — No docstring provided.
- `on_button_pressed(self, event)` — No docstring provided.
- `action_close(self)` — No docstring provided.

## cli/screens/main_screen.py

### Classes

#### MainScreen

Primary screen with list + detail split layout.

##### Methods

- `__init__(self, appointment_service, label_service, config=None, dry_run=False, **kwargs)` — No docstring provided.
- `compose(self)` — No docstring provided.
- `on_mount(self)` — No docstring provided.
- `_load_appointments(self)` — No docstring provided.
- `_lock_ui(self)` — Show loading indicator and block mutation actions.
- `_unlock_ui(self)` — Hide loading indicator and re-enable mutation actions.
- `on_filter_changed(self, event)` — No docstring provided.
- `on_appointment_selected(self, event)` — No docstring provided.
- `_select_appointment(self, appt_id)` — No docstring provided.
- `_handle_unsaved_on_selection(self, result)` — No docstring provided.
- `_parse_filter_date(self, value, field_name)` — No docstring provided.
- `_normalize_date_text(self, text)` — No docstring provided.
- `_reload_appointments(self, start_date, end_date)` — No docstring provided.
- `_update_filter_labels(self)` — No docstring provided.
- `_date_to_datetime(self, value, clamp_end=False)` — No docstring provided.
- `action_edit_mode(self)` — No docstring provided.
- `action_save(self)` — No docstring provided.
- `_do_save(self, then_select=None)` — No docstring provided.
- `_on_strategy_selected_for_update(self, strategy, old_values, new_values, then_select)` — No docstring provided.
- `_on_update_confirmed(self, confirmed, strategy, then_select)` — No docstring provided.
- `_on_create_confirmed(self, confirmed, then_select)` — No docstring provided.
- `action_cancel_edit(self)` — No docstring provided.
- `_handle_unsaved_on_cancel(self, result)` — No docstring provided.
- `action_new_appointment(self)` — No docstring provided.
- `_handle_unsaved_then_new(self, result)` — No docstring provided.
- `_start_create(self)` — No docstring provided.
- `action_delete_appointment(self)` — No docstring provided.
- `_on_delete_strategy(self, strategy, appt)` — No docstring provided.
- `_show_delete_confirmation(self, appt, strategy)` — No docstring provided.
- `_on_delete_confirmed(self, confirmed, appt, strategy)` — No docstring provided.
- `action_export(self)` — No docstring provided.
- `action_focus_filter(self)` — No docstring provided.
- `action_search(self)` — No docstring provided.
- `action_toggle_sort(self)` — No docstring provided.
- `action_refresh(self)` — No docstring provided.
- `refresh_list(self)` — No docstring provided.
- `_check_dirty_before_quit(self)` — Check for unsaved changes before quitting.
- `_handle_unsaved_on_quit(self, result)` — No docstring provided.

## cli/services/appointment_service.py

### Classes

#### AppointmentService

Manage the in-memory appointment list with filter/sort/search.

##### Methods

- `__init__(self, client, organization_id, date_range_days=30)` — No docstring provided.
- `load(self, start=None, end=None)` — No docstring provided.
- `_dict_to_appointment(self, d)` — No docstring provided.
- `set_label_filter(self, label_ids)` — No docstring provided.
- `set_search(self, text, include_description=None)` — No docstring provided.
- `set_date_filter(self, start, end)` — No docstring provided.
- `toggle_sort(self)` — No docstring provided.
- `_apply_filters(self)` — No docstring provided.
- `_within_date_range(self, appointment)` — No docstring provided.
- `appointments(self)` — No docstring provided.
- `all_appointments(self)` — No docstring provided.
- `get_by_id(self, appt_id)` — No docstring provided.
- `update(self, appt, strategy='all')` — Update an appointment via the client and refresh local cache.
- `create(self, appt)` — Create a new appointment via the client.
- `delete(self, appt_id, strategy='all', time_=None)` — Delete an appointment via the client.

## cli/services/label_service.py

### Classes

#### LabelService

Fetch labels from the API once and provide lookup by ID.

##### Methods

- `__init__(self, client, organization_id)` — No docstring provided.
- `load(self)` — No docstring provided.
- `labels(self)` — No docstring provided.
- `get_by_id(self, label_id)` — No docstring provided.
- `get_name(self, label_id)` — No docstring provided.
- `get_color(self, label_id)` — No docstring provided.
- `get_names_for_ids(self, label_ids)` — No docstring provided.

## cli/widgets/appointment_list.py

### Classes

#### AppointmentSelected

Posted when an appointment is selected.

##### Methods

- `__init__(self, appointment_id)` — No docstring provided.

#### AppointmentList

Scrollable appointment list as a DataTable.

##### Methods

- `__init__(self, label_service=None, display_tz='Europe/Berlin', **kwargs)` — No docstring provided.
- `compose(self)` — No docstring provided.
- `_fmt_dt(self, dt)` — No docstring provided.
- `update_appointments(self, appointments)` — No docstring provided.
- `on_data_table_row_selected(self, event)` — No docstring provided.
- `get_appointment_at_cursor(self)` — No docstring provided.

## cli/widgets/confirmation_dialog.py

### Classes

#### ConfirmationDialog

Modal confirmation dialog showing a diff summary before mutations.



For updates: side-by-side old→new diff.

For creates: structured payload summary.

For deletes: name + irreversibility warning.

##### Methods

- `__init__(self, title, body, warning='', confirm_label='Confirm', cancel_label='Cancel', **kwargs)` — No docstring provided.
- `compose(self)` — No docstring provided.
- `on_button_pressed(self, event)` — No docstring provided.
- `build_update_diff(old_values, new_values)` — Build a field-by-field diff string for update confirmation.
- `build_create_summary(values)` — Build a structured payload summary for create confirmation.
- `build_delete_summary(name, start, end)` — Build a delete confirmation body.

#### UnsavedChangesDialog

Modal dialog for unsaved changes — Save, Discard, or Cancel.

##### Methods

- `compose(self)` — No docstring provided.
- `on_button_pressed(self, event)` — No docstring provided.

#### RecurrenceStrategyDialog

Modal dialog for choosing recurrence strategy (single/upcoming/all).

##### Methods

- `compose(self)` — No docstring provided.
- `on_button_pressed(self, event)` — No docstring provided.

## cli/widgets/detail_panel.py

### Classes

#### DetailPanel

Right-side panel showing appointment details with edit mode support.

##### Methods

- `__init__(self, **kwargs)` — No docstring provided.
- `edit_mode(self)` — No docstring provided.
- `create_mode(self)` — No docstring provided.
- `dirty(self)` — No docstring provided.
- `current_appointment(self)` — No docstring provided.
- `compose(self)` — No docstring provided.
- `show_appointment(self, appt, label_service=None, display_tz=None)` — Display appointment in read-only mode.
- `_fmt_dt(self, dt)` — Format a datetime in the configured display timezone.
- `_render_read_only(self, appt, label_service=None)` — Render all fields as read-only static text.
- `enter_edit_mode(self)` — Switch to edit mode with editable field display.
- `enter_create_mode(self, defaults)` — Switch to create mode with empty/default fields.
- `_render_edit_form(self, appt)` — Render fields as an editable form display.
- `_get_field_values(self, appt)` — Extract editable field values from an appointment.
- `update_field(self, field_name, value)` — Update a field value and mark as modified.
- `_apply_field_to_appointment(self, field_name, value)` — Apply a field value to the current appointment object.
- `get_changes(self)` — Return (old_values, new_values) dicts for changed fields only.
- `validate_fields(self)` — Validate the current appointment fields. Returns a list of error messages.
- `discard_changes(self)` — Revert all fields to original values.
- `show_help(self)` — Display help text when no appointment is selected.

### Functions

- `_format_recurrence(rec)` — Format recurrence dict as a human-readable summary.

## cli/widgets/filter_bar.py

### Classes

#### FilterChanged

Posted when any filter changes.

#### FilterBar

Filter bar with dynamic label toggles, date range, and search toggles.

##### Methods

- `__init__(self, labels=None, default_label_ids=None, default_start='', default_end='', include_description=False, **kwargs)` — No docstring provided.
- `compose(self)` — No docstring provided.
- `_iter_label_buttons(self, labels)` — No docstring provided.
- `_create_label_button(self, label)` — No docstring provided.
- `update_labels(self, labels)` — No docstring provided.
- `_swap_label_buttons(self)` — No docstring provided.
- `selected_label_ids(self)` — No docstring provided.
- `start_date(self)` — No docstring provided.
- `end_date(self)` — No docstring provided.
- `search_in_description(self)` — No docstring provided.
- `on_input_changed(self, event)` — No docstring provided.
- `on_button_pressed(self, event)` — No docstring provided.
- `on_switch_changed(self, event)` — No docstring provided.
- `toggle_label(self, label_id)` — No docstring provided.
- `focus_search(self)` — No docstring provided.

## framework/__init__.py

### Functions

- `configure_logging(level='INFO', logfile='groupalarm.log', max_bytes=5 * 1024 * 1024, backup_count=5)` — Configure root logger to log to console and a rotating file.



- level: logging level name (e.g. 'INFO', 'DEBUG')

- logfile: path to rotating logfile; if None, file logging is disabled

- max_bytes, backup_count: rotation settings

## framework/appointment.py

### Classes

#### Appointment

No docstring provided.

##### Methods

- `validate(self)` — Validate appointment fields.



Raises

------

ValueError

    If required fields are missing or invalid (name, start/end dates, organizationID).
- `to_api_payload(self)` — Return the appointment as a JSON-serializable payload for the API.



The method validates the appointment and returns a dictionary matching

the GroupAlarm API schema. When ``self.id`` is present it will be included

in the payload (required for update operations).



Returns

-------

dict

    JSON-serializable payload suitable for POST/PUT requests.

## framework/client.py

### Classes

#### AppointmentNotFound

Raised when an appointment id is not found on the GroupAlarm server.

#### GroupAlarmClient

Client for interacting with the GroupAlarm REST API.



The client supports creating, updating and querying appointments, and

implements simple retry/backoff logic for transient failures. In ``dry_run``

mode HTTP calls are skipped and payloads are logged instead.

##### Methods

- `__init__(self, token, dry_run=False, base_url='https://app.groupalarm.com/api/v1')` — Create a GroupAlarmClient.



Parameters

----------

token : str or None

    Personal-Access-Token used for authenticated requests. If ``None``

    and ``dry_run`` is ``False`` some methods will raise :class:`ValueError`.

dry_run : bool, optional

    When ``True`` API calls are not executed and payloads are only logged.

base_url : str, optional

    Base URL for the GroupAlarm API (default: production API).
- `create_appointment(self, appt, retries=3, backoff=1.0)` — Create an appointment in GroupAlarm.



Parameters

----------

appt : Appointment

    The appointment object to create (will be validated via ``Appointment.validate``).

retries : int, optional

    Number of retries for transient errors (5xx) (default: 3).

backoff : float, optional

    Initial backoff in seconds for retries; it will be multiplied on each retry.



Returns

-------

dict

    The parsed JSON response from the API (may include the created ``id``).



Raises

------

ValueError

    If a token is required but not provided (non-dry run).

requests.RequestException

    For network or HTTP errors after exhausting retries.
- `update_appointment(self, appt, strategy='all', retries=2, backoff=1.0)` — Update an existing appointment identified by ``appt.id``.



Parameters

----------

appt : Appointment

    The appointment to update. ``appt.id`` must be set.

retries : int, optional

    Number of retries for transient errors (5xx) (default: 2).

backoff : float, optional

    Initial backoff in seconds for retries; it will be multiplied on each retry.



Returns

-------

dict

    The parsed JSON response from the API (may include the updated ``id``).



Raises

------

ValueError

    If ``appt.id`` is not set or token missing when required.

AppointmentNotFound

    If the server returns a 404 for the given id.

requests.RequestException

    For network or HTTP errors after exhausting retries.
- `get_appointment(self, id_)` — Retrieve a single appointment by id.



Parameters

----------

id_ : int

    The appointment id to fetch.



Returns

-------

dict

    The appointment JSON object as returned by the API.



Raises

------

AppointmentNotFound

    If the server responds with 404.

requests.RequestException

    For other HTTP/network errors.
- `list_appointments(self, start, end, type_='personal', organization_id=None)` — List appointments in the specified time range.



Parameters

----------

start : str

    ISO 8601 start timestamp for the range.

end : str

    ISO 8601 end timestamp for the range.

type_ : str, optional

    Appointment type filter (``'personal'`` or ``'organization'``).

organization_id : int, optional

    Organization id when querying organization appointments.



Returns

-------

list

    A list of appointment JSON objects.
- `delete_appointment(self, id_, strategy='all', time_=None, retries=2, backoff=1.0)` — No docstring provided.
- `list_labels(self, organization_id, label_type='normal')` — No docstring provided.

## framework/config.py

### Classes

#### AppConfig

No docstring provided.

### Functions

- `load_config(path=Path('.groupalarm.toml'))` — No docstring provided.
- `save_config(config, path=Path('.groupalarm.toml'))` — No docstring provided.

## framework/exporter.py

### Functions

- `_format_datetime(dt, tz_name)` — No docstring provided.
- `export_appointments(appointments, output_path, timezone='Europe/Berlin')` — No docstring provided.

## framework/importer_token.py

### Classes

#### ImporterToken

Generate and validate compact importer tokens embedded in appointment descriptions.



Token format: [GA-IMPORTER:<shortid>|<ts>|<chk4>]

- shortid: first 8 hex chars of UUID4

- ts: UTC timestamp YYYYMMDDHHMMSS (14 digits)

- chk4: first 4 hex chars of sha1(shortid + ts)

##### Methods

- `create_token()` — Create a compact importer token.



Returns

-------

str

    Token string in the format ``[GA-IMPORTER:shortid|YYYYMMDDHHMMSS|chk]``.
- `find_in_text(text)` — Search for a token inside free text and return the token if found.



Parameters

----------

text : str or None

    Text to scan for a token.



Returns

-------

str or None

    The token string if found, otherwise ``None``.
- `validate_token(token)` — Validate token checksum.



Parameters

----------

token : str

    Token string to validate.



Returns

-------

bool

    ``True`` if checksum matches, otherwise ``False``.

## framework/importers.py

### Classes

#### ExcelImporter

Importer for Excel files using :mod:`pandas`.



The importer caches the read DataFrame so modifications can be persisted back

to disk with :meth:`save`.

##### Methods

- `__init__(self, filename, sheet_name=None, date_column=None)` — Create an ExcelImporter.



Parameters

----------

filename : str

    Path to the Excel file.

sheet_name : str, optional

    Sheet name to read (default: first sheet).

date_column : str, optional

    Optional column name used to filter out rows with missing dates.
- `_load(self)` — No docstring provided.
- `rows(self)` — Yield rows as :class:`pandas.Series` objects.



Yields

------

pandas.Series

    Rows from the loaded sheet, optionally filtered by ``date_column``.
- `set_value(self, index, column, value)` — Set a value in the internal DataFrame at ``index`` and ``column``.



The change is kept in memory until :meth:`save` is called.
- `save(self)` — Persist the current DataFrame back to the Excel file (overwrites file).

#### CSVImporter

Importer for CSV files that supports read, in-memory mutation and save.



The importer attempts multiple common encodings when reading (useful for

Excel-generated CSV files). It preserves the detected encoding when saving.

##### Methods

- `__init__(self, filename, delimiter=',', date_column=None, encoding='cp1252')` — Create a CSVImporter.



Parameters

----------

filename : str

    Path to the CSV file.

delimiter : str, optional

    Field delimiter (default: ',').

date_column : str, optional

    Optional column name used to filter out rows with missing dates.

encoding : str, optional

    Preferred encoding to try first when reading (default: 'cp1252').
- `_load(self)` — No docstring provided.
- `rows(self)` — Yield rows as :class:`pandas.Series` objects.



Yields

------

pandas.Series

    Rows from the loaded CSV, optionally filtered by ``date_column``.
- `set_value(self, index, column, value)` — Set a value in the internal DataFrame at ``index`` and ``column``.



If ``column`` does not exist it will be created.
- `save(self)` — Persist the DataFrame back to the CSV file using the detected encoding.

## framework/label_mapper.py

### Functions

- `map_labels_from_participants(text, token_map=None)` — Map a free-text participants cell to a list of label IDs.



    Parameters

    ----------

    text : str

        Free-text participants field (may contain tokens separated by commas, semicolons or newlines).

    token_map : dict, optional

        Mapping from token strings to label id(s). Defaults to :data:`DEFAULT_TOKEN_MAP`.



    Returns

    -------

    list of int

        Sorted unique label IDs that matched tokens found in ``text``.



    Notes

    -----

    Matching is case-insensitive. The function first attempts a word-boundary regex

    search and falls back to a substring match if necessary.



    Examples

    --------

    >>> s = "1.TZ/B

1.TZ/FGr N

1.TZ/ZTr TZ TZ"

    >>> map_labels_from_participants(s)

    [40427, 40433, 40436]

## framework/log_sanitizer.py

### Classes

#### ApiKeySanitizer

Logging filter that replaces the API key in log messages with '***'.

##### Methods

- `__init__(self, api_key)` — No docstring provided.
- `filter(self, record)` — No docstring provided.

### Functions

- `install_api_key_sanitizer(api_key)` — Install the API key sanitizer on the root logger.

## framework/mapper.py

### Classes

#### Mapper

Map a row (pandas.Series) to an Appointment using a mapping dict provided by the user.



Mapping value options:

  - callable(row, helpers) -> value

  - string with `{}` placeholders -> format with row dict

  - string column name -> direct column value

  - constants (int, list, dict) depending on the field

  - special dict for notificationDate: {"days_before": 5} or {"minutes_before": 60}

##### Methods

- `__init__(self, mapping, defaults=None)` — Create a Mapper.



Parameters

----------

mapping : dict

    User-provided mapping specification that defines how to construct

    Appointment fields from a source row.

defaults : dict, optional

    Default values (timezone, start/end hour, etc.) applied when

    mapping values are missing.
- `_eval(self, key, row)` — Evaluate a mapping spec for a given key using the provided row.



Parameters

----------

key : str

    The mapping key (e.g. ``'name'``, ``'labelIDs'``).

row : pandas.Series

    The source row to extract values from.



Returns

-------

Any

    The evaluated value for the mapping key.
- `map_row(self, row)` — Map a source row into an :class:`Appointment` instance.



Parameters

----------

row : pandas.Series

    A single input row as returned by an importer.



Returns

-------

Appointment

    The constructed :class:`Appointment` object ready for validation and API submission.

## framework/runner.py

### Classes

#### Runner

Execute mapping + API synchronization between a tabular source and GroupAlarm.



The Runner reads rows from an importer (CSV/Excel), maps each row into an

:class:`Appointment` using a :class:`Mapper` and then either creates or

updates the appointment in GroupAlarm. By default created appointments get a

short importer token appended to their description and both the token and

the returned ``id`` are persisted back to the source file so future runs

can reliably update the appointment.

##### Methods

- `__init__(self, importer, mapping, defaults=None, dry_run=True, id_column='groupalarm_id', token_column='ga_importer_token')` — Create a Runner instance.



Parameters

----------

importer : object

    An importer instance providing a ``rows()`` generator and optional

    ``set_value(index, column, value)`` and ``save()`` methods.

mapping : dict

    Mapping specification passed to :class:`Mapper` to convert rows to

    :class:`Appointment` objects.

defaults : dict, optional

    Defaults passed to the :class:`Mapper` (timezone, start/end hour, etc.).

dry_run : bool, optional

    When ``True`` no HTTP calls are made; payloads are only logged.

id_column : str, optional

    Column name used to read/write the GroupAlarm appointment id.

token_column : str, optional

    Column name used to read/write the importer token (for robust lookup).
- `run(self, prompt_token=True, token=None)` — Process all rows from the importer and sync with GroupAlarm.



For each row the method maps the row to an :class:`Appointment` and then

decides whether to create a new appointment (no ``id`` present) or update

an existing one (``id`` present). Created appointments get an importer

token appended to their description; updates may add a token if missing.



Parameters

----------

prompt_token : bool, optional

    Prompt the user for a Personal-Access-Token when running in non-dry mode.

token : str, optional

    Personal-Access-Token to use for GroupAlarm API calls. If ``None`` and

    ``prompt_token`` is ``True`` the user will be prompted; required when

    ``dry_run`` is ``False``.

## framework/utils.py

### Functions

- `parse_date(value, hour=None, tz='UTC', fmt=None)` — Parse a value into a timezone-aware :class:`datetime.datetime`.



Parameters

----------

value : str or datetime-like

    Input value to parse. May be a :class:`str`, :class:`pandas.Timestamp`, :class:`datetime.datetime` or date-like object.

hour : int, optional

    If provided and the parsed value has no time component, set the hour to this value (minutes default to zero).

tz : str, optional

    IANA timezone string to attach to the resulting datetime (default: ``"UTC"``).

fmt : str, optional

    Explicit :func:`datetime.strptime` format string (e.g. ``"%d.%m.%Y %H:%M"``). If provided an initial ``strptime`` attempt will be made and on failure the function falls back to ``dateutil.parser.parse`` for greater robustness.



Returns

-------

datetime

    A timezone-aware :class:`datetime.datetime` instance.



Raises

------

ValueError

    If ``value`` is ``None``.



Notes

-----

The function will attach timezone information using :mod:`zoneinfo` when available, otherwise falls back to :mod:`dateutil.tz`.
- `relative_notification(start, days_before=0, minutes_before=0)` — Compute a notification datetime relative to a start datetime.



Parameters

----------

start : datetime

    The appointment start datetime.

days_before : int, optional

    Number of days before ``start`` to schedule the notification.

minutes_before : int, optional

    Number of minutes before ``start`` to schedule the notification.



Returns

-------

datetime

    The computed notification datetime.
- `clean_text(text, remove_newlines=True, collapse_whitespace=True)` — Normalize and clean a text value.



    Parameters

    ----------

    text : str or None

        The text to normalize. If ``None`` returns ``None``.

    remove_newlines : bool, optional

        Replace newline sequences with a single space (default: ``True``).

    collapse_whitespace : bool, optional

        Collapse consecutive whitespace characters into a single space (default: ``True``).



    Returns

    -------

    str or None

        The cleaned text or ``None`` if input was ``None``.



    Examples

    --------

    >>> clean_text('foo

bar')

    'foo bar'

## groupalarm_cli.py

### Functions

- `main()` — No docstring provided.

## scripts/generate_api_docs.py

### Classes

#### FunctionDoc

No docstring provided.

#### ClassDoc

No docstring provided.

#### ModuleDoc

No docstring provided.

##### Methods

- `module_heading(self)` — No docstring provided.

### Functions

- `safe_unparse(node)` — No docstring provided.
- `clean_docstring(value)` — No docstring provided.
- `should_skip(path)` — No docstring provided.
- `format_arguments(args)` — No docstring provided.
- `build_function_doc(node)` — No docstring provided.
- `build_class_doc(node)` — No docstring provided.
- `parse_module(path, *, root)` — No docstring provided.
- `iter_python_files(root)` — No docstring provided.
- `render_markdown(modules)` — No docstring provided.
- `generate_docs(root, output)` — No docstring provided.
- `parse_args()` — No docstring provided.
- `main()` — No docstring provided.

## tests/test_app.py

### Functions

- `_make_mock_client()` — No docstring provided.
- `_make_app(client=None, dry_run=False)` — No docstring provided.
- `test_app_startup_loads_appointments()` — T017: Verify app starts and appointment list is populated.
- `test_app_startup_calls_list_labels()` — T017: Verify labels are fetched on startup.
- `test_search_filters_appointments()` — T018: Verify search narrows the appointment list.
- `test_search_no_match_shows_empty()` — T019: Verify search with no match shows empty list.
- `test_description_search_requires_toggle()` — T018: Description field is searched only when toggle is enabled.
- `test_dry_run_banner_shown()` — Verify dry-run banner is visible when --dry-run is active.
- `test_dry_run_banner_hidden_by_default()` — Verify dry-run banner is hidden when --dry-run is not active.
- `test_detail_panel_populated_on_selection()` — T029: Select appointment in list -> detail panel shows fields.
- `test_edit_mode_toggle()` — T030: Enter edit mode -> fields become editable, indicator shown.
- `test_export_empty_list_shows_message()` — T041: Export with empty list -> notification shown.
- `test_new_appointment_creates_form()` — T045: Press n -> detail panel opens with default fields.
- `test_delete_no_selection_shows_hint()` — T049: Delete with no selection -> notification shown.
- `test_delete_triggers_confirmation()` — T049: Select appointment -> press d -> confirmation dialog shown.
- `test_recurring_delete_shows_strategy()` — T050: Recurring appointment delete -> strategy selector shown.
- `test_label_filter_toggles_appointments()` — T018: Click label toggle button -> only matching appointments shown.
- `test_date_filters_limit_appointments()` — T018: Setting start/end dates narrows the appointment list.
- `test_date_filter_reload_calls_api_with_range()` — T018: Adjusting date inputs triggers a fresh API load with full range.
- `test_label_buttons_only_show_used_labels()` — Label buttons list only labels present in the current dataset.
- `test_duplicate_ids_are_skipped_in_table()` — App should not crash when API returns duplicate appointment IDs.

## tests/test_appointment.py

### Functions

- `_make_appt(**kwargs)` — No docstring provided.
- `test_recurrence_defaults_to_none()` — No docstring provided.
- `test_recurrence_populated_from_dict()` — No docstring provided.
- `test_recurrence_not_in_api_payload()` — No docstring provided.
- `test_recurrence_none_not_in_payload()` — No docstring provided.

## tests/test_client.py

### Functions

- `make_appt()` — No docstring provided.
- `test_create_appointment_dry_run_no_token()` — No docstring provided.
- `test_create_appointment_requires_token_when_not_dry()` — No docstring provided.
- `test_create_appointment_posts(monkeypatch)` — No docstring provided.
- `test_update_appointment_dry_run_no_token()` — No docstring provided.
- `test_update_appointment_requires_token_when_not_dry()` — No docstring provided.
- `test_update_appointment_puts(monkeypatch)` — No docstring provided.
- `test_get_appointment_dry_run_no_token()` — No docstring provided.
- `test_get_appointment_not_found_raises(monkeypatch)` — No docstring provided.
- `test_update_appointment_raises_not_found(monkeypatch)` — No docstring provided.
- `test_get_appointment_returns_json(monkeypatch)` — No docstring provided.
- `test_list_labels_returns_labels(monkeypatch)` — No docstring provided.
- `test_list_labels_with_type(monkeypatch)` — No docstring provided.
- `test_delete_appointment_dry_run()` — No docstring provided.
- `test_delete_appointment_requires_token()` — No docstring provided.
- `test_delete_appointment_sends_delete(monkeypatch)` — No docstring provided.
- `test_delete_appointment_with_strategy(monkeypatch)` — No docstring provided.
- `test_delete_appointment_invalid_strategy()` — No docstring provided.
- `test_delete_appointment_not_found(monkeypatch)` — No docstring provided.
- `test_update_appointment_with_strategy(monkeypatch)` — No docstring provided.
- `test_update_appointment_default_strategy_no_param(monkeypatch)` — No docstring provided.
- `test_update_appointment_invalid_strategy()` — No docstring provided.

## tests/test_config.py

### Functions

- `test_load_missing_file_returns_defaults(tmp_path)` — No docstring provided.
- `test_load_valid_toml(tmp_path)` — No docstring provided.
- `test_load_invalid_toml_raises(tmp_path)` — No docstring provided.
- `test_save_and_reload_roundtrip(tmp_path)` — No docstring provided.
- `test_organization_id_none_when_missing(tmp_path)` — No docstring provided.
- `test_unknown_keys_ignored(tmp_path)` — No docstring provided.

## tests/test_confirmation.py

### Functions

- `_make_mock_client()` — No docstring provided.
- `_make_app(client=None, dry_run=False)` — No docstring provided.
- `test_confirmation_dialog_confirm()` — T031: Verify confirmation dialog returns True on confirm.
- `test_confirmation_dialog_cancel()` — T031: Verify confirmation dialog returns False on cancel.
- `test_unsaved_changes_dialog_save()` — T032: Verify unsaved changes dialog returns 'save'.
- `test_unsaved_changes_dialog_discard()` — T032: Verify unsaved changes dialog returns 'discard'.
- `test_unsaved_changes_dialog_cancel()` — T032: Verify unsaved changes dialog returns 'cancel'.
- `test_build_update_diff()` — T031: Verify diff builder shows changed fields.
- `test_build_update_diff_no_changes()` — Verify diff with no changes.
- `test_build_create_summary()` — Verify create summary shows all non-empty fields.
- `test_build_delete_summary()` — Verify delete summary shows appointment name and period.

## tests/test_exporter.py

### Functions

- `_make_appt(id_=1, name='Test', description='desc [GA-IMPORTER:aabbccdd|20260101120000|abcd]')` — No docstring provided.
- `test_export_creates_xlsx_with_13_columns(tmp_path)` — No docstring provided.
- `test_export_contains_groupalarm_id_and_token(tmp_path)` — No docstring provided.
- `test_export_empty_list_raises(tmp_path)` — No docstring provided.
- `test_export_multiple_appointments(tmp_path)` — No docstring provided.
- `test_export_appointment_without_token(tmp_path)` — No docstring provided.

## tests/test_importer_token.py

### Functions

- `test_create_and_find_token()` — No docstring provided.
- `test_token_format_is_short()` — No docstring provided.
- `test_find_none()` — No docstring provided.

## tests/test_importers.py

### Functions

- `test_csv_importer_reads_cp1252(tmp_path)` — No docstring provided.

## tests/test_label_mapper.py

### Functions

- `test_map_labels_simple()` — No docstring provided.
- `test_map_labels_multiple_and_duplicates()` — No docstring provided.
- `test_map_labels_case_insensitive_and_substring()` — No docstring provided.
- `test_map_labels_empty_returns_empty()` — No docstring provided.

## tests/test_log_sanitizer.py

### Functions

- `test_sanitizer_replaces_key_in_message()` — No docstring provided.
- `test_sanitizer_replaces_key_in_args()` — No docstring provided.
- `test_sanitizer_passes_through_clean_messages()` — No docstring provided.
- `test_install_adds_filter_to_root_logger()` — No docstring provided.
- `test_install_with_empty_key_does_nothing()` — No docstring provided.

## tests/test_mapper.py

### Functions

- `test_mapper_parses_dates_and_labels()` — No docstring provided.
- `test_name_cleaning_removes_newlines()` — No docstring provided.

## tests/test_runner.py

### Functions

- `test_runner_dry_run_does_not_require_token(tmp_path, caplog)` — No docstring provided.
- `test_runner_non_dry_run_calls_client(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_calls_update_when_id_present(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_writes_id_back_on_create(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_writes_id_back_on_update(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_creates_token_on_update_when_missing(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_writes_token_and_id_on_create(monkeypatch, tmp_path)` — No docstring provided.
- `test_runner_token_lookup_on_update(monkeypatch, tmp_path)` — No docstring provided.

## tests/test_utils.py

### Functions

- `test_parse_date_with_format_and_tz()` — No docstring provided.
- `test_parse_date_with_hour_only()` — No docstring provided.
- `test_relative_notification()` — No docstring provided.

---

## TUI UX Enhancements (Feature 002)

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `←` / `→` | Switch focus between appointment list and detail panel |
| `Ctrl + /` | Focus the start-date filter in the filter bar |
| `Ctrl + Shift + /` | Focus the end-date filter in the filter bar |
| `Ctrl + F` | Focus the search input in the filter bar |
| `e` | Enter edit mode for the selected appointment |
| `n` | Create a new appointment |
| `d` | Delete the selected appointment |
| `s` | Save changes (triggers diff preview) |
| `Esc` | Cancel edit mode / leave filter bar |
| `x` | Export visible appointments to Excel |
| `?` | Show help screen |
| `q` | Quit (with unsaved-changes guard) |

### Reminder Limits

Reminder values are validated against a fixed range enforced by the GroupAlarm API:

- **Minimum**: 0 minutes
- **Maximum**: 10 080 minutes (7 days)
- Supported units: `minutes`, `hours`, `days` (converted via `convert_reminder_to_minutes`)
- Values outside the range produce an inline warning in the edit form and block save

Constants defined in `framework/appointment.py`:
- `REMINDER_MIN_MINUTES = 0`
- `REMINDER_MAX_MINUTES = 10_080`
- `REMINDER_UNIT_FACTORS = {"minutes": 1, "hours": 60, "days": 1440}`

### Diff Preview & Confirmation Flow

When saving an edited appointment the TUI presents a confirmation dialog before persisting:

1. **Field-by-field diff** — Changed fields are grouped into sections:
   - **Grunddaten**: `name`, `description`
   - **Zeitplan**: `startDate`, `endDate`, `timezone`
   - **Benachrichtigungen**: `notificationDate`, `feedbackDeadline`
   - **Erinnerung**: `reminder`
   - **Labels**: `labelIDs`
   - **Weitere Felder**: any other modified fields

2. **Warnings section** — If labels reference names not found in the organization directory, a "Hinweise" (notices) section lists each unknown label.

3. **Recurrence strategy** — For recurring appointments, a strategy dialog appears first (`single` / `upcoming` / `all`) before the diff preview.

4. **Blocking confirmation** — The API call is not executed until the user explicitly confirms the dialog. Cancelling returns to edit mode without changes.

### Timestamp Formatting

All timestamps in the TUI are displayed in German format (`dd.mm.yyyy HH:MM`) converted from UTC to `Europe/Berlin` via `ZoneInfo`. If timezone conversion fails, the raw ISO string is displayed and a warning toast is dispatched.

Shared helpers in `framework/utils.py`:
- `format_de_datetime(dt, tz_name)` → `DisplayFormatResult(text, warning)`
- `parse_de_datetime(date_str, time_str, tz_name)` → `datetime`
- `DE_DATETIME_FORMAT = "%d.%m.%Y %H:%M"`

### Detail Panel Sections (View Mode)

The read-only detail view groups fields into sections with visual spacing:

- **Title + ID + Beschreibung** (or `—` placeholder)
- **Zeitplan**: Start, Ende, Zone
- **Labels**: Resolved names or IDs, Öffentlich flag
- **Benachrichtigungen** (conditional): Erinnerung, Benachrichtigung, Rückmeldefrist
- **Teilnehmer** (conditional): Participant count
- **Wiederholung** (conditional): Recurrence summary

### Filter Bar Behavior

- **Unfocused**: Shows up to 5 label toggles with a `+N weitere` helper chip
- **Focused** (via shortcut or Tab): Expands to show all labels instantly
- **Zero-match labels**: Muted `0` badge + "Keine Treffer" chip, but remain focusable
