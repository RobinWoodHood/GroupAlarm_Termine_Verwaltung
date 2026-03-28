# Contract: Client Extensions (Users API)

**Feature**: 003-tui-detail-ux-overhaul  
**Module**: `framework/client.py` — `GroupAlarmClient`

## New Method: `list_users`

Fetches all users from an organization via the Users API.

**Signature**:
```
list_users(organization_id: int) -> List[Dict[str, Any]]
```

**API Endpoint**: `GET /users?organization={organization_id}`

**Authentication**: `Personal-Access-Token` header (same token as appointment API).

**Response**: Array of user objects, each containing:
```json
{
  "id": 12345,
  "name": "Max",
  "surname": "Mustermann",
  "email": "max@example.com",
  "pending": false,
  "availableStatus": "available",
  "availablePreference": "",
  "avatarURL": "",
  "editable": true,
  "externalID": ""
}
```

**Error handling**:
- Network/HTTP errors raise `requests.RequestException`
- In `dry_run` mode, logs the call and returns an empty list

**Usage**: Called by `UserService` to populate the user cache for name resolution and type-ahead suggestions.

---

## Extended Behavior: `get_appointment`

The existing `get_appointment(id_)` method already returns the full `Appointment` schema including `participants[]`. No method change needed — the caller must parse participant data from the response dict.

**Participant fields in response**:
```json
{
  "participants": [
    {
      "userID": 12345,
      "labelID": 0,
      "feedback": 1,
      "feedbackMessage": "Bin dabei!",
      "appointmentID": 67890
    }
  ]
}
```
