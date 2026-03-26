# Contract: GroupAlarmClient Extensions

**Scope**: New methods added to `framework/client.py` — `GroupAlarmClient`

## delete_appointment

Deletes an appointment by ID, with recurrence strategy support.

**Signature**:
```python
def delete_appointment(
    self,
    id_: int,
    strategy: str = "all",
    time: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> None:
```

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| id_ | int | Yes | — | Appointment ID to delete |
| strategy | str | No | "all" | Recurrence strategy: "single", "upcoming", or "all" |
| time | Optional[str] | No | None | ISO 8601 datetime; required when strategy is "single" or "upcoming" for recurring appointments |
| retries | int | No | 2 | Number of retries for 5xx errors |
| backoff | float | No | 1.0 | Initial backoff seconds (doubles on retry) |

**Returns**: `None` (success is 200 with no body)

**Raises**:
| Exception | Condition |
|-----------|-----------|
| ValueError | Token not provided (non-dry-run) |
| ValueError | Invalid strategy value |
| AppointmentNotFound | API returns 404 |
| requests.RequestException | Network or HTTP error after retries |

**API Mapping**:
- Method: `DELETE`
- URL: `{base_url}/appointment/{id_}`
- Query params: `strategy={strategy}`, `time={time}` (if provided)
- Headers: `Personal-Access-Token: {token}`, `Content-Type: application/json`
- Success: HTTP 200

**Dry-run behavior**: Logs `"DRY-RUN: would DELETE {url} with strategy={strategy}"` and returns `None`.

---

## list_labels

Fetches available labels for a given organization.

**Signature**:
```python
def list_labels(
    self,
    organization_id: int,
    label_type: str = "normal",
) -> List[Dict[str, Any]]:
```

**Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| organization_id | int | Yes | — | Organization to fetch labels for |
| label_type | str | No | "normal" | Type filter: "normal", "smart", or "all" |

**Returns**: `List[Dict]` — list of label objects with at minimum `{ id, name, color, organizationID }`.

**Raises**:
| Exception | Condition |
|-----------|-----------|
| requests.RequestException | Network or HTTP error |

**API Mapping**:
- Method: `GET`
- URL: `{base_url}/labels`
- Query params: `organization={organization_id}`, `all=true`, `type={label_type}`
- Headers: `Personal-Access-Token: {token}`
- Response: `LabelList` → `{ labels: Label[], total: int }` — return the `labels` array directly

**Note**: Uses `all=true` to bypass pagination (max 50 per page). The `/labels` endpoint takes the organization ID directly, unlike `/label/organizations` which groups by org.

---

## update_appointment (strategy extension)

Extends the existing `update_appointment` method to accept an optional `strategy` parameter for recurring appointments.

**Signature change**:
```python
def update_appointment(
    self,
    appt: Appointment,
    strategy: str = "all",       # NEW parameter
    retries: int = 2,
    backoff: float = 1.0,
) -> dict:
```

**New Parameter**:
| Name | Type | Default | Description |
|------|------|---------|-------------|
| strategy | str | "all" | Recurrence strategy: "single", "upcoming", or "all" |

**API Mapping Change**: Adds `?strategy={strategy}` query param to the PUT URL.
