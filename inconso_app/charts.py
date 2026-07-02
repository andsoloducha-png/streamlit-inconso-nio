from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from .config import COLOR_SEQUENCE


def metric_card(label: str, value: object) -> None:
    """Render a Streamlit metric using the shared card styling."""
    st.metric(label, value)


def style_chart(fig, height: int = 520):
    """Apply the shared dark Plotly styling to a figure."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        height=height,
        margin=dict(l=20, r=20, t=55, b=20),
        font=dict(family="Arial, sans-serif", size=13, color="#f8fafc"),
        legend_title_text="",
    )
    return fig


def pie_chart(df: pd.DataFrame, names: str, values: str, title: str):
    """Build a donut chart with optional NIO and sorter hover context."""
    custom_data = (
        ["hover_nio", "hover_sorter"]
        if {"hover_nio", "hover_sorter"}.issubset(df.columns)
        else None
    )
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.35,
        title=title,
        color_discrete_sequence=COLOR_SEQUENCE,
        custom_data=custom_data,
    )
    fig.update_traces(textposition="outside", textinfo="label+percent")
    if custom_data:
        fig.update_traces(
            hovertemplate=(
                "%{label}<br>"
                "NIO: %{customdata[0]}<br>"
                "Sorter: %{customdata[1]}<br>"
                "Ilość: %{value}<br>"
                "Udział: %{percent}<extra></extra>"
            )
        )
    return style_chart(fig)
