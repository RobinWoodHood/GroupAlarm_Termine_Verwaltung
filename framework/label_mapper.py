import re
from typing import Dict, Iterable, List, Union


# Default token → label mapping. Adjust or extend as needed.
DEFAULT_TOKEN_MAP: Dict[str, Union[int, Iterable[int]]] = {
    "1.TZ/ZTr TZ": 40436,
    "1.TZ/B": 40427,
    "1.TZ/FGr N": 40433,
    "1.TZ/FGr E": 40429,
    "UFB": [40428, 40431, 40434, 40435],  # multiple labels for this token
    "KF CE": 40442,
    "KF BE": 40441,
}


def map_labels_from_participants(text: str, token_map: Dict[str, Union[int, Iterable[int]]] = None) -> List[int]:
    """Map a free-text participants cell to a list of label IDs.

    Parameters
    ----------
    text : str
        Free-text participants field (may contain tokens separated by commas, semicolons or newlines).
    token_map : dict, optional
        Mapping from token strings to label id(s). Defaults to :data:`DEFAULT_TOKEN_MAP`.

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
    >>> map_labels_from_participants(s)
    [40427, 40433, 40436]
    """
    if not text:
        return []
    tm = token_map or DEFAULT_TOKEN_MAP
    txt = str(text)
    labels = set()

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
                    if isinstance(val, (list, tuple, set)):
                        labels.update(val)
                    else:
                        labels.add(val)
                    continue
            except re.error:
                # fallback to substring match if regex fails for some reason
                if token.lower() in s.lower():
                    if isinstance(val, (list, tuple, set)):
                        labels.update(val)
                    else:
                        labels.add(val)
                    continue
            # substring fallback
            if token.lower() in s.lower():
                if isinstance(val, (list, tuple, set)):
                    labels.update(val)
                else:
                    labels.add(val)
    return sorted(labels)