# Contract: User Service

**Feature**: 003-tui-detail-ux-overhaul  
**Module**: `cli/services/user_service.py` (new)

## Purpose

Provides a cached user directory for:
1. Resolving participant user IDs to display names
2. Supplying type-ahead suggestions for the participants field

## Interface

### `UserService.__init__(client, organization_id)`

Initialize with a `GroupAlarmClient` and the organization ID.

### `UserService.load()`

Fetch all organization users via `client.list_users(organization_id)` and build internal lookup structures. Should be called once on app startup (after label service loads).

### `UserService.get_display_name(user_id: int) -> str`

Returns `"Name Surname"` for the given user ID. Falls back to `"User #{user_id}"` if the user is not in the cache.

### `UserService.get_user_id_by_display_name(display_name: str) -> int | None`

Reverse lookup: given a display name string, returns the user ID or None if not found. Used when parsing the participants input field.

### `UserService.get_all_display_names() -> list[str]`

Returns a sorted list of all `"Name Surname"` strings for building the type-ahead suggestion list.

### `UserService.get_directory() -> list[dict]`

Returns the raw user list for other consumers (e.g., building enriched participant displays).

## Caching Behavior

- Users are loaded once per app session (on `load()`)
- No automatic refresh (org members rarely change during a session)
- If `load()` fails (network error), an empty cache is used and a warning is shown

## Error Handling

- `load()` catches `requests.RequestException` and logs a warning
- All lookup methods return fallback values on cache miss (never raise)
