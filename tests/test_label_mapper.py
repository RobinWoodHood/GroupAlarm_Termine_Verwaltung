from framework.label_mapper import map_labels_from_participants, DEFAULT_TOKEN_MAP


def test_map_labels_simple():
    s = "1.TZ/ZTr TZ"
    assert map_labels_from_participants(s, DEFAULT_TOKEN_MAP) == [40436]


def test_map_labels_multiple_and_duplicates():
    s = "1.TZ/B\n1.TZ/FGr N\n1.TZ/ZTr TZ TZ\n1.TZ/FGr"
    labels = map_labels_from_participants(s, DEFAULT_TOKEN_MAP)
    assert labels == [40427, 40433, 40436]


def test_map_labels_case_insensitive_and_substring():
    s = "1.tz/ztr tz"
    assert map_labels_from_participants(s, DEFAULT_TOKEN_MAP) == [40436]


def test_map_labels_empty_returns_empty():
    assert map_labels_from_participants(None, DEFAULT_TOKEN_MAP) == []
    assert map_labels_from_participants("", DEFAULT_TOKEN_MAP) == []
