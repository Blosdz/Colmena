from __future__ import annotations

import base64
import binascii


MAX_IMAGE_BYTES = 5 * 1024 * 1024
PNG_PREFIX = "data:image/png;base64,"
SVG_PREFIX = "data:image/svg+xml;base64,"


def decode_chart_data_url(data_url: str, image_format: str) -> bytes:
    prefix = PNG_PREFIX if image_format == "png" else SVG_PREFIX
    if not data_url.startswith(prefix):
        raise ValueError("Invalid data URL prefix for chart image")

    encoded = data_url[len(prefix) :]
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Invalid base64 image payload") from exc

    if not decoded:
        raise ValueError("Image payload is empty")
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ValueError("Image payload exceeds the 5 MB limit")
    return decoded
