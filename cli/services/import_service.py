"""Import service — Excel import lifecycle: parse, upload, summary."""
from __future__ import annotations

import importlib.util
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dateutil.parser import isoparse

from framework.appointment import Appointment
from framework.client import AppointmentNotFound, GroupAlarmClient
from framework.config import ImportConfig
from framework.importer_token import ImporterToken
from framework.importers import ExcelImporter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model dataclasses (per data-model.md)
# ---------------------------------------------------------------------------


@dataclass
class SkippedRow:
    """Record of a row that could not be parsed into an appointment."""

    row_index: int
    reason: str


@dataclass
class ImportSession:
    """Transient in-memory state for one import workflow."""

    source_path: str
    appointments: list[Appointment]
    skipped_rows: list[SkippedRow] = field(default_factory=list)
    column_mapping_used: str = "tier1-default"
    label_warnings: list[str] = field(default_factory=list)


@dataclass
class UploadResult:
    """Outcome of a single appointment upload operation."""

    appointment_name: str
    action: str  # "created", "updated", or "failed"
    appointment_start: Optional[str] = None
    error: Optional[str] = None
    appointment_id: Optional[int] = None


@dataclass
class ImportSummary:
    """Aggregate outcome of the full upload operation."""

    total: int
    created: int = 0
    updated: int = 0
    failed: int = 0
    dry_run: bool = False
    results: list[UploadResult] = field(default_factory=list)

    @property
    def failed_results(self) -> list[UploadResult]:
        """Execute `failed_results`."""
        return [r for r in self.results if r.action == "failed"]

    @property
    def success_rate(self) -> float:
        """Execute `success_rate`."""
        if self.total == 0:
            return 0.0
        return (self.created + self.updated) / self.total * 100


# ---------------------------------------------------------------------------
# Default column mapping — Tier 1 (matches exporter.COLUMNS)
# ---------------------------------------------------------------------------


def _parse_optional_int(value) -> Optional[int]:
    """Parse a value to int, returning None for empty/NaN."""
    if value is None:
        return None
    import pandas as pd

    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_optional_datetime(value):
    """Parse ISO 8601 string to datetime, returning None for empty/NaN."""
    if value is None:
        return None
    import pandas as pd

    if isinstance(value, float) and pd.isna(value):
        return None
    s = str(value).strip()
    if not s:
        return None
    return isoparse(s)


def _parse_label_ids(value) -> list[int]:
    """Parse comma-separated label IDs string to list[int]."""
    if value is None:
        return []
    import pandas as pd

    if isinstance(value, float) and pd.isna(value):
        return []
    s = str(value).strip()
    if not s:
        return []
    result = []
    for part in s.split(","):
        part = part.strip()
        if part:
            result.append(int(part))
    return result


def _parse_labels(
    value,
    label_resolver: "Callable[[str], int | None] | None" = None,
) -> tuple[list[int], list[str]]:
    """Parse comma-separated label names/IDs to (resolved_ids, warnings).

    For each token:
    1. Try int() first (backward compat with numeric ID exports).
    2. If not numeric and resolver is provided, resolve by name (case-insensitive).
    3. If resolver returns None, add a warning and skip the token.
    """
    if value is None:
        return [], []
    import pandas as pd

    if isinstance(value, float) and pd.isna(value):
        return [], []
    s = str(value).strip()
    if not s:
        return [], []
    result: list[int] = []
    warnings: list[str] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        # Try numeric ID first
        try:
            result.append(int(part))
            continue
        except ValueError:
            pass
        # Try name resolution
        if label_resolver is not None:
            resolved = label_resolver(part)
            if resolved is not None:
                result.append(resolved)
            else:
                warnings.append(f"Label '{part}' nicht gefunden")
        else:
            warnings.append(f"Label '{part}' nicht gefunden")
    return result, warnings


def _parse_bool(value) -> bool:
    """Parse boolean-ish value from Excel."""
    if isinstance(value, bool):
        return value
    if value is None:
        return True
    s = str(value).strip().lower()
    return s in ("true", "1", "yes", "ja")


def _safe_str(value) -> str:
    """Get string value, handling NaN/None."""
    if value is None:
        return ""
    import pandas as pd

    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


# The 13-column mapping matching framework/exporter.COLUMNS
DEFAULT_IMPORT_COLUMNS: list[str] = [
    "name",
    "description",
    "startDate",
    "endDate",
    "organizationID",
    "labelIDs",
    "isPublic",
    "reminder",
    "notificationDate",
    "feedbackDeadline",
    "timezone",
    "groupalarm_id",
    "ga_importer_token",
]


# ---------------------------------------------------------------------------
# Tier 1: parse a row using the default column mapping
# ---------------------------------------------------------------------------


