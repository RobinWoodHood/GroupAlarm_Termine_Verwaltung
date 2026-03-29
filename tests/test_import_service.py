"""Unit tests for import service (Tier 1/Tier 2 parsing + upload)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cli.services import import_service
from framework.appointment import Appointment
from framework.config import ImportConfig
from framework.importer_token import ImporterToken


class _Row(dict):
    """Minimal row object compatible with Mapper expectations."""

    def to_dict(self):
        """Execute `to_dict`."""
        return dict(self)


def _iso(dt: datetime) -> str:
    """Internal helper for `iso`."""
    return dt.astimezone(timezone.utc).isoformat()


def _tier1_row(
    name: str = "Training A",
    *,
    appt_id: int | None = None,
    token: str = "",
):
    """Internal helper for `tier1_row`."""
    start = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
    return _Row(
        {
            "name": name,
            "description": "desc",
            "startDate": _iso(start),
            "endDate": _iso(end),
            "organizationID": 100,
            "labelIDs": "1,2",
            "isPublic": "true",
            "reminder": "30",
            "notificationDate": _iso(start),
            "feedbackDeadline": "",
            "timezone": "Europe/Berlin",
            "groupalarm_id": appt_id,
            "ga_importer_token": token,
        }
    )


class _ImporterStub:
    """Container class `_ImporterStub`."""
    def __init__(self, _filename: str, sheet_name: str | None = None):
        """Initialize the _ImporterStub instance."""
        self.sheet_name = sheet_name

    def rows(self):
        """Execute `rows`."""
        return iter([])


def test_parse_excel_tier1_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test `parse_excel_tier1_valid` behavior."""
    file_path = tmp_path / "sample.xlsx"
    file_path.write_text("x", encoding="utf-8")

    class _LocalImporter(_ImporterStub):
        """Container class `_LocalImporter`."""
        def rows(self):
            """Execute `rows`."""
            return iter([_tier1_row(appt_id=None, token="[GA-IMPORTER:abcd1234|20260301000000|0abc]")])

    monkeypatch.setattr(import_service, "ExcelImporter", _LocalImporter)

    session = import_service.parse_excel(
        str(file_path),
        import_config=None,
        organization_id=100,
        timezone="Europe/Berlin",
    )

    assert session.column_mapping_used == "tier1-default"
    assert len(session.appointments) == 1
    assert len(session.skipped_rows) == 0
    appt = session.appointments[0]
    assert appt.name == "Training A"
    assert appt.organizationID == 100
    assert appt.labelIDs == [1, 2]
    assert appt.id is None
    assert "GA-IMPORTER" in appt.description


def test_parse_excel_tier1_skipped_rows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test `parse_excel_tier1_skipped_rows` behavior."""
    file_path = tmp_path / "sample.xlsx"
    file_path.write_text("x", encoding="utf-8")

    broken = _tier1_row(name="")

    class _LocalImporter(_ImporterStub):
        """Container class `_LocalImporter`."""
        def rows(self):
            """Execute `rows`."""
            return iter([broken])

    monkeypatch.setattr(import_service, "ExcelImporter", _LocalImporter)

    session = import_service.parse_excel(str(file_path), None, 100, "Europe/Berlin")
    assert len(session.appointments) == 0
    assert len(session.skipped_rows) == 1
    assert "name" in session.skipped_rows[0].reason.lower()


def test_parse_excel_empty_file_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test `parse_excel_empty_file_raises` behavior."""
    file_path = tmp_path / "sample.xlsx"
    file_path.write_text("x", encoding="utf-8")

    class _LocalImporter(_ImporterStub):
        """Container class `_LocalImporter`."""
        def rows(self):
            """Execute `rows`."""
            return iter([])

    monkeypatch.setattr(import_service, "ExcelImporter", _LocalImporter)

    with pytest.raises(ValueError, match="No data rows"):
        import_service.parse_excel(str(file_path), None, 100, "Europe/Berlin")


