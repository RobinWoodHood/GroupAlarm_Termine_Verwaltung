import logging
from typing import Any
import getpass

from .importers import ExcelImporter, CSVImporter
from .mapper import Mapper
from .client import GroupAlarmClient

logger = logging.getLogger(__name__)


from .importer_token import ImporterToken


class Runner:
    """Execute mapping + API synchronization between a tabular source and GroupAlarm.

    The Runner reads rows from an importer (CSV/Excel), maps each row into an
    :class:`Appointment` using a :class:`Mapper` and then either creates or
    updates the appointment in GroupAlarm. By default created appointments get a
    short importer token appended to their description and both the token and
    the returned ``id`` are persisted back to the source file so future runs
    can reliably update the appointment.
    """

    def __init__(self, importer: Any, mapping: dict, defaults: dict = None, dry_run: bool = True, id_column: str = 'groupalarm_id', token_column: str = 'ga_importer_token'):
        """Create a Runner instance.

        Parameters
        ----------
        importer : object
            An importer instance providing a ``rows()`` generator and optional
            ``set_value(index, column, value)`` and ``save()`` methods.
        mapping : dict
            Mapping specification passed to :class:`Mapper` to convert rows to
            :class:`Appointment` objects.
        defaults : dict, optional
            Defaults passed to the :class:`Mapper` (timezone, start/end hour, etc.).
        dry_run : bool, optional
            When ``True`` no HTTP calls are made; payloads are only logged.
        id_column : str, optional
            Column name used to read/write the GroupAlarm appointment id.
        token_column : str, optional
            Column name used to read/write the importer token (for robust lookup).
        """
        self.importer = importer
        self.mapping = mapping
        self.defaults = defaults or {}
        self.dry_run = dry_run
        self.id_column = id_column
        self.token_column = token_column
        # token helper
        self._token_helper = ImporterToken()

    def run(self, prompt_token: bool = True, token: str = None):
        """Process all rows from the importer and sync with GroupAlarm.

        For each row the method maps the row to an :class:`Appointment` and then
        decides whether to create a new appointment (no ``id`` present) or update
        an existing one (``id`` present). Created appointments get an importer
        token appended to their description; updates may add a token if missing.

        Parameters
        ----------
        prompt_token : bool, optional
            Prompt the user for a Personal-Access-Token when running in non-dry mode.
        token : str, optional
            Personal-Access-Token to use for GroupAlarm API calls. If ``None`` and
            ``prompt_token`` is ``True`` the user will be prompted; required when
            ``dry_run`` is ``False``.
        """
        # If dry_run, token is optional; if not dry_run, require it (prompt if requested).
        if not self.dry_run:
            if prompt_token and not token:
                token = getpass.getpass("Enter Personal-Access-Token: ")
            if not token:
                raise ValueError("No token provided")
        else:
            if token:
                logger.debug("Dry-run: token provided but it will only be used for non-dry runs.")

        # Always create a client object; it will accept None token and avoid sending when dry_run=True.
        client = GroupAlarmClient(token=token, dry_run=self.dry_run)
        mapper = Mapper(self.mapping, defaults=self.defaults)

        for i, row in enumerate(self.importer.rows()):
            try:
                appt = mapper.map_row(row)

                # Check for existing ID in the source row
                existing_id = None
                try:
                    existing_id = row.get(self.id_column) if row is not None else None
                except Exception:
                    existing_id = None

                if existing_id:
                    # ensure id is stored on appointment and update
                    try:
                        appt.id = int(existing_id)
                    except Exception:
                        appt.id = existing_id

                    # Determine whether a token is present; if not, we will create one and persist it after a successful update
                    token_present = False
                    try:
                        token_val = None
                        try:
                            token_val = row.get(self.token_column)
                        except Exception:
                            token_val = None
                        if token_val:
                            token_present = True
                        else:
                            # maybe token is already embedded in description
                            if self._token_helper.find_in_text(appt.description):
                                token_present = True
                    except Exception:
                        token_present = False

                    persist_token_after_update = False
                    if not token_present:
                        # create token and append to description BEFORE updating so server stores it in description
                        token = self._token_helper.create_token()
                        if appt.description:
                            appt.description = f"{appt.description}\n{token}"
                        else:
                            appt.description = token
                        persist_token_after_update = True

                    if self.dry_run:
                        logger.info("[DRY] Would update appointment id=%s for row %d: %s", appt.id, i, appt.to_api_payload())
                    else:
                        try:
                            res = client.update_appointment(appt)

                            # If server returned a (possibly new) id, persist it back to the source
                            new_id = None
                            if isinstance(res, dict) and 'id' in res:
                                new_id = res['id']
                            if new_id is not None and hasattr(self.importer, 'set_value'):
                                try:
                                    idx = row.name
                                except Exception:
                                    idx = None
                                if idx is not None:
                                    try:
                                        self.importer.set_value(idx, self.id_column, new_id)
                                        if hasattr(self.importer, 'save'):
                                            self.importer.save()
                                        logger.info("Updated id for row %s: %s -> %s", idx, appt.id, new_id)
                                    except Exception as exc:
                                        logger.exception("Failed to write updated id back to source for row %s: %s", idx, exc)

                            # If we created a token, persist it now to the source as well
                            if persist_token_after_update and hasattr(self.importer, 'set_value'):
                                try:
                                    idx = row.name
                                except Exception:
                                    idx = None
                                if idx is not None:
                                    try:
                                        self.importer.set_value(idx, self.token_column, token)
                                        if hasattr(self.importer, 'save'):
                                            self.importer.save()
                                        logger.info("Wrote importer token to column '%s' for row %s", self.token_column, idx)
                                    except Exception as exc:
                                        logger.exception("Failed to write token back to source for row %s: %s", idx, exc)

                        except Exception as exc:
                            # Try token-based lookup on not-found
                            from .client import AppointmentNotFound
                            if isinstance(exc, AppointmentNotFound):
                                try:
                                    token = None
                                    try:
                                        token = row.get(self.token_column)
                                    except Exception:
                                        token = None

                                    if not token:
                                        # maybe token is embedded in description
                                        token = self._token_helper.find_in_text(appt.description)

                                    if token:
                                        # search using calendar list in the time window
                                        logger.info("Attempting to find appointment by token %s for row %s", token, i)
                                        try:
                                            start = appt.startDate.astimezone().isoformat()
                                            end = appt.endDate.astimezone().isoformat()
                                        except Exception:
                                            start = None
                                            end = None

                                        if start is not None and end is not None:
                                            try:
                                                cand = client.list_appointments(start, end, type_='personal', organization_id=appt.organizationID)
                                                found = None
                                                for item in cand:
                                                    desc = item.get('description') or ''
                                                    if token in desc:
                                                        found = item
                                                        break

                                                if found:
                                                    new_id = found.get('id')
                                                    logger.info("Found appointment by token: id=%s", new_id)
                                                    appt.id = new_id
                                                    # try update again
                                                    res2 = client.update_appointment(appt)
                                                    # persist updated id if returned
                                                    if isinstance(res2, dict) and 'id' in res2 and hasattr(self.importer, 'set_value'):
                                                        try:
                                                            idx = row.name
                                                        except Exception:
                                                            idx = None
                                                        if idx is not None:
                                                            self.importer.set_value(idx, self.id_column, res2['id'])
                                                            if hasattr(self.importer, 'save'):
                                                                self.importer.save()
                                                            logger.info("Wrote new id %s to column '%s' for row %s after token lookup", res2['id'], self.id_column, idx)
                                                    continue
                                            except Exception as exc2:
                                                logger.exception("Failed to list/search appointments for token lookup: %s", exc2)
                                    # re-raise if no token or unsuccessful
                                except Exception:
                                    logger.exception("Token lookup failed for row %s", i)
                                raise
                            else:
                                logger.exception("Failed to update appointment id=%s for row %d: %s", appt.id, i, exc)
                else:
                    if self.dry_run:
                        logger.info("[DRY] Prepared payload for row %d: %s", i, appt.to_api_payload())
                    else:
                        # Before creating, generate an importer token and append it to description
                        token = self._token_helper.create_token()
                        if appt.description:
                            appt.description = f"{appt.description}\n{token}"
                        else:
                            appt.description = token

                        # client is created regardless; when not dry-run token must be present
                        res = client.create_appointment(appt)

                        # If server returned an id, persist it back to the source (if importer supports it)
                        try:
                            new_id = None
                            if isinstance(res, dict) and 'id' in res:
                                new_id = res['id']
                            if new_id is not None and hasattr(self.importer, 'set_value'):
                                # row.name is the original dataframe index from pandas.iterrows
                                try:
                                    idx = row.name
                                except Exception:
                                    idx = None
                                if idx is not None:
                                    try:
                                        self.importer.set_value(idx, self.id_column, new_id)
                                        # persist token as well
                                        self.importer.set_value(idx, self.token_column, token)
                                        if hasattr(self.importer, 'save'):
                                            self.importer.save()
                                        logger.info("Wrote new id %s and token to columns '%s','%s' for row %s", new_id, self.id_column, self.token_column, idx)
                                    except Exception as exc:
                                        logger.exception("Failed to write id/token back to source for row %s: %s", idx, exc)
                        except Exception:
                            logger.exception("Failed to persist created appointment id for row %d", i)
            except Exception as exc:
                logger.exception("Failed to process row %d: %s", i, exc)
