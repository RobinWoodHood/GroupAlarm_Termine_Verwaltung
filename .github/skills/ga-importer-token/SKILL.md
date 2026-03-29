---
name: ga-importer-token
description: 'Use for GA or GI Importer Token work: token generation, token-first update matching, duplicate prevention, manual create token injection, import upload behavior, and related tests.'
argument-hint: 'Describe the token workflow change and affected create/update paths.'
---

# GA Importer Token Workflow

## Goal
Keep appointment identity stable across imports by using the GA-IMPORTER token as the primary matching key.

## Use This Skill When
- A request mentions GA-IMPORTER, GI importer token, importer hash, token matching, or duplicate prevention.
- You change import upload behavior in `cli/services/import_service.py`.
- You change manual appointment creation in `cli/services/appointment_service.py`.
- You change token extraction or generation in `framework/importer_token.py`.

## Source of Truth
- Token helper: `framework/importer_token.py`
- Import upload orchestration: `cli/services/import_service.py`
- Manual create flow: `cli/services/appointment_service.py`
- Behavioral tests: `tests/test_import_service.py`, `tests/test_appointment_service.py`

## Non-Negotiable Rules
1. Every newly created appointment must have exactly one GA-IMPORTER token in description.
2. Imported updates must resolve target appointment by token, not by incoming appointment id.
3. If token lookup returns no match, fail that row and do not create a fallback duplicate.
4. If token lookup returns multiple matches, fail that row as ambiguous.
5. If an appointment has an id but no token, fail safely for update paths.
6. Keep token format compatible with `ImporterToken.TOKEN_RE`:
   `[GA-IMPORTER:8hex|YYYYMMDDHHMMSS|4hex]`

## Standard Procedure
1. Parse and preserve token:
   - Use `ImporterToken.find_in_text(description)`.
   - Use `ImporterToken.ensure_token(appointment)` before any create call.
2. Update path in import upload:
   - Build lookup window from appointment start/end.
   - Call `client.list_appointments(start, end, type_="personal", organization_id=...)`.
   - Match candidates by token in server description.
   - Update only when exactly one match is found.
3. Create path:
   - Ensure token first.
   - Call `client.create_appointment(...)`.
4. Error handling:
   - Record failed result with clear reason.
   - Never silently downgrade a failed update into create.
5. Logging:
   - Log token-resolution intent, match counts, and failure reasons.
   - Keep logs operational and concise.

## Validation Checklist
- `tests/test_import_service.py` covers:
  - create with token injection,
  - token-first update resolution,
  - no-match and ambiguous-match failures,
  - id-without-token safe failure,
  - dry-run behavior.
- `tests/test_appointment_service.py` covers:
  - manual create adds token,
  - existing token is preserved without duplication.

## Quick Validation Commands
- `python -m pytest -q tests/test_import_service.py tests/test_appointment_service.py`
- `python -m pytest -q`

## Common Mistakes To Avoid
- Reintroducing id-first update behavior.
- Adding a create fallback when token-based update cannot be resolved.
- Appending additional tokens when one already exists.
- Changing token format or regex without updating all dependent tests.
