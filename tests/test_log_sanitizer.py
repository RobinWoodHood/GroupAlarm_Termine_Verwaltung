"""Tests for API key log sanitizer."""
import logging
from framework.log_sanitizer import ApiKeySanitizer, install_api_key_sanitizer


def test_sanitizer_replaces_key_in_message():
    filt = ApiKeySanitizer("my-secret-key-123")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Token is my-secret-key-123 here", args=(), exc_info=None,
    )
    filt.filter(record)
    assert "my-secret-key-123" not in record.msg
    assert "***" in record.msg


def test_sanitizer_replaces_key_in_args():
    filt = ApiKeySanitizer("secret")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Header: %s", args=("Personal-Access-Token: secret",), exc_info=None,
    )
    filt.filter(record)
    assert "secret" not in str(record.args)
    assert "***" in str(record.args)


def test_sanitizer_passes_through_clean_messages():
    filt = ApiKeySanitizer("secret")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Normal log message", args=(), exc_info=None,
    )
    result = filt.filter(record)
    assert result is True
    assert record.msg == "Normal log message"


def test_install_adds_filter_to_root_logger():
    root = logging.getLogger()
    original_count = len(root.filters)
    install_api_key_sanitizer("test-key")
    assert len(root.filters) == original_count + 1
    # Clean up
    root.filters = root.filters[:original_count]


def test_install_with_empty_key_does_nothing():
    root = logging.getLogger()
    original_count = len(root.filters)
    install_api_key_sanitizer("")
    assert len(root.filters) == original_count
