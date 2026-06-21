from __future__ import annotations

from typing import Any

from app.scoring.scoring_warnings import insufficient_items, low_completion, reverse_scoring_missing_options


def compute_sum_score(values: list[float]) -> float | None:
    return float(sum(values)) if values else None


def compute_mean_score(values: list[float]) -> float | None:
    if not values:
        return None
    return float(sum(values) / len(values))


def compute_weighted_mean_score(values: list[float], weights: list[float]) -> float | None:
    if not values or not weights or len(values) != len(weights):
        return None
    total_weight = float(sum(weights))
    if total_weight <= 0:
        return None
    return float(sum(value * weight for value, weight in zip(values, weights)) / total_weight)


def compute_completion(answered: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((answered / total) * 100, 3)


def apply_reverse_scoring_if_needed(answer: Any, question: Any, options_by_id: dict[str, Any]) -> tuple[float | None, list[str]]:
    warnings: list[str] = []
    if answer is None:
        return None, warnings
    if not getattr(question, "is_scored", False):
        return None, warnings

    option_id = getattr(answer, "option_id", None)
    if option_id is not None:
        option = options_by_id.get(option_id)
        if option is None or getattr(option, "score", None) is None:
            return getattr(answer, "score_value", None), warnings
        score = float(option.score)
        if getattr(question, "is_reverse_scored", False):
            scores = [
                float(candidate.score)
                for candidate in options_by_id.values()
                if getattr(candidate, "deleted_at", None) is None and getattr(candidate, "score", None) is not None
            ]
            if len(scores) < 2:
                warnings.append(reverse_scoring_missing_options())
                return score, warnings
            return max(scores) + min(scores) - score, warnings
        return score, warnings

    if getattr(question, "question_type", None) == "number":
        value_number = getattr(answer, "value_number", None)
        return (float(value_number) if value_number is not None else None), warnings

    score_value = getattr(answer, "score_value", None)
    return (float(score_value) if score_value is not None else None), warnings


def resolve_scored_items(config: Any, questions: list[Any]) -> list[Any]:
    scoring_level = getattr(config, "scoring_level", "custom")
    config_json = getattr(config, "config_json", None) if isinstance(getattr(config, "config_json", None), dict) else {}
    if scoring_level == "instrument" and getattr(config, "instrument_id", None):
        return [question for question in questions if question.instrument_id == config.instrument_id and question.is_scored]
    if scoring_level == "dimension" and getattr(config, "dimension_id", None):
        return [question for question in questions if question.dimension_id == config.dimension_id and question.is_scored]
    if scoring_level == "project_variable" and getattr(config, "project_variable_id", None):
        return [question for question in questions if question.project_variable_id == config.project_variable_id and question.is_scored]
    question_ids = config_json.get("question_ids") if isinstance(config_json, dict) else None
    if isinstance(question_ids, list) and question_ids:
        selected = {str(item) for item in question_ids}
        return [question for question in questions if question.id in selected and question.is_scored]
    return [question for question in questions if question.is_scored]


def apply_missing_policy(
    *,
    values: list[float],
    weights: list[float],
    answered_items: int,
    total_items: int,
    config: Any,
) -> tuple[float | None, float | None, float | None, float | None, list[str]]:
    warnings: list[str] = []
    raw_score = compute_sum_score(values)
    mean_score = compute_mean_score(values)
    weighted_score = compute_weighted_mean_score(values, weights) if weights else None

    completion_percent = compute_completion(answered_items, total_items)
    min_answered_items = getattr(config, "min_answered_items", None)
    min_completion_percent = getattr(config, "min_completion_percent", None)
    missing_policy = getattr(config, "missing_policy", "allow_partial")
    aggregation_method = getattr(config, "aggregation_method", "mean")

    if answered_items == 0:
        warnings.append(insufficient_items())
        return raw_score, mean_score, weighted_score, None, warnings

    if min_answered_items is not None and answered_items < int(min_answered_items):
        warnings.append(insufficient_items())
        return raw_score, mean_score, weighted_score, None, warnings

    if min_completion_percent is not None and completion_percent < float(min_completion_percent):
        warnings.append(low_completion())
        if missing_policy == "strict_complete":
            return raw_score, mean_score, weighted_score, None, warnings

    if missing_policy == "strict_complete" and answered_items < total_items:
        warnings.append(insufficient_items())
        return raw_score, mean_score, weighted_score, None, warnings

    if aggregation_method == "sum":
        final_score = raw_score
        if missing_policy == "prorate_if_threshold_met" and raw_score is not None and mean_score is not None and answered_items < total_items:
            final_score = float(mean_score * total_items)
    elif aggregation_method == "weighted_mean":
        final_score = weighted_score
    else:
        final_score = mean_score
    return raw_score, mean_score, weighted_score, final_score, warnings


def compute_response_score(response: Any, config: Any, answers: dict[str, Any], questions: list[Any], options_by_question_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scored_questions = resolve_scored_items(config, questions)
    values: list[float] = []
    weights: list[float] = []
    warnings: list[str] = []

    for question in scored_questions:
        answer = answers.get(question.id)
        score, question_warnings = apply_reverse_scoring_if_needed(answer, question, options_by_question_id.get(question.id, {}))
        warnings.extend(question_warnings)
        if score is not None:
            values.append(float(score))
            question_weights = {}
            if isinstance(getattr(config, "config_json", None), dict):
                question_weights = getattr(config, "config_json") or {}
            weights_map = question_weights.get("weights", {})
            weight = weights_map.get(question.id, 1.0) if isinstance(weights_map, dict) else 1.0
            weights.append(float(weight))

    answered_items = len(values)
    total_items = len(scored_questions)
    missing_items = max(total_items - answered_items, 0)
    raw_score, mean_score, weighted_score, final_score, policy_warnings = apply_missing_policy(
        values=values,
        weights=weights,
        answered_items=answered_items,
        total_items=total_items,
        config=config,
    )
    warnings.extend(policy_warnings)
    return {
        "project_id": response.project_id,
        "form_id": response.form_id,
        "response_id": response.id,
        "scoring_config_id": config.id,
        "instrument_id": getattr(config, "instrument_id", None),
        "dimension_id": getattr(config, "dimension_id", None),
        "project_variable_id": getattr(config, "project_variable_id", None),
        "raw_score": raw_score,
        "mean_score": mean_score,
        "weighted_score": weighted_score,
        "final_score": final_score,
        "answered_items": answered_items,
        "missing_items": missing_items,
        "total_items": total_items,
        "completion_percent": compute_completion(answered_items, total_items),
        "validity_status": "valid",
        "warnings_json": list(dict.fromkeys(warnings)),
    }
