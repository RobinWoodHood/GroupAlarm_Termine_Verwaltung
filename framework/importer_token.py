from __future__ import annotations
import hashlib
import uuid
from datetime import datetime, timezone
import re
from typing import Optional

TOKEN_PREFIX = "GA-IMPORTER"
# Short token: [GA-IMPORTER:8hex|YYYYMMDDHHMMSS|4hex]
TOKEN_RE = re.compile(r"\[GA-IMPORTER:([0-9a-fA-F]{8})\|([0-9]{14})\|([0-9a-fA-F]{4})\]")


class ImporterToken:
    """Generate and validate compact importer tokens embedded in appointment descriptions.

    Token format: [GA-IMPORTER:<shortid>|<ts>|<chk4>]
    - shortid: first 8 hex chars of UUID4
    - ts: UTC timestamp YYYYMMDDHHMMSS (14 digits)
    - chk4: first 4 hex chars of sha1(shortid + ts)
    """

    @staticmethod
    def create_token() -> str:
        """Create a compact importer token.

        Returns
        -------
        str
            Token string in the format ``[GA-IMPORTER:shortid|YYYYMMDDHHMMSS|chk]``.
        """
        short_uid = uuid.uuid4().hex[:8]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        chk = hashlib.sha1((short_uid + ts).encode('utf-8')).hexdigest()[:4]
        return f"[{TOKEN_PREFIX}:{short_uid}|{ts}|{chk}]"

    @staticmethod
    def find_in_text(text: Optional[str]) -> Optional[str]:
        """Search for a token inside free text and return the token if found.

        Parameters
        ----------
        text : str or None
            Text to scan for a token.

        Returns
        -------
        str or None
            The token string if found, otherwise ``None``.
        """
        if not text:
            return None
        m = TOKEN_RE.search(text)
        if not m:
            return None
        return m.group(0)

    @staticmethod
    def strip_from_text(text: Optional[str]) -> tuple[str, Optional[str]]:
        """Remove a GA-IMPORTER token from *text* and return the clean text plus the token.

        Returns
        -------
        tuple[str, str | None]
            ``(clean_text, token)`` — *token* is ``None`` when no token was found.
        """
        if not text:
            return (text or "", None)
        m = TOKEN_RE.search(text)
        if not m:
            return (text, None)
        token = m.group(0)
        clean = text[:m.start()] + text[m.end():]
        # Remove trailing/leading whitespace and blank lines left by removal
        clean = clean.strip()
        return (clean, token)

    @staticmethod
    def validate_token(token: str) -> bool:
        """Validate token checksum.

        Parameters
        ----------
        token : str
            Token string to validate.

        Returns
        -------
        bool
            ``True`` if checksum matches, otherwise ``False``.
        """
        m = TOKEN_RE.match(token)
        if not m:
            return False
        short_uid, ts, chk = m.group(1), m.group(2), m.group(3)
        expected = hashlib.sha1((short_uid + ts).encode('utf-8')).hexdigest()[:4]
        return expected == chk
