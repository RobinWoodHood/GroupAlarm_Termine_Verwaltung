from framework.importer_token import ImporterToken


def test_create_and_find_token():
    token = ImporterToken.create_token()
    assert token.startswith('[GA-IMPORTER:')
    assert ImporterToken.find_in_text('foo\n' + token + '\nbar') == token
    assert ImporterToken.validate_token(token) is True


def test_token_format_is_short():
    token = ImporterToken.create_token()
    # inside the brackets we expect 3 parts separated by '|', and short lengths
    inner = token.strip('[]').split(':', 1)[1]
    parts = inner.split('|')
    assert len(parts[0]) == 8  # short uid
    assert len(parts[1]) == 14  # timestamp YYYYMMDDHHMMSS
    assert len(parts[2]) == 4  # 4-char checksum


def test_find_none():
    assert ImporterToken.find_in_text('no token here') is None
    assert ImporterToken.find_in_text(None) is None
