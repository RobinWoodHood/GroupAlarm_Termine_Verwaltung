from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tomli_w


@dataclass(frozen=True)
class ImportConfig:
    """Configuration for the Excel import workflow ([import] section)."""

    mapping_file: Optional[str] = None
    sheet_name: Optional[str] = None


@dataclass
class AppConfig:
    """Container class `AppConfig`."""
    organization_id: Optional[int] = None
    timezone: str = "Europe/Berlin"
    show_startup_welcome: bool = True
    date_range_days: int = 30
    default_label_ids: List[int] = field(default_factory=list)
    default_appointment_duration_hours: int = 4
    import_config: Optional[ImportConfig] = None


def load_config(path: Path = Path(".groupalarm.toml")) -> AppConfig:
    """Execute `load_config`."""
    if not path.exists():
        return AppConfig()
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {path}: {exc}") from exc

    general = data.get("general", {})
    defaults = data.get("defaults", {})

    import_section = data.get("import", None)
    import_config = None
    if import_section is not None:
        import_config = ImportConfig(
            mapping_file=import_section.get("mapping_file"),
            sheet_name=import_section.get("sheet_name"),
        )

    return AppConfig(
        organization_id=general.get("organization_id"),
        timezone=general.get("timezone", "Europe/Berlin"),
        show_startup_welcome=general.get("show_startup_welcome", True),
        date_range_days=defaults.get("date_range_days", 30),
        default_label_ids=defaults.get("label_ids", []),
        default_appointment_duration_hours=defaults.get("appointment_duration_hours", 4),
        import_config=import_config,
    )


def save_config(config: AppConfig, path: Path = Path(".groupalarm.toml")) -> None:
    """Execute `save_config`."""
    data: dict[str, dict[str, object]] = {
        "general": {
            "organization_id": config.organization_id,
            "timezone": config.timezone,
            "show_startup_welcome": config.show_startup_welcome,
        },
        "defaults": {
            "date_range_days": config.date_range_days,
            "label_ids": config.default_label_ids,
            "appointment_duration_hours": config.default_appointment_duration_hours,
        },
    }
    # Remove None values from general section
    data["general"] = {k: v for k, v in data["general"].items() if v is not None}

    if config.import_config is not None:
        import_data: dict[str, object] = {}
        if config.import_config.mapping_file is not None:
            import_data["mapping_file"] = config.import_config.mapping_file
        if config.import_config.sheet_name is not None:
            import_data["sheet_name"] = config.import_config.sheet_name
        if import_data:
            data["import"] = import_data

    with open(path, "wb") as f:
        tomli_w.dump(data, f)

    # Set restrictive permissions on Unix
    if sys.platform != "win32":
        os.chmod(path, 0o600)
