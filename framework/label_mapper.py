import re
from typing import Dict, Iterable, List


def map_labels_from_participants(text: str, token_map: Dict[str, int | Iterable[int]]) -> List[int]:
    """Map a free-text participants cell to a list of label IDs.

    Parameters
    ----------
    text : str
        Free-text participants field (may contain tokens separated by commas, semicolons or newlines).
    token_map : dict
        Mapping from token strings to label id(s).

    Returns
    -------
    list of int
        Sorted unique label IDs that matched tokens found in ``text``.

    Notes
    -----
    Matching is case-insensitive. The function first attempts a word-boundary regex
    search and falls back to a substring match if necessary.

    Examples
    --------
    >>> s = "1.TZ/B\n1.TZ/FGr N\n1.TZ/ZTr TZ TZ"
    >>> map_labels_from_participants(s, {"1.TZ/B": 40427, "1.TZ/FGr N": 40433, "1.TZ/ZTr TZ": 40436})
    [40427, 40433, 40436]
    """
    if not text:
        return []
    tm = token_map
    txt = str(text)
    labels: set[int] = set()

    # Normalize: split into candidate tokens
    parts = re.split(r"[,;\n]+", txt)

    for part in parts:
        s = part.strip()
        if not s:
            continue
        for token, val in tm.items():
            # case-insensitive word boundary search
            try:
                if re.search(r"\b" + re.escape(token) + r"\b", s, flags=re.IGNORECASE):
                    if isinstance(val, int):
                        labels.add(val)
                    else:
                        labels.update(int(v) for v in val)
                    continue
            except re.error:
                # fallback to substring match if regex fails for some reason
                if token.lower() in s.lower():
                    if isinstance(val, int):
                        labels.add(val)
                    else:
                        labels.update(int(v) for v in val)
                    continue
            # substring fallback
            if token.lower() in s.lower():
                if isinstance(val, int):
                    labels.add(val)
                else:
                    labels.update(int(v) for v in val)
    return sorted(labels)