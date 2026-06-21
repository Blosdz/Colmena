from __future__ import annotations

from typing import Any


def compare_value(value: float | int | None, threshold: float | None, operator: str | None) -> bool:
    if value is None or threshold is None or operator is None:
        return False
    numeric = float(value)
    threshold_value = float(threshold)
    if operator == "gt":
        return numeric > threshold_value
    if operator == "gte":
        return numeric >= threshold_value
    if operator == "lt":
        return numeric < threshold_value
    if operator == "lte":
        return numeric <= threshold_value
    if operator == "eq":
        return numeric == threshold_value
    return False


def evaluate_sum_threshold(values: list[float], threshold: float | None, operator: str | None) -> tuple[float, bool]:
    score = float(sum(values)) if values else 0.0
    return score, compare_value(score, threshold, operator)


def evaluate_mean_threshold(values: list[float], threshold: float | None, operator: str | None) -> tuple[float | None, bool]:
    if not values:
        return None, False
    score = float(sum(values) / len(values))
    return score, compare_value(score, threshold, operator)


def evaluate_any_failed(failed_items: int) -> tuple[float, bool]:
    return float(failed_items), failed_items > 0


def evaluate_count_failed(failed_items: int, threshold: float | None, operator: str | None) -> tuple[float, bool]:
    return float(failed_items), compare_value(failed_items, threshold, operator)


def evaluate_paired_inconsistency(pair_scores: dict[str, list[float]]) -> tuple[float, bool, dict[str, Any]]:
    inconsistent_pairs: dict[str, dict[str, Any]] = {}
    failed_count = 0
    for pair_group, values in pair_scores.items():
        if len(values) < 2:
            continue
        if len(set(round(value, 6) for value in values)) > 1:
            inconsistent_pairs[pair_group] = {"values": values}
            failed_count += 1
    return float(failed_count), failed_count > 0, {"pairs": inconsistent_pairs}


def _answer_matches_expected(item: Any, answer: Any) -> bool:
    if answer is None:
        return False
    expected_option_id = getattr(item, "expected_option_id", None)
    expected_value_text = getattr(item, "expected_value_text", None)
    expected_value_number = getattr(item, "expected_value_number", None)
    if expected_option_id and getattr(answer, "option_id", None) == expected_option_id:
        return True
    if expected_value_text is not None and getattr(answer, "value_text", None) == expected_value_text:
        return True
    if expected_value_number is not None:
        answer_number = getattr(answer, "value_number", None)
        if answer_number is not None and float(answer_number) == float(expected_value_number):
            return True
    return False


def _answer_numeric_value(answer: Any) -> float | None:
    if answer is None:
        return None
    score_value = getattr(answer, "score_value", None)
    if score_value is not None:
        return float(score_value)
    value_number = getattr(answer, "value_number", None)
    if value_number is not None:
        return float(value_number)
    return None


def evaluate_control_scale(response: Any, control_scale: Any, answers: dict[str, Any]) -> dict[str, Any]:
    active_items = [item for item in getattr(control_scale, "items", []) if getattr(item, "deleted_at", None) is None]
    failed_items = 0
    numeric_values: list[float] = []
    pair_scores: dict[str, list[float]] = {}
    item_details: list[dict[str, Any]] = []

    for item in active_items:
        answer = answers.get(item.question_id)
        matched = _answer_matches_expected(item, answer)
        failed = False
        if answer is None:
            failed = False
        elif item.fail_if_selected:
            failed = matched
        elif any(
            value is not None
            for value in (getattr(item, "expected_option_id", None), getattr(item, "expected_value_text", None), getattr(item, "expected_value_number", None))
        ):
            failed = not matched

        numeric_value = _answer_numeric_value(answer)
        if numeric_value is not None:
            weighted_value = numeric_value * float(getattr(item, "weight", 1.0) or 1.0)
            numeric_values.append(weighted_value)
            if getattr(item, "pair_group", None):
                pair_scores.setdefault(item.pair_group, []).append(weighted_value)
        if failed:
            failed_items += 1
        item_details.append(
            {
                "question_id": item.question_id,
                "failed": failed,
                "matched_expected": matched,
                "numeric_value": numeric_value,
                "pair_group": getattr(item, "pair_group", None),
            }
        )

    rule_type = getattr(control_scale, "rule_type", "any_failed")
    if rule_type == "sum_threshold":
        score, triggered = evaluate_sum_threshold(numeric_values, getattr(control_scale, "threshold", None), getattr(control_scale, "comparison_operator", None))
        details = {"items": item_details}
    elif rule_type == "mean_threshold":
        score, triggered = evaluate_mean_threshold(numeric_values, getattr(control_scale, "threshold", None), getattr(control_scale, "comparison_operator", None))
        details = {"items": item_details}
    elif rule_type == "count_failed":
        score, triggered = evaluate_count_failed(failed_items, getattr(control_scale, "threshold", None), getattr(control_scale, "comparison_operator", None))
        details = {"items": item_details}
    elif rule_type == "paired_inconsistency":
        score, triggered, details = evaluate_paired_inconsistency(pair_scores)
        details["items"] = item_details
    else:
        score, triggered = evaluate_any_failed(failed_items)
        details = {"items": item_details}

    if triggered:
        flag_status = "invalid" if getattr(control_scale, "flag_level", "warning") == "invalid" else "warning"
    else:
        flag_status = "pass"
    return {
        "score": score,
        "failed_items": failed_items,
        "total_items": len(active_items),
        "flag_status": flag_status,
        "message": getattr(control_scale, "message", None),
        "details_json": details,
    }