def _parse_row_tier1(
    row, row_index: int, default_org_id: int, default_tz: str,
    label_resolver: "Callable[[str], int | None] | None" = None,
) -> tuple[Optional[Appointment], Optional[SkippedRow], list[str]]:
    """Parse a single row using the Tier 1 default column mapping.

    Returns (appointment, None, label_warnings) on success or
    (None, skipped_row, []) on failure.
    """
    try:
        name = _safe_str(row.get("name"))
        if not name:
            logger.warning(
                "Tier1 parse error at row %d: Missing required field: name\nRow data: %s",
                row_index, row.to_dict(),
            )
            return None, SkippedRow(row_index=row_index, reason="Missing required field: name"), []

        description = _safe_str(row.get("description"))

        start_date = _parse_optional_datetime(row.get("startDate"))
        if start_date is None:
            logger.warning(
                "Tier1 parse error at row %d: Missing or invalid startDate\nRow data: %s",
                row_index, row.to_dict(),
            )
            return None, SkippedRow(row_index=row_index, reason="Missing or invalid startDate"), []

        end_date = _parse_optional_datetime(row.get("endDate"))
        if end_date is None:
            logger.warning(
                "Tier1 parse error at row %d: Missing or invalid endDate\nRow data: %s",
                row_index, row.to_dict(),
            )
            return None, SkippedRow(row_index=row_index, reason="Missing or invalid endDate"), []

        org_id = _parse_optional_int(row.get("organizationID")) or default_org_id
        label_ids, label_warnings = _parse_labels(row.get("labelIDs"), label_resolver)
        is_public = _parse_bool(row.get("isPublic"))
        reminder = _parse_optional_int(row.get("reminder"))
        notification_date = _parse_optional_datetime(row.get("notificationDate"))
        feedback_deadline = _parse_optional_datetime(row.get("feedbackDeadline"))
        timezone_str = _safe_str(row.get("timezone")) or default_tz

        groupalarm_id = _parse_optional_int(row.get("groupalarm_id"))
        ga_importer_token = _safe_str(row.get("ga_importer_token"))

        # Re-append importer token to description if present
        if ga_importer_token:
            if ga_importer_token not in description:
                if description:
                    description = f"{description}\n{ga_importer_token}"
                else:
                    description = ga_importer_token

        appt = Appointment(
            name=name,
            description=description,
            startDate=start_date,
            endDate=end_date,
            organizationID=org_id,
            id=groupalarm_id,
            labelIDs=label_ids,
            isPublic=is_public,
            reminder=reminder,
            notificationDate=notification_date,
            feedbackDeadline=feedback_deadline,
            timezone=timezone_str,
        )
        return appt, None, label_warnings
    except Exception as exc:
        logger.warning(
            "Tier1 parse error at row %d: %s\nRow data: %s",
            row_index, exc, row.to_dict(),
        )
        return None, SkippedRow(row_index=row_index, reason=str(exc)), []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_mapping_module(mapping_file: str) -> tuple[dict, dict]:
    """Load a Python mapping module and extract mapping + defaults dicts.

    Parameters
    ----------
    mapping_file : str
        Absolute or project-relative path to a ``.py`` file.

    Returns
    -------
    tuple[dict, dict]
        ``(mapping, defaults)`` extracted from the module.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file is not ``.py``, has syntax errors, or lacks a ``mapping`` dict.
    """
    path = Path(mapping_file)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()

    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")
    if path.suffix != ".py":
        raise ValueError(f"Mapping file must be a .py file: {path}")

    module_name = path.stem
    logger.info("Loading import mapping module: %s", path)
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load mapping file: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except SyntaxError as exc:
        raise ValueError(f"Syntax error in mapping file {path}: {exc}") from exc
    except Exception as exc:
        if isinstance(exc, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Error loading mapping file {path}: {exc}") from exc

    if not hasattr(module, "mapping"):
        raise ValueError(f"Mapping file must export a 'mapping' dict: {path}")
    mapping = module.mapping
    if not isinstance(mapping, dict):
        raise ValueError(f"'mapping' attribute must be a dict: {path}")

    defaults = getattr(module, "defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}

    logger.info(
        "Loaded mapping module '%s' with %d mapping keys and %d default keys",
        path,
        len(mapping),
        len(defaults),
    )

    return mapping, defaults


def parse_excel(
    file_path: str,
    import_config: Optional[ImportConfig],
    organization_id: int,
    timezone: str,
    label_resolver: "Callable[[str], int | None] | None" = None,
) -> ImportSession:
    """Parse an Excel file into appointments using the three-tier mapping strategy.

    Parameters
    ----------
    file_path : str
        Absolute path to the Excel file.
    import_config : ImportConfig or None
        Import settings from config. ``None`` → Tier 1 default mapping.
    organization_id : int
        Default organization ID for appointments.
    timezone : str
        Default timezone (e.g. ``"Europe/Berlin"``).

    Returns
    -------
    ImportSession
        Parsed appointments and any skipped rows.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file has no data rows or mapping module has errors.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sheet_name = None
    if import_config and import_config.sheet_name:
        sheet_name = import_config.sheet_name

    # Determine tier
    use_tier2 = import_config is not None and import_config.mapping_file is not None

    logger.info(
        "Starting import parse: file=%s, tier=%s, sheet=%s",
        file_path,
        "tier2" if use_tier2 else "tier1",
        sheet_name if sheet_name is not None else "first",
    )

    if use_tier2 and import_config is not None and import_config.mapping_file is not None:
        # Tier 2: Python mapping module
        from framework.mapper import Mapper

        mapping_dict, defaults_dict = load_mapping_module(import_config.mapping_file)

        # Merge defaults with function params as fallbacks
        merged_defaults = dict(defaults_dict)
        merged_defaults.setdefault("timezone", timezone)
        merged_defaults.setdefault("organizationID", organization_id)

        mapper = Mapper(mapping_dict, merged_defaults)
        importer = ExcelImporter(file_path, sheet_name=sheet_name)

        appointments: list[Appointment] = []
        skipped_rows: list[SkippedRow] = []

        for row_index, row in enumerate(importer.rows()):
            try:
                appt = mapper.map_row(row)
                appointments.append(appt)
            except Exception as exc:
                logger.warning(
                    "Tier2 parse error at row %d: %s\nRow data: %s",
                    row_index, exc, row.to_dict(),
                )
                skipped_rows.append(SkippedRow(row_index=row_index, reason=str(exc)))

        if not appointments and not skipped_rows:
            raise ValueError(f"No data rows found in {file_path}")

        logger.info(
            "Import parse complete (tier2): appointments=%d skipped=%d",
            len(appointments),
            len(skipped_rows),
        )
        for sk in skipped_rows:
            logger.warning("Skipped row %d: %s", sk.row_index, sk.reason)
        for appt in appointments:
            logger.debug(
                "Parsed appointment: name=%r start=%s labels=%s",
                appt.name, appt.startDate, appt.labelIDs,
            )

        return ImportSession(
            source_path=os.path.abspath(file_path),
            appointments=appointments,
            skipped_rows=skipped_rows,
            column_mapping_used=f"tier2-module:{import_config.mapping_file}",
        )
    else:
        # Tier 1: default mapping
        importer = ExcelImporter(file_path, sheet_name=sheet_name)

        appointments = []
        skipped_rows = []
        all_label_warnings: list[str] = []

        for row_index, row in enumerate(importer.rows()):
            parsed_appt, skipped_row, row_label_warnings = _parse_row_tier1(
                row, row_index, organization_id, timezone,
                label_resolver=label_resolver,
            )
            if parsed_appt:
                appointments.append(parsed_appt)
            elif skipped_row:
                skipped_rows.append(skipped_row)
            all_label_warnings.extend(row_label_warnings)

        if not appointments and not skipped_rows:
            raise ValueError(f"No data rows found in {file_path}")

        logger.info(
            "Import parse complete (tier1): appointments=%d skipped=%d label_warnings=%d",
            len(appointments),
            len(skipped_rows),
            len(all_label_warnings),
        )
        for sk in skipped_rows:
            logger.warning("Skipped row %d: %s", sk.row_index, sk.reason)
        for warn in all_label_warnings:
            logger.warning("Label warning: %s", warn)
        for appt in appointments:
            logger.debug(
                "Parsed appointment: name=%r start=%s labels=%s",
                appt.name, appt.startDate, appt.labelIDs,
            )

        return ImportSession(
            source_path=os.path.abspath(file_path),
            appointments=appointments,
            skipped_rows=skipped_rows,
            column_mapping_used="tier1-default",
            label_warnings=all_label_warnings,
        )


def upload(
    appointments: list[Appointment],
    client: GroupAlarmClient,
    dry_run: bool,
) -> ImportSummary:
    """Upload appointments to GroupAlarm, creating or updating as appropriate.

    Parameters
    ----------
    appointments : list[Appointment]
        Appointments to upload.
    client : GroupAlarmClient
        Authenticated API client.
    dry_run : bool
        If ``True``, log payloads but do not send requests.

    Returns
    -------
    ImportSummary
        Per-appointment results.
    """
    results: list[UploadResult] = []
    created = 0
    updated = 0
    failed = 0

    logger.info("Starting import upload: total=%d dry_run=%s", len(appointments), dry_run)

    def _extract_token(appt: Appointment) -> Optional[str]:
        """Internal helper for `extract_token`."""
        return ImporterToken.find_in_text(appt.description)

    def _format_start(appt: Appointment) -> Optional[str]:
        """Internal helper for `format_start`."""
        try:
            return appt.startDate.astimezone().strftime("%d.%m.%Y %H:%M")
        except Exception:
            return None

    def _lookup_by_token(appt: Appointment, token: str):
        """Find server appointment by GA-IMPORTER token in appointment time window."""
        try:
            start = appt.startDate.astimezone().isoformat()
            end = appt.endDate.astimezone().isoformat()
        except Exception as exc:
            logger.error("Cannot build token lookup window for '%s': %s", appt.name, exc)
            return []

        try:
            candidates = client.list_appointments(
                start,
                end,
                type_="personal",
                organization_id=appt.organizationID,
            )
        except Exception as exc:
            logger.exception("Token lookup request failed for '%s': %s", appt.name, exc)
            return []

        matches = []
        for item in candidates or []:
            desc = item.get("description") or ""
            if token in desc:
                matches.append(item)
        return matches

    for appt in appointments:
        token = _extract_token(appt)

        if dry_run:
            action = "updated" if token else "created"
            logger.info("[DRY-RUN] Would %s: %s", action, appt.name)
            results.append(UploadResult(
                appointment_name=appt.name,
                appointment_start=_format_start(appt),
                action=action,
                appointment_id=appt.id,
            ))
            if action == "created":
                created += 1
            else:
                updated += 1
            continue

        try:
            if token:
                # Token-first identity resolution for updates.
                logger.info("Resolving server identity by token for '%s'", appt.name)
                matches = _lookup_by_token(appt, token)
                if len(matches) == 1:
                    resolved_id = matches[0].get("id")
                    if resolved_id is None:
                        raise ValueError("Token lookup returned match without id")

                    if appt.id != resolved_id:
                        logger.info(
                            "Resolved changed server id for '%s': imported=%s resolved=%s",
                            appt.name,
                            appt.id,
                            resolved_id,
                        )
                    appt.id = resolved_id
                    client.update_appointment(appt)
                    results.append(UploadResult(
                        appointment_name=appt.name,
                        appointment_start=_format_start(appt),
                        action="updated",
                        appointment_id=resolved_id,
                    ))
                    updated += 1
                elif len(matches) == 0:
                    reason = (
                        "No server appointment found for GA-IMPORTER token in time window; "
                        "update skipped to avoid duplicates"
                    )
                    logger.warning("%s: %s", appt.name, reason)
                    results.append(UploadResult(
                        appointment_name=appt.name,
                        appointment_start=_format_start(appt),
                        action="failed",
                        error=reason,
                    ))
                    failed += 1
                else:
                    reason = (
                        f"Ambiguous GA-IMPORTER token match ({len(matches)} appointments); "
                        "update skipped"
                    )
                    logger.error("%s: %s", appt.name, reason)
                    results.append(UploadResult(
                        appointment_name=appt.name,
                        appointment_start=_format_start(appt),
                        action="failed",
                        error=reason,
                    ))
                    failed += 1
            else:
                if appt.id is not None:
                    # Explicitly fail to avoid trusting mutable IDs for identity.
                    reason = (
                        "Appointment has id but no GA-IMPORTER token; cannot perform safe update"
                    )
                    logger.warning("%s: %s", appt.name, reason)
                    results.append(UploadResult(
                        appointment_name=appt.name,
                        appointment_start=_format_start(appt),
                        action="failed",
                        error=reason,
                        appointment_id=appt.id,
                    ))
                    failed += 1
                    continue

                # Create new appointment and always ensure token is present.
                token_added = ImporterToken.ensure_token(appt)
                if token_added:
                    logger.info("Added GA-IMPORTER token for new appointment '%s'", appt.name)
                resp = client.create_appointment(appt)
                new_id = resp.get("id") if isinstance(resp, dict) else None
                results.append(UploadResult(
                    appointment_name=appt.name,
                    appointment_start=_format_start(appt),
                    action="created",
                    appointment_id=new_id,
                ))
                created += 1
        except AppointmentNotFound:
            logger.error("Update target disappeared for '%s' during upload", appt.name)
            results.append(UploadResult(
                appointment_name=appt.name,
                appointment_start=_format_start(appt),
                action="failed",
                error="Resolved appointment not found during update",
                appointment_id=appt.id,
            ))
            failed += 1
        except Exception as exc:
            logger.error("Upload failed for '%s': %s", appt.name, exc)
            results.append(UploadResult(
                appointment_name=appt.name,
                appointment_start=_format_start(appt),
                action="failed",
                error=str(exc),
            ))
            failed += 1

    logger.info(
        "Import upload complete: total=%d created=%d updated=%d failed=%d dry_run=%s",
        len(appointments),
        created,
        updated,
        failed,
        dry_run,
    )

    return ImportSummary(
        total=len(appointments),
        created=created,
        updated=updated,
        failed=failed,
        dry_run=dry_run,
        results=results,
    )
