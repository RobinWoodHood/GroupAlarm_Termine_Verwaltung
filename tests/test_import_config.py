"""Tests for ImportConfig loading and saving in framework/config.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from framework.config import AppConfig, ImportConfig, load_config, save_config


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    return tmp_path / ".groupalarm.toml"


class TestImportConfigLoading:
    """Test load_config handling of the [import] TOML section."""

    def test_missing_import_section_returns_none(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 1\n[defaults]\n', encoding="utf-8"
        )
        cfg = load_config(config_path)
        assert cfg.import_config is None

    def test_empty_import_section_returns_empty_import_config(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 1\n[import]\n', encoding="utf-8"
        )
        cfg = load_config(config_path)
        assert cfg.import_config is not None
        assert cfg.import_config.mapping_file is None
        assert cfg.import_config.sheet_name is None

    def test_mapping_file_set(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 1\n'
            '[import]\nmapping_file = "mappings/custom.py"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.import_config is not None
        assert cfg.import_config.mapping_file == "mappings/custom.py"
        assert cfg.import_config.sheet_name is None

    def test_sheet_name_set(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 1\n'
            '[import]\nsheet_name = "Termine"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.import_config is not None
        assert cfg.import_config.mapping_file is None
        assert cfg.import_config.sheet_name == "Termine"

    def test_both_fields_set(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 1\n'
            '[import]\nmapping_file = "m.py"\nsheet_name = "Sheet2"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.import_config is not None
        assert cfg.import_config.mapping_file == "m.py"
        assert cfg.import_config.sheet_name == "Sheet2"

    def test_existing_fields_unchanged(self, config_path: Path):
        config_path.write_text(
            '[general]\norganization_id = 42\ntimezone = "UTC"\n'
            '[defaults]\ndate_range_days = 60\n'
            '[import]\nmapping_file = "x.py"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.organization_id == 42
        assert cfg.timezone == "UTC"
        assert cfg.date_range_days == 60
        assert cfg.import_config is not None


class TestImportConfigSaving:
    """Test save_config round-trip for the [import] section."""

    def test_save_without_import_config(self, config_path: Path):
        cfg = AppConfig(organization_id=1)
        save_config(cfg, config_path)
        reloaded = load_config(config_path)
        assert reloaded.import_config is None

    def test_save_with_import_config_round_trip(self, config_path: Path):
        cfg = AppConfig(
            organization_id=1,
            import_config=ImportConfig(mapping_file="my_map.py", sheet_name="Data"),
        )
        save_config(cfg, config_path)
        reloaded = load_config(config_path)
        assert reloaded.import_config is not None
        assert reloaded.import_config.mapping_file == "my_map.py"
        assert reloaded.import_config.sheet_name == "Data"

    def test_save_import_config_none_fields_omitted(self, config_path: Path):
        cfg = AppConfig(
            organization_id=1,
            import_config=ImportConfig(),  # both None
        )
        save_config(cfg, config_path)
        content = config_path.read_text(encoding="utf-8")
        # Empty ImportConfig → no [import] section written
        assert "[import]" not in content

    def test_save_import_config_partial(self, config_path: Path):
        cfg = AppConfig(
            organization_id=1,
            import_config=ImportConfig(mapping_file="test.py"),
        )
        save_config(cfg, config_path)
        reloaded = load_config(config_path)
        assert reloaded.import_config is not None
        assert reloaded.import_config.mapping_file == "test.py"
        assert reloaded.import_config.sheet_name is None


class TestImportConfigFrozen:
    """ImportConfig must be frozen (immutable)."""

    def test_frozen(self):
        ic = ImportConfig(mapping_file="test.py")
        with pytest.raises(AttributeError):
            ic.mapping_file = "other.py"  # type: ignore[misc]
