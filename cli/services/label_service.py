"""Label service — fetches and caches labels for the TUI session."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from cli.widgets.state import LabelReference

logger = logging.getLogger(__name__)


class LabelService:
    """Fetch labels from the API once and provide lookup by ID."""

    def __init__(self, client: Any, organization_id: int) -> None:
        """Initialize the LabelService instance."""
        self._client = client
        self._organization_id = organization_id
        self._labels: List[Dict[str, Any]] = []
        self._by_id: Dict[int, Dict[str, Any]] = {}

    def load(self) -> None:
        """Execute `load`."""
        self._labels = self._client.list_labels(self._organization_id)
        self._by_id = {label["id"]: label for label in self._labels}
        logger.info("Loaded %d labels for org %d", len(self._labels), self._organization_id)

    @property
    def labels(self) -> List[Dict[str, Any]]:
        """Execute `labels`."""
        return list(self._labels)

    def get_by_id(self, label_id: int) -> Optional[Dict[str, Any]]:
        """Execute `get_by_id`."""
        return self._by_id.get(label_id)

    def get_name(self, label_id: int) -> str:
        """Execute `get_name`."""
        label = self._by_id.get(label_id)
        return label["name"] if label else str(label_id)

    def get_color(self, label_id: int) -> str:
        """Execute `get_color`."""
        label = self._by_id.get(label_id)
        return label.get("color", "#FFFFFF") if label else "#FFFFFF"

    def get_names_for_ids(self, label_ids: List[int]) -> str:
        """Execute `get_names_for_ids`."""
        return ", ".join(self.get_name(lid) for lid in label_ids)

    def get_directory(self) -> List[LabelReference]:
        """Return rich label references for filters/autocomplete."""

        return [
            LabelReference(
                id=label["id"],
                name=label["name"],
                color=label.get("color"),
                assigned_count=label.get("assigned_count", 0),
            )
            for label in self._labels
        ]
