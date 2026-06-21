from typing import Any

import pandas as pd

from app.schemas.descriptive import FrequencyRowRead


def _round(value: float | None, decimals: int) -> float | None:
    if value is None:
        return None
    return round(float(value), decimals)


def frequency_table(
    values: pd.Series,
    total_n: int,
    *,
    labels: pd.Series | None = None,
    ordered_pairs: list[tuple[Any, str | None]] | None = None,
    decimals: int = 3,
) -> tuple[list[FrequencyRowRead], int]:
    normalized_values = values.where(pd.notna(values), None)
    normalized_labels = labels.where(pd.notna(labels), None) if labels is not None else normalized_values

    valid_mask = normalized_values.notna()
    valid_values = normalized_values[valid_mask]
    valid_labels = normalized_labels[valid_mask]
    valid_n = int(valid_mask.sum())

    rows: list[FrequencyRowRead] = []
    cumulative = 0.0

    if ordered_pairs:
        seen: set[str] = set()
        for raw_value, raw_label in ordered_pairs:
            frequency = int((valid_values == raw_value).sum())
            if raw_value is not None:
                seen.add(str(raw_value))
            cumulative = cumulative + ((frequency / valid_n) * 100 if valid_n else 0.0)
            rows.append(
                FrequencyRowRead(
                    label=raw_label,
                    value=str(raw_value) if raw_value is not None else None,
                    frequency=frequency,
                    percent=_round((frequency / total_n) * 100 if total_n else 0.0, decimals),
                    valid_percent=_round((frequency / valid_n) * 100 if valid_n else 0.0, decimals),
                    cumulative_percent=_round(cumulative if valid_n else 0.0, decimals),
                )
            )

        remaining = (
            pd.DataFrame({"value": valid_values.astype(object), "label": valid_labels.astype(object)})
            .assign(_key=lambda frame: frame["value"].astype(str))
        )
        remaining = remaining[~remaining["_key"].isin(seen)]
        if not remaining.empty:
            grouped = (
                remaining.groupby(["value", "label"], dropna=False)
                .size()
                .reset_index(name="frequency")
                .sort_values(["label", "value"], kind="stable")
            )
            for item in grouped.itertuples(index=False):
                cumulative = cumulative + ((item.frequency / valid_n) * 100 if valid_n else 0.0)
                rows.append(
                    FrequencyRowRead(
                        label=item.label,
                        value=str(item.value) if item.value is not None else None,
                        frequency=int(item.frequency),
                        percent=_round((item.frequency / total_n) * 100 if total_n else 0.0, decimals),
                        valid_percent=_round((item.frequency / valid_n) * 100 if valid_n else 0.0, decimals),
                        cumulative_percent=None,
                    )
                )
        return rows, valid_n

    grouped = (
        pd.DataFrame({"value": valid_values.astype(object), "label": valid_labels.astype(object)})
        .groupby(["value", "label"], dropna=False)
        .size()
        .reset_index(name="frequency")
        .sort_values(["label", "value"], kind="stable")
    )
    for item in grouped.itertuples(index=False):
        rows.append(
            FrequencyRowRead(
                label=item.label,
                value=str(item.value) if item.value is not None else None,
                frequency=int(item.frequency),
                percent=_round((item.frequency / total_n) * 100 if total_n else 0.0, decimals),
                valid_percent=_round((item.frequency / valid_n) * 100 if valid_n else 0.0, decimals),
                cumulative_percent=None,
            )
        )
    return rows, valid_n


def multiple_choice_frequency(
    values: pd.Series,
    total_n: int,
    *,
    ordered_pairs: list[tuple[str, str | None]] | None = None,
    decimals: int = 3,
) -> tuple[list[FrequencyRowRead], int]:
    exploded_rows: list[tuple[str | None, str | None]] = []
    valid_n = 0
    for value in values:
        if not isinstance(value, list) or not value:
            continue
        valid_n += 1
        for item in value:
            if isinstance(item, dict):
                exploded_rows.append((item.get("value"), item.get("label")))
            elif isinstance(item, str):
                exploded_rows.append((item, item))

    exploded_df = pd.DataFrame(exploded_rows, columns=["value", "label"])
    if exploded_df.empty:
        return [], valid_n
    return frequency_table(
        exploded_df["value"],
        total_n,
        labels=exploded_df["label"],
        ordered_pairs=ordered_pairs,
        decimals=decimals,
    )
