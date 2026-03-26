from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import tomli_w


@dataclass
class AppConfig:
    organization_id: Optional[int] = None
    timezone: str = "Europe/Berlin"
    date_range_days: int = 30
    default_label_ids: List[int] = field(default_factory=list)
    default_appointment_duration_hours: int = 4


def load_config(path: Path = Path(".groupalarm.toml")) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {path}: {exc}") from exc

    general = data.get("general", {})
    defaults = data.get("defaults", {})

    return AppConfig(
        organization_id=general.get("organization_id"),
        timezone=general.get("timezone", "Europe/Berlin"),
        date_range_days=defaults.get("date_range_days", 30),
        default_label_ids=defaults.get("label_ids", []),
        default_appointment_duration_hours=defaults.get("appointment_duration_hours", 4),
    )


def save_config(config: AppConfig, path: Path = Path(".groupalarm.toml")) -> None:
    data = {
        "general": {
            "organization_id": config.organization_id,
            "timezone": config.timezone,
        },
        "defaults": {
            "date_range_days": config.date_range_days,
            "label_ids": config.default_label_ids,
            "appointment_duration_hours": config.default_appointment_duration_hours,
        },
    }
    # Remove None values from general section
    data["general"] = {k: v for k, v in data["general"].items() if v is not None}

    with open(path, "wb") as f:
        tomli_w.dump(data, f)

    # Set restrictive permissions on Unix
    if sys.platform != "win32":
        os.chmod(path, 0o600)
