from typing import Any

import pandas as pd


def build_score_matrix(
    dataframe: pd.DataFrame,
    question_columns: dict[str, str],
) -> pd.DataFrame:
    base_columns = ["response_id"] if "response_id" in dataframe.columns else []
    selected_columns = base_columns + [column for column in question_columns.values() if column in dataframe.columns]
    matrix = dataframe[selected_columns].copy()
    for column in question_columns.values():
        if column in matrix.columns:
            matrix[column] = pd.to_numeric(matrix[column], errors="coerce")
    return matrix


def compute_group_score(
    dataframe: pd.DataFrame,
    score_columns: list[str],
    *,
    aggregation: str,
) -> pd.DataFrame:
    if not score_columns:
        response_ids = dataframe["response_id"] if "response_id" in dataframe.columns else pd.Series(dtype="object")
        return pd.DataFrame(
            {
                "response_id": response_ids,
                "score": pd.Series([None] * len(dataframe), dtype="float"),
                "answered_items": 0,
                "missing_items": 0,
                "completeness_percent": 0.0,
            }
        )

    numeric_frame = dataframe[score_columns].apply(pd.to_numeric, errors="coerce")
    answered_items = numeric_frame.notna().sum(axis=1)
    missing_items = len(score_columns) - answered_items
    if aggregation == "sum":
        score = numeric_frame.sum(axis=1, min_count=1)
    else:
        score = numeric_frame.mean(axis=1)
    completeness_percent = (answered_items / len(score_columns) * 100).round(3)
    return pd.DataFrame(
        {
            "response_id": dataframe["response_id"].tolist() if "response_id" in dataframe.columns else list(range(len(dataframe))),
            "score": score,
            "answered_items": answered_items,
            "missing_items": missing_items,
            "completeness_percent": completeness_percent,
        }
    )


def compute_dimension_scores(
    dataframe: pd.DataFrame,
    dimension_question_columns: dict[str, list[str]],
    *,
    aggregation: str,
) -> dict[str, pd.DataFrame]:
    scores: dict[str, pd.DataFrame] = {}
    for dimension_id, columns in dimension_question_columns.items():
        scores[dimension_id] = compute_group_score(dataframe, columns, aggregation=aggregation)
    return scores


def compute_instrument_scores(
    dataframe: pd.DataFrame,
    instrument_question_columns: dict[str, list[str]],
    *,
    aggregation: str,
) -> dict[str, pd.DataFrame]:
    scores: dict[str, pd.DataFrame] = {}
    for instrument_id, columns in instrument_question_columns.items():
        scores[instrument_id] = compute_group_score(dataframe, columns, aggregation=aggregation)
    return scores
