import re
import secrets
import unicodedata


def generate_public_slug(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s-]", "", normalized)
    normalized = re.sub(r"[\s_-]+", "-", normalized).strip("-")
    normalized = normalized[:60].rstrip("-")
    if not normalized:
        normalized = "formulario"
    suffix = secrets.token_hex(3)
    return f"{normalized}-{suffix}"[:80].rstrip("-")
