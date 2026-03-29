from framework.label_mapper import map_labels_from_participants


TEST_TOKEN_MAP = {
    "1.TZ/ZTr TZ": 40436,
    "1.TZ/B": 40427,
    "1.TZ/FGr N": 40433,
    "1.TZ/FGr E": 40429,
    "UFB": [40428, 40431, 40434, 40435],
    "KF CE": 40442,
    "KF BE": 40441,
}


def test_map_labels_simple():
    """Test `map_labels_simple` behavior."""
    s = "1.TZ/ZTr TZ"
    assert map_labels_from_participants(s, TEST_TOKEN_MAP) == [40436]


def test_map_labels_multiple_and_duplicates():
    """Test `map_labels_multiple_and_duplicates` behavior."""
    s = "1.TZ/B\n1.TZ/FGr N\n1.TZ/ZTr TZ TZ\n1.TZ/FGr"
    labels = map_labels_from_participants(s, TEST_TOKEN_MAP)
    assert labels == [40427, 40433, 40436]


def test_map_labels_case_insensitive_and_substring():
    """Test `map_labels_case_insensitive_and_substring` behavior."""
    s = "1.tz/ztr tz"
    assert map_labels_from_participants(s, TEST_TOKEN_MAP) == [40436]


def test_map_labels_empty_returns_empty():
    """Test `map_labels_empty_returns_empty` behavior."""
    assert map_labels_from_participants(None, TEST_TOKEN_MAP) == []
    assert map_labels_from_participants("", TEST_TOKEN_MAP) == []
