# Contract: Config Module

**Scope**: New module `framework/config.py` — read/write `.groupalarm.toml`

## AppConfig dataclass

**Signature**:
```python
@dataclass
class AppConfig:
    organization_id: Optional[int] = None
    timezone: str = "Europe/Berlin"
    date_range_days: int = 30
    default_label_ids: List[int] = field(default_factory=list)
    default_appointment_duration_hours: int = 4
```

---

## load_config

Reads configuration from a TOML file.

**Signature**:
```python
def load_config(path: Path = Path(".groupalarm.toml")) -> AppConfig:
```

**Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| path | Path | `.groupalarm.toml` | Path to TOML config file |

**Returns**: `AppConfig` populated from file. Missing fields use dataclass defaults.

**Behavior**:
- If file does not exist → returns `AppConfig()` with all defaults (`organization_id=None`)
- If file exists but has invalid TOML → raises `ValueError` with descriptive message
- Unknown keys are silently ignored (forward compatibility)

---

## save_config

Writes configuration to a TOML file.

**Signature**:
```python
def save_config(config: AppConfig, path: Path = Path(".groupalarm.toml")) -> None:
```

**Parameters**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| config | AppConfig | — | Configuration to persist |
| path | Path | `.groupalarm.toml` | Path to TOML config file |

**Behavior**:
- Creates the file if it does not exist
- Overwrites the file completely (no merge)
- Produces valid TOML matching the schema defined in data-model.md
