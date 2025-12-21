import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


def configure_logging(level: str = 'INFO', logfile: Optional[str] = 'groupalarm.log', max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5):
    """Configure root logger to log to console and a rotating file.

    - level: logging level name (e.g. 'INFO', 'DEBUG')
    - logfile: path to rotating logfile; if None, file logging is disabled
    - max_bytes, backup_count: rotation settings
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, level.upper(), logging.INFO))
    ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))

    # Remove existing stream handlers to avoid duplicate logs
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)

    root.addHandler(ch)

    # File handler (rotating)
    if logfile:
        fh = RotatingFileHandler(logfile, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
        fh.setLevel(getattr(logging, level.upper(), logging.INFO))
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))

        # Remove existing RotatingFileHandler instances to avoid duplicates
        for h in list(root.handlers):
            if isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', None) == logfile:
                root.removeHandler(h)

        root.addHandler(fh)

    return root
