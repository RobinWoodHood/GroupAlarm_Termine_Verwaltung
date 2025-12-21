import logging
import time
from typing import Optional

import requests

from .appointment import Appointment

logger = logging.getLogger(__name__)


from typing import Optional


class AppointmentNotFound(Exception):
    """Raised when an appointment id is not found on the GroupAlarm server."""


class GroupAlarmClient:
    """Client for interacting with the GroupAlarm REST API.

    The client supports creating, updating and querying appointments, and
    implements simple retry/backoff logic for transient failures. In ``dry_run``
    mode HTTP calls are skipped and payloads are logged instead.
    """

    def __init__(self, token: Optional[str], dry_run: bool = False, base_url: str = "https://app.groupalarm.com/api/v1"):
        """Create a GroupAlarmClient.

        Parameters
        ----------
        token : str or None
            Personal-Access-Token used for authenticated requests. If ``None``
            and ``dry_run`` is ``False`` some methods will raise :class:`ValueError`.
        dry_run : bool, optional
            When ``True`` API calls are not executed and payloads are only logged.
        base_url : str, optional
            Base URL for the GroupAlarm API (default: production API).
        """
        self.token = token
        self.dry_run = dry_run
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            self.headers["Personal-Access-Token"] = self.token

    def create_appointment(self, appt: Appointment, retries: int = 3, backoff: float = 1.0):
        """Create an appointment in GroupAlarm.

        Parameters
        ----------
        appt : Appointment
            The appointment object to create (will be validated via ``Appointment.validate``).
        retries : int, optional
            Number of retries for transient errors (5xx) (default: 3).
        backoff : float, optional
            Initial backoff in seconds for retries; it will be multiplied on each retry.

        Returns
        -------
        dict
            The parsed JSON response from the API (may include the created ``id``).

        Raises
        ------
        ValueError
            If a token is required but not provided (non-dry run).
        requests.RequestException
            For network or HTTP errors after exhausting retries.
        """
        payload = appt.to_api_payload()
        url = f"{self.base_url}/appointment"
        if self.dry_run:
            logger.info("DRY-RUN: would POST to %s with payload:\n%s", url, payload)
            return {"dry_run": True, "payload": payload}

        # Non-dry run: ensure we have a token
        if not self.token:
            raise ValueError("No token provided for non-dry run")

        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
                if resp.status_code in (200, 201):
                    logger.info("Appointment created: %s", resp.json())
                    return resp.json()
                # retry on 5xx
                if 500 <= resp.status_code < 600 and attempt < retries:
                    logger.warning("Server error %s, retrying in %.1fs...", resp.status_code, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                # otherwise log and raise
                logger.error("Failed to create appointment: %s %s", resp.status_code, resp.text)
                resp.raise_for_status()
            except requests.RequestException as exc:
                if attempt < retries:
                    logger.warning("Request failed: %s, retrying in %.1fs...", exc, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.exception("Failed to create appointment after %d attempts", attempt)
                raise

    def update_appointment(self, appt: Appointment, retries: int = 2, backoff: float = 1.0):
        """Update an existing appointment identified by ``appt.id``.

        Parameters
        ----------
        appt : Appointment
            The appointment to update. ``appt.id`` must be set.
        retries : int, optional
            Number of retries for transient errors (5xx) (default: 2).
        backoff : float, optional
            Initial backoff in seconds for retries; it will be multiplied on each retry.

        Returns
        -------
        dict
            The parsed JSON response from the API (may include the updated ``id``).

        Raises
        ------
        ValueError
            If ``appt.id`` is not set or token missing when required.
        AppointmentNotFound
            If the server returns a 404 for the given id.
        requests.RequestException
            For network or HTTP errors after exhausting retries.
        """
        if not getattr(appt, 'id', None):
            raise ValueError("Appointment.id is required for update")
        payload = appt.to_api_payload()
        url = f"{self.base_url}/appointment/{appt.id}"
        if self.dry_run:
            logger.info("DRY-RUN: would PUT to %s with payload:\n%s", url, payload)
            return {"dry_run": True, "payload": payload, "id": appt.id}

        if not self.token:
            raise ValueError("No token provided for non-dry run")

        for attempt in range(1, retries + 1):
            try:
                logger.debug("PUT %s payload=%s (attempt %d)", url, payload, attempt)
                resp = requests.put(url, json=payload, headers=self.headers, timeout=10)

                if resp.status_code in (200, 201):
                    logger.info("Appointment updated: %s", resp.json())
                    return resp.json()

                # Not found -> raise a specific exception so callers can handle fallback logic
                if resp.status_code == 404:
                    logger.error("Appointment %s not found (404). Response: %s", appt.id, resp.text)
                    raise AppointmentNotFound(appt.id)

                # retry on 5xx
                if 500 <= resp.status_code < 600 and attempt < retries:
                    logger.warning("Server error %s, retrying in %.1fs...", resp.status_code, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                # otherwise log and raise
                logger.error("Failed to update appointment %s: %s %s", appt.id, resp.status_code, resp.text)
                resp.raise_for_status()
            except AppointmentNotFound:
                # Re-raise without wrapping to let callers decide
                raise
            except requests.RequestException as exc:
                if attempt < retries:
                    logger.warning("Request failed: %s, retrying in %.1fs...", exc, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.exception("Failed to update appointment after %d attempts", attempt)
                raise

    def get_appointment(self, id_: int):
        """Retrieve a single appointment by id.

        Parameters
        ----------
        id_ : int
            The appointment id to fetch.

        Returns
        -------
        dict
            The appointment JSON object as returned by the API.

        Raises
        ------
        AppointmentNotFound
            If the server responds with 404.
        requests.RequestException
            For other HTTP/network errors.
        """
        url = f"{self.base_url}/appointment/{id_}"
        if self.dry_run:
            logger.info("DRY-RUN: would GET %s", url)
            return {"dry_run": True, "id": id_}

        resp = requests.get(url, headers=self.headers, timeout=10)
        if resp.status_code == 404:
            logger.error("Appointment %s not found (404). Response: %s", id_, resp.text)
            raise AppointmentNotFound(id_)
        resp.raise_for_status()
        logger.info("Fetched appointment %s", id_)
        return resp.json()

    def list_appointments(self, start: str, end: str, type_: str = "personal", organization_id: Optional[int] = None):
        """List appointments in the specified time range.

        Parameters
        ----------
        start : str
            ISO 8601 start timestamp for the range.
        end : str
            ISO 8601 end timestamp for the range.
        type_ : str, optional
            Appointment type filter (``'personal'`` or ``'organization'``).
        organization_id : int, optional
            Organization id when querying organization appointments.

        Returns
        -------
        list
            A list of appointment JSON objects.
        """
        url = f"{self.base_url}/appointments/calendar"
        params = {"start": start, "end": end, "type": type_}
        if organization_id:
            params["organization_id"] = organization_id
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()
