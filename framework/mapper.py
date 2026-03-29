from __future__ import annotations
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

from .appointment import Appointment
from .utils import parse_date, relative_notification, clean_text


class Mapper:
    """Map a row (pandas.Series) to an Appointment using a mapping dict provided by the user.

    Mapping value options:
      - callable(row, helpers) -> value
      - string with `{}` placeholders -> format with row dict
      - string column name -> direct column value
      - constants (int, list, dict) depending on the field
      - special dict for notificationDate: {"days_before": 5} or {"minutes_before": 60}
    """

    def __init__(self, mapping: Dict[str, Any], defaults: Optional[Dict[str, Any]] = None):
        """Create a Mapper.

        Parameters
        ----------
        mapping : dict
            User-provided mapping specification that defines how to construct
            Appointment fields from a source row.
        defaults : dict, optional
            Default values (timezone, start/end hour, etc.) applied when
            mapping values are missing.
        """
        self.mapping = mapping
        self.defaults = defaults or {}

    def _eval(self, key: str, row) -> Any:
        """Evaluate a mapping spec for a given key using the provided row.

        Parameters
        ----------
        key : str
            The mapping key (e.g. ``'name'``, ``'labelIDs'``).
        row : pandas.Series
            The source row to extract values from.

        Returns
        -------
        Any
            The evaluated value for the mapping key.
        """
        spec = self.mapping.get(key, None)
        helpers = {
            # accept optional fmt for explicit formats like "%d.%m.%Y %H:%M"
            "parse_date": lambda v, hour=None, tz=self.defaults.get("timezone", "UTC"), fmt=None: parse_date(v, hour=hour, tz=tz, fmt=fmt),
        }

        if callable(spec):
            return spec(row, helpers)

        if isinstance(spec, str):
            if "{" in spec and "}" in spec:
                # template
                return spec.format(**row.to_dict())
            # column name
            return row.get(spec)

        if isinstance(spec, dict):
            # special handling for notificationDate relative spec
            if key == "notificationDate":
                start = self._eval("startDate", row)
                if isinstance(start, str):
                    # try to parse using defaults
                    start = helpers["parse_date"](start)
                if "days_before" in spec:
                    return relative_notification(start, days_before=int(spec["days_before"]))
                if "minutes_before" in spec:
                    return relative_notification(start, minutes_before=int(spec["minutes_before"]))
                if "column" in spec:
                    return helpers["parse_date"](row.get(spec["column"]), fmt=spec.get("format"))
            # fallback: return dict as is
            return spec

        # other (int, list, etc.)
        return spec

    def map_row(self, row) -> Appointment:
        """Map a source row into an :class:`Appointment` instance.

        Parameters
        ----------
        row : pandas.Series
            A single input row as returned by an importer.

        Returns
        -------
        Appointment
            The constructed :class:`Appointment` object ready for validation and API submission.
        """
        # required fields
        name = self._eval("name", row)
        description = self._eval("description", row)

        # clean the name by default to remove stray newlines and extra whitespace
        if name is not None and self.defaults.get("clean_name", True):
            name = clean_text(name)

        # start / end date parsing: allow column name or callable
        start_spec = self.mapping.get("startDate")
        end_spec = self.mapping.get("endDate")

        # use helpers to parse dates with optional default hours
        default_start_hour = self.defaults.get("start_hour")
        default_end_hour = self.defaults.get("end_hour")
        tz = self.defaults.get("timezone", "UTC")

        def parse_field(spec, role: str):
            """Execute `parse_field`."""
            if callable(spec):
                # provide a helper that accepts the same kwargs as in _eval (hour, fmt, tz)
                default_tz = tz
                helpers_local = {
                    "parse_date": lambda val, hour=None, fmt=None, tz=None: parse_date(val, hour=hour, tz=(tz if tz is not None else default_tz), fmt=fmt)
                }
                v = spec(row, helpers_local)
                return v
            if isinstance(spec, str):
                # column name
                raw = row.get(spec)
                hour = default_start_hour if role == "start" else default_end_hour
                return parse_date(raw, hour=hour, tz=tz)
            if isinstance(spec, dict) and "column" in spec:
                hour = spec.get("hour", default_start_hour if role == "start" else default_end_hour)
                fmt = spec.get("format")
                return parse_date(row.get(spec["column"]), hour=hour, tz=tz, fmt=fmt)
            return spec

        start = parse_field(start_spec, "start")
        end = parse_field(end_spec, "end")

        # other fields
        organizationID = self._eval("organizationID", row) or self.defaults.get("organizationID")
        labelIDs = self._eval("labelIDs", row) or self.defaults.get("labelIDs", [])
        reminder = self._eval("reminder", row) or self.defaults.get("reminder")
        notificationDate = None
        if "notificationDate" in self.mapping:
            notificationDate = self._eval("notificationDate", row)
        
        feedbackDeadline = None
        if "feedbackDeadline" in self.mapping:
            feedbackDeadline = self._eval("feedbackDeadline", row)

        isPublic = self._eval("isPublic", row)
        if isPublic is None:
            isPublic = self.defaults.get("isPublic", True)

        appt = Appointment(
            name=name,
            description=description,
            startDate=start,
            endDate=end,
            organizationID=int(organizationID),
            labelIDs=list(labelIDs) if labelIDs is not None else [],
            isPublic=bool(isPublic),
            keepLabelParticipantsInSync=True,
            reminder=int(reminder) if reminder is not None else None,
            notificationDate=notificationDate,
            feedbackDeadline=feedbackDeadline,
            timezone=self.defaults.get("timezone", "UTC"),
        )
        return appt
