from typing import Any


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def format_missing(value: Any) -> str:
    return "" if value is None else safe_text(value)


def format_decimal(value: float | int | None, decimals: int = 3) -> str:
    if value is None:
        return ""
    return f"{float(value):.{decimals}f}"


def format_p_value(value: float | None) -> str:
    if value is None:
        return ""
    if value < 0.001:
        return "< .001"
    text = f"{float(value):.3f}"
    if text.startswith("0"):
        text = text[1:]
    return f"= {text}"


def format_percentage(value: float | int | None, decimals: int = 1) -> str:
    if value is None:
        return ""
    return f"{float(value):.{decimals}f}"


def format_statistic(value: float | int | None, decimals: int = 3) -> str:
    return format_decimal(value, decimals=decimals)


def format_n(value: int | None) -> str:
    if value is None:
        return ""
    return str(int(value))


def format_effect_size(value: float | None, decimals: int = 3) -> str:
    return format_decimal(value, decimals=decimals)
