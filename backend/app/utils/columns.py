import re
import unicodedata


def sanitize_column_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s_]", "", normalized)
    normalized = re.sub(r"[\s-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def build_fallback_column_name(sort_order: int, question_id: str) -> str:
    short_id = sanitize_column_name(question_id.replace("-", ""))[:6]
    return f"q_{sort_order}_{short_id}"