def test_load_mapping_module_valid(tmp_path: Path):
    """Test `load_mapping_module_valid` behavior."""
    mapping_file = tmp_path / "mapping.py"
    mapping_file.write_text(
        "mapping = {'name': 'name', 'description': 'description', 'startDate': 'startDate', 'endDate': 'endDate', 'organizationID': 100}\n"
        "defaults = {'timezone': 'Europe/Berlin'}\n",
        encoding="utf-8",
    )

    mapping, defaults = import_service.load_mapping_module(str(mapping_file))
    assert isinstance(mapping, dict)
    assert isinstance(defaults, dict)
    assert defaults["timezone"] == "Europe/Berlin"


def test_load_mapping_module_missing_file():
    """Test `load_mapping_module_missing_file` behavior."""
    with pytest.raises(FileNotFoundError):
        import_service.load_mapping_module("definitely_missing_mapping.py")


def test_load_mapping_module_syntax_error(tmp_path: Path):
    """Test `load_mapping_module_syntax_error` behavior."""
    mapping_file = tmp_path / "broken.py"
    mapping_file.write_text("mapping = {\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Syntax error"):
        import_service.load_mapping_module(str(mapping_file))


def test_load_mapping_module_missing_mapping_attr(tmp_path: Path):
    """Test `load_mapping_module_missing_mapping_attr` behavior."""
    mapping_file = tmp_path / "missing.py"
    mapping_file.write_text("defaults = {}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        import_service.load_mapping_module(str(mapping_file))


def test_parse_excel_tier2_uses_mapping_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Test `parse_excel_tier2_uses_mapping_file` behavior."""
    file_path = tmp_path / "sample.xlsx"
    file_path.write_text("x", encoding="utf-8")

    mapping_file = tmp_path / "tier2_map.py"
    mapping_file.write_text(
        "mapping = {\n"
        "  'name': 'title',\n"
        "  'description': 'text',\n"
        "  'startDate': 'start',\n"
        "  'endDate': 'end',\n"
        "  'organizationID': 100,\n"
        "  'labelIDs': [1],\n"
        "  'isPublic': True\n"
        "}\n"
        "defaults = {'timezone': 'Europe/Berlin'}\n",
        encoding="utf-8",
    )

    row = _Row(
        {
            "title": "Tier2 Name",
            "text": "Tier2 Desc",
            "start": _iso(datetime(2026, 3, 2, 8, 0, tzinfo=timezone.utc)),
            "end": _iso(datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)),
        }
    )

    class _LocalImporter(_ImporterStub):
        """Container class `_LocalImporter`."""
        def rows(self):
            """Execute `rows`."""
            return iter([row])

    monkeypatch.setattr(import_service, "ExcelImporter", _LocalImporter)

    session = import_service.parse_excel(
        str(file_path),
        import_config=ImportConfig(mapping_file=str(mapping_file), sheet_name="Sheet1"),
        organization_id=100,
        timezone="Europe/Berlin",
    )

    assert len(session.appointments) == 1
    assert session.column_mapping_used.startswith("tier2-module:")
    assert session.appointments[0].name == "Tier2 Name"


class _ClientStub:
    """Container class `_ClientStub`."""
    def __init__(self):
        """Initialize the _ClientStub instance."""
        self.created: list[Appointment] = []
        self.updated: list[Appointment] = []
        self.lookup_result = []

    def create_appointment(self, appt: Appointment):
        """Execute `create_appointment`."""
        self.created.append(appt)
        return {"id": 1234}

    def update_appointment(self, appt: Appointment):
        """Execute `update_appointment`."""
        self.updated.append(appt)
        return {"ok": True}

    def list_appointments(self, start: str, end: str, type_: str = "personal", organization_id: int | None = None):
        """Execute `list_appointments`."""
        return self.lookup_result


def _appt(name: str, appt_id: int | None = None, description: str = "desc") -> Appointment:
    """Internal helper for `appt`."""
    start = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return Appointment(
        id=appt_id,
        name=name,
        description=description,
        startDate=start,
        endDate=start.replace(hour=12),
        organizationID=100,
        timezone="Europe/Berlin",
    )


def test_upload_create_and_update_paths():
    """Test `upload_create_and_update_paths` behavior."""
    client = _ClientStub()
    token = ImporterToken.create_token()
    appointments = [
        _appt("Create Me", None),
        _appt("Update Me", 42, description=f"existing\n{token}"),
    ]
    client.lookup_result = [{"id": 777, "description": f"server\n{token}"}]

    summary = import_service.upload(appointments, client, dry_run=False)

    assert summary.total == 2
    assert summary.created == 1
    assert summary.updated == 1
    assert summary.failed == 0
    assert len(client.created) == 1
    assert len(client.updated) == 1
    assert summary.results[0].appointment_start is not None
    assert summary.results[1].appointment_start is not None
    # Update uses resolved server ID from token lookup.
    assert client.updated[0].id == 777
    # New appointment always receives GA token.
    assert ImporterToken.find_in_text(client.created[0].description) is not None


def test_upload_token_not_found_fails_no_create():
    """Test `upload_token_not_found_fails_no_create` behavior."""
    client = _ClientStub()
    token = ImporterToken.create_token()
    appt = _appt("Missing Token", 99, description=f"body\n{token}")
    client.lookup_result = []

    summary = import_service.upload([appt], client, dry_run=False)

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert len(client.created) == 0
    assert len(client.updated) == 0
    assert "No server appointment found" in (summary.results[0].error or "")


def test_upload_id_without_token_fails_safely():
    """Test `upload_id_without_token_fails_safely` behavior."""
    client = _ClientStub()
    appt = _appt("No Token", 88, description="plain description")

    summary = import_service.upload([appt], client, dry_run=False)

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert len(client.created) == 0
    assert len(client.updated) == 0
    assert "no GA-IMPORTER token" in (summary.results[0].error or "")


def test_upload_ambiguous_token_match_fails():
    """Test `upload_ambiguous_token_match_fails` behavior."""
    client = _ClientStub()
    token = ImporterToken.create_token()
    appt = _appt("Ambiguous", 90, description=f"text\n{token}")
    client.lookup_result = [
        {"id": 1, "description": token},
        {"id": 2, "description": token},
    ]

    summary = import_service.upload([appt], client, dry_run=False)

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert "Ambiguous" in (summary.results[0].error or "")


def test_upload_resolved_update_not_found_fails():
    """Test `upload_resolved_update_not_found_fails` behavior."""
    class _FailUpdateClient(_ClientStub):
        """Container class `_FailUpdateClient`."""
        def update_appointment(self, appt: Appointment):
            """Execute `update_appointment`."""
            raise Exception("update failed")

    client = _FailUpdateClient()
    token = ImporterToken.create_token()
    appt = _appt("Fail Update", 101, description=f"text\n{token}")
    client.lookup_result = [{"id": 202, "description": f"x\n{token}"}]

    summary = import_service.upload([appt], client, dry_run=False)

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert "update failed" in (summary.results[0].error or "")


def test_upload_failure_records_error():
    """Test `upload_failure_records_error` behavior."""
    class _FailClient(_ClientStub):
        """Container class `_FailClient`."""
        def create_appointment(self, appt: Appointment):
            """Execute `create_appointment`."""
            raise RuntimeError("boom")

    client = _FailClient()
    summary = import_service.upload([_appt("Fail", None)], client, dry_run=False)

    assert summary.created == 0
    assert summary.updated == 0
    assert summary.failed == 1
    assert summary.results[0].action == "failed"
    assert "boom" in (summary.results[0].error or "")


def test_upload_dry_run_no_api_calls():
    """Test `upload_dry_run_no_api_calls` behavior."""
    client = _ClientStub()
    token = ImporterToken.create_token()
    summary = import_service.upload(
        [_appt("Dry", None), _appt("Dry2", 2, description=f"text\n{token}")],
        client,
        dry_run=True,
    )

    assert summary.dry_run is True
    assert summary.created == 1
    assert summary.updated == 1
    assert summary.failed == 0
    assert client.created == []
    assert client.updated == []
