"""Tests for config module — load/save .groupalarm.toml."""
import pytest
from pathlib import Path
from framework.config import AppConfig, load_config, save_config


def test_load_missing_file_returns_defaults(tmp_path):
    """Test `load_missing_file_returns_defaults` behavior."""
    config = load_config(tmp_path / "nonexistent.toml")
    assert config.organization_id is None
    assert config.timezone == "Europe/Berlin"
    assert config.show_startup_welcome is True
    assert config.date_range_days == 30
    assert config.default_label_ids == []
    assert config.default_appointment_duration_hours == 4


def test_load_valid_toml(tmp_path):
    """Test `load_valid_toml` behavior."""
    toml_path = tmp_path / ".groupalarm.toml"
    toml_path.write_text(
        '[general]\norganization_id = 999\ntimezone = "UTC"\nshow_startup_welcome = false\n\n'
        "[defaults]\ndate_range_days = 7\nlabel_ids = [1, 2]\n"
        "appointment_duration_hours = 8\n",
        encoding="utf-8",
    )
    config = load_config(toml_path)
    assert config.organization_id == 999
    assert config.timezone == "UTC"
    assert config.show_startup_welcome is False
    assert config.date_range_days == 7
    assert config.default_label_ids == [1, 2]
    assert config.default_appointment_duration_hours == 8


def test_load_invalid_toml_raises(tmp_path):
    """Test `load_invalid_toml_raises` behavior."""
    toml_path = tmp_path / "bad.toml"
    toml_path.write_text("this is not valid toml [[[", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid TOML"):
        load_config(toml_path)


def test_save_and_reload_roundtrip(tmp_path):
    """Test `save_and_reload_roundtrip` behavior."""
    toml_path = tmp_path / ".groupalarm.toml"
    config = AppConfig(
        organization_id=123,
        timezone="America/New_York",
        show_startup_welcome=False,
        date_range_days=14,
        default_label_ids=[10, 20],
        default_appointment_duration_hours=2,
    )
    save_config(config, toml_path)
    loaded = load_config(toml_path)
    assert loaded.organization_id == 123
    assert loaded.timezone == "America/New_York"
    assert loaded.show_startup_welcome is False
    assert loaded.date_range_days == 14
    assert loaded.default_label_ids == [10, 20]
    assert loaded.default_appointment_duration_hours == 2


def test_organization_id_none_when_missing(tmp_path):
    """Test `organization_id_none_when_missing` behavior."""
    toml_path = tmp_path / ".groupalarm.toml"
    toml_path.write_text('[general]\ntimezone = "UTC"\n', encoding="utf-8")
    config = load_config(toml_path)
    assert config.organization_id is None


def test_unknown_keys_ignored(tmp_path):
    """Test `unknown_keys_ignored` behavior."""
    toml_path = tmp_path / ".groupalarm.toml"
    toml_path.write_text(
        '[general]\norganization_id = 1\nfuture_key = "hello"\n',
        encoding="utf-8",
    )
    config = load_config(toml_path)
    assert config.organization_id == 1
