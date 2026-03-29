"""Slim Tier-2 import mapping for TUI Excel import.

Usage in .groupalarm.toml:

[import]
mapping_file = "example_import.py"
sheet_name = "sheet_name_in_excel"
"""

from importlib import import_module
from typing import Dict, List, Union

LabelValue = Union[int, List[int]]


DEFAULT_TOKEN_MAP: Dict[str, LabelValue] = {
    "FF": 123,  # Example: map "FF" to label ID 123
    "ABC": [456, 789],  # Example: map "ABC" to label IDs 456 and 789
}


def _map_labels_from_framework(text: str, token_map: Dict[str, LabelValue]) -> List[int]:
    """Delegate label mapping to framework.label_mapper at runtime."""
    label_mapper = import_module("framework.label_mapper")
    return label_mapper.map_labels_from_participants(text, token_map)

mapping = {
    "name": lambda r, helpers: f"{r['Dienstart']}", # Example: use 'Dienstart' column for appointment name
    "description": lambda r, helpers: ( # Example: create description from multiple columns
        f"Ort: {r.get('Ort')}\n"
        f"Thema: {r.get('Thema')}\n"
        f"Teilnehmer: {r.get('Teilnehmer')}\n"
        f"Bekleidung: {r.get('Bekleidung')}"
    ),
    "startDate": lambda r, helpers: helpers["parse_date"](
        r["Beginn"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin" # Example: parse German datetime format from 'Beginn' column
    ),
    "endDate": lambda r, helpers: helpers["parse_date"](
        r["Ende"], fmt="%d.%m.%Y %H:%M:%S", tz="Europe/Berlin" # Example: parse German datetime format from 'Ende' column
    ),
    "organizationID": 13915,
    "labelIDs": lambda r, helpers: _map_labels_from_framework(
        r.get("Teilnehmer"), DEFAULT_TOKEN_MAP # Example: map labels based on 'Teilnehmer' column using the token map
    ),
    "reminder": 60 * 24,
    "notificationDate": {"days_before": 5},
    "isPublic": False,
}
