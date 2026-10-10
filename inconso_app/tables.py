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


def filter_multi(
    df: pd.DataFrame, column: str, selected_values: list[str]
) -> pd.DataFrame:
    """Apply a multi-value filter; an empty selection means all values."""
    if not selected_values:
        return df.copy()
    selected = [str(value) for value in selected_values]
    return df[df[column].astype("string").isin(selected)].copy()


def selection_label(
    selected_values: list[str], all_label: str, item_label: str, limit: int = 3
) -> str:
    """Build a compact label for metrics from a multi-select value list."""
    if not selected_values:
        return all_label
    if len(selected_values) <= limit:
        return ", ".join(str(value) for value in selected_values)
    return f"{len(selected_values)} {item_label}"


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
    share = table["count"] / total * 100
    table["pct"] = share.round(2)
    table["pct_cum"] = share.cumsum().round(2)
    return table


def make_station_quality_table(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize total, OK, NIO and NIO percentage per station."""
    columns = ["Station", "Wszystkie", "OK", "NIO", "% NIO"]
    if df.empty or "Station" not in df.columns or "IsNIO" not in df.columns:
        return pd.DataFrame(columns=columns)

    table = (
        df.groupby("Station", dropna=False)
        .agg(Wszystkie=("IsNIO", "size"), NIO=("IsNIO", "sum"))
        .reset_index()
    )
    table["OK"] = table["Wszystkie"] - table["NIO"]
    table["% NIO"] = (table["NIO"] / table["Wszystkie"] * 100).round(2)
    table = table[["Station", "Wszystkie", "OK", "NIO", "% NIO"]]
    return table.sort_values(["% NIO", "NIO"], ascending=False)


def add_unique_tray_label(df: pd.DataFrame, selected_sorter: str) -> pd.DataFrame:
    """Use sorter-prefixed tray labels when all sorters are selected."""
    df = df.copy()
    df["Tray Tray"] = df["Tray Tray"].astype(str)
    df["Tray Label"] = df["Tray Tray"]
    if selected_sorter == ALL_LABEL and "Tray Sorter" in df.columns:
        df["Tray Label"] = df["Tray Sorter"].astype(str) + " / " + df["Tray Tray"]
    return df
