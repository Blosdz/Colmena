from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def export_chart_specs_json(*, exports_dir: Path, form_id: str, payload: dict[str, Any]) -> tuple[str, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"form_{form_id}_charts_{timestamp}.json"
    file_path = exports_dir / file_name
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_name, file_path
