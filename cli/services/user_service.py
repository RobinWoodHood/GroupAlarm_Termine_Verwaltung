"""User service — fetches and caches organization users for name resolution and type-ahead."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UserService:
    """Fetch org users once and provide display-name lookups."""

    def __init__(self, client: Any, organization_id: int) -> None:
        self._client = client
        self._organization_id = organization_id
        self._users: List[Dict[str, Any]] = []
        self._by_id: Dict[int, Dict[str, Any]] = {}
        self._by_display_name: Dict[str, int] = {}

    def load(self) -> None:
        try:
            self._users = self._client.list_users(self._organization_id)
        except Exception:
            logger.warning("Failed to load users for org %d — using empty cache", self._organization_id)
            self._users = []
        self._by_id = {u["id"]: u for u in self._users}
        self._by_display_name = {
            self._format_display_name(u): u["id"] for u in self._users
        }
        logger.info("Loaded %d users for org %d", len(self._users), self._organization_id)

    @staticmethod
    def _format_display_name(user: Dict[str, Any]) -> str:
        name = user.get("name", "")
        surname = user.get("surname", "")
        return f"{name} {surname}".strip() or f"User #{user.get('id', '?')}"

    def get_display_name(self, user_id: int) -> str:
        user = self._by_id.get(user_id)
        if user is None:
            return f"User #{user_id}"
        return self._format_display_name(user)

    def get_user_id_by_display_name(self, display_name: str) -> Optional[int]:
        return self._by_display_name.get(display_name.strip())

    def get_all_display_names(self) -> List[str]:
        return sorted(self._by_display_name.keys())

    def get_directory(self) -> List[Dict[str, Any]]:
        return list(self._users)
