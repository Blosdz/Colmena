from app.services.invitation_service import generate_invitation_token, hash_invitation_token


def test_generate_invitation_token_is_unique_and_url_safe() -> None:
    tokens = {generate_invitation_token() for _ in range(50)}
    assert len(tokens) == 50


def test_hash_invitation_token_is_deterministic() -> None:
    token = generate_invitation_token()
    assert hash_invitation_token(token) == hash_invitation_token(token)


def test_hash_invitation_token_differs_for_different_tokens() -> None:
    a, b = generate_invitation_token(), generate_invitation_token()
    assert hash_invitation_token(a) != hash_invitation_token(b)
