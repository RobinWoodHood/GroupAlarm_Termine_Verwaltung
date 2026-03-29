from __future__ import annotations

import logging
import os


class ApiKeySanitizer(logging.Filter):
    """Logging filter that replaces the API key in log messages with '***'."""

    def __init__(self, api_key: str) -> None:
        """Initialize the ApiKeySanitizer instance."""
        super().__init__()
        self._api_key = api_key

    def filter(self, record: logging.LogRecord) -> bool:
        """Execute `filter`."""
        if self._api_key:
            if isinstance(record.msg, str) and self._api_key in record.msg:
                record.msg = record.msg.replace(self._api_key, "***")
            if record.args:
                sanitized = []
                for arg in (record.args if isinstance(record.args, tuple) else (record.args,)):
                    if isinstance(arg, str) and self._api_key in arg:
                        sanitized.append(arg.replace(self._api_key, "***"))
                    else:
                        sanitized.append(arg)
                record.args = tuple(sanitized)
        return True


def install_api_key_sanitizer(api_key: str) -> None:
    """Install the API key sanitizer on the root logger."""
    if not api_key:
        return
    sanitizer = ApiKeySanitizer(api_key)
    root = logging.getLogger()
    root.addFilter(sanitizer)
