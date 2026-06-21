from __future__ import annotations

import re
from pathlib import Path


_SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_file_name(file_name: str, *, fallback: str) -> str:
    cleaned = _SAFE_FILENAME_PATTERN.sub("_", file_name.strip())
    cleaned = cleaned.strip("._")
    return cleaned or fallback


def ensure_path_within(base_dir: Path, target_path: Path) -> Path:
    resolved_base = base_dir.resolve()
    resolved_target = target_path.resolve()
    if resolved_base not in resolved_target.parents and resolved_target != resolved_base:
        raise ValueError("Target path is outside the allowed export directory")
    return resolved_target
