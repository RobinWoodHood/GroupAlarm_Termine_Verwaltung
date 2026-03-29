"""Slim Tier-2 import mapping for TUI Excel import.

Usage in .groupalarm.toml:

[import]
mapping_file = "example_import.py"
"""

from importlib import import_module
from typing import Dict, List, Union

LabelValue = Union[int, List[int]]


DEFAULT_TOKEN_MAP: Dict[str, LabelValue] = {
    "1.TZ/ZTr TZ": 40436,
    "1.TZ/B": 40427,
    "1.TZ/FGr N": 40433,
    "1.TZ/FGr E": 40429,
    "UFB": [40428, 40431, 40434, 40435],
    "KF CE": 40442,
    "KF BE": 40441,
}


def _map_labels_from_framework(text: str, token_map: Dict[str, LabelValue]) -> List[int]:
    """Delegate label mapping to framework.label_mapper at runtime."""
    label_mapper = import_module("framework.label_mapper")
    return label_mapper.map_labels_from_participants(text, token_map)

mapping = {
    "name": lambda r, helpers: f"{r['Dienstart']}",
    "description": lambda r, helpers: (
        f"Ort: {r.get('Ort')}\n"
        f"Thema: {r.get('Thema')}\n"
        f"Teilnehmer: {r.get('Teilnehmer')}\n"
        f"Bekleidung: {r.get('Bekleidung')}"
    ),
    "startDate": lambda r, helpers: helpers["parse_date"](
        r["Beginn"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"
    ),
    "endDate": lambda r, helpers: helpers["parse_date"](
        r["Ende"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin"
    ),
    "organizationID": 13915,
    "labelIDs": lambda r, helpers: _map_labels_from_framework(
        r.get("Teilnehmer"), DEFAULT_TOKEN_MAP
    ),
    "reminder": 60 * 24,
    "notificationDate": {"days_before": 5},
    "isPublic": False,
}
