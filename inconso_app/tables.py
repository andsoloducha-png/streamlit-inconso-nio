from __future__ import annotations

import pandas as pd

from .config import ALL_LABEL


def available_values(df: pd.DataFrame, column: str) -> list[str]:
    """Return sorted non-empty values for a filter column."""
    values = df[column].dropna().astype(str).sort_values().unique().tolist()
    return values


def with_all_option(values: list[str]) -> list[str]:
    """Prepend the Total option to a list of filter values."""
    return [ALL_LABEL, *values]


def filter_optional(df: pd.DataFrame, column: str, selected_value: str) -> pd.DataFrame:
    """Apply a filter only when the selected value is not Total."""
    if selected_value == ALL_LABEL:
        return df.copy()
    return df[df[column].astype("string") == selected_value].copy()


def make_count_table(
    df: pd.DataFrame, group_columns: list[str], limit: int | None = None
) -> pd.DataFrame:
    """Aggregate rows by selected columns and return descending counts."""
    if df.empty:
        return pd.DataFrame(columns=[*group_columns, "count"])
    table = (
        df.groupby(group_columns, dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    if limit is not None:
        table = table.head(limit)
    return table


def top_values_label(df: pd.DataFrame, column: str, limit: int = 3) -> str:
    """Build a compact top-values label for chart hover details."""
    if df.empty or column not in df.columns:
        return "brak"
    counts = df[column].dropna().astype(str).value_counts().head(limit)
    if counts.empty:
        return "brak"
    return ", ".join(f"{label} ({count})" for label, count in counts.items())


def add_pie_hover_context(
    chart_df: pd.DataFrame, source_df: pd.DataFrame, slice_column: str
) -> pd.DataFrame:
    """Attach top NIO and sorter descriptions to pie chart slices."""
    chart_df = chart_df.copy()
    nio_values = []
    sorter_values = []

    source_slice = source_df.copy()
    source_slice["_slice_value"] = source_slice[slice_column].astype(str)

    for value in chart_df[slice_column].astype(str):
        part = source_slice[source_slice["_slice_value"] == value]
        nio_values.append(top_values_label(part, "NokReason"))
        sorter_values.append(top_values_label(part, "Tray Sorter"))

    chart_df["hover_nio"] = nio_values
    chart_df["hover_sorter"] = sorter_values
    return chart_df


def make_pareto_table(df: pd.DataFrame, column: str, limit: int = 15) -> pd.DataFrame:
    """Create a Pareto table with percentage and cumulative percentage."""
    table = make_count_table(df, [column], limit=limit)
    if table.empty:
        return table.assign(
            pct=pd.Series(dtype="float64"), pct_cum=pd.Series(dtype="float64")
        )

    total = table["count"].sum()
    table["pct"] = (table["count"] / total * 100).round(2)
    table["pct_cum"] = table["pct"].cumsum().round(2)
    return table


def add_unique_tray_label(df: pd.DataFrame, selected_sorter: str) -> pd.DataFrame:
    """Use sorter-prefixed tray labels when all sorters are selected."""
    df = df.copy()
    df["Tray Tray"] = df["Tray Tray"].astype(str)
    df["Tray Label"] = df["Tray Tray"]
    if selected_sorter == ALL_LABEL and "Tray Sorter" in df.columns:
        df["Tray Label"] = df["Tray Sorter"].astype(str) + " / " + df["Tray Tray"]
    return df
