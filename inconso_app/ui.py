from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from .charts import metric_card, pie_chart, style_chart
from .config import (
    ALL_LABEL,
    COLOR_SEQUENCE,
    DEFAULT_CSV,
    FILTER_STATE_VERSION,
    TIME_FILTER_END,
    TIME_FILTER_START,
)
from .data import load_csv
from .tables import (
    add_pie_hover_context,
    add_unique_tray_label,
    available_values,
    filter_optional,
    make_count_table,
    make_pareto_table,
    with_all_option,
)
from .time_filters import (
    bucket_labels_for_time_range,
    filter_by_clock_range,
    filter_by_time_window,
)


def render_app() -> None:
    """Render the full Streamlit dashboard and bind all app filters."""
    with st.sidebar:
        st.markdown("### ℹ️ Informacje")
        st.markdown("""
            **Raport zawiera:**

            - 📊 Rozkład godzinowy NIO
            - 🧩 Udział stanowisk
            - 🥧 Udział tac
            - 📈 Pareto i porównanie zmian
            - 🎯 Top kombinacje problemowe
            - 🔥 Mapę ciepła sorterów
            - 📋 Podgląd danych

            **Dane:**

            - Format: CSV
            - Separator: średnik
            - Czas: `TimeTele`
            """)
        st.markdown("---")

    st.markdown(
        """
        <div class="app-hero">
            <div class="app-title"><span class="hero-icon">📊</span><span>Analiza Inconso NIO</span></div>
            <div class="app-subtitle">Profesjonalna analiza NIO w kilka sekund</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        """
        <div class="intro-block">
            <h2>🚀 Jak używać:</h2>
            <ol>
                <li>Wgraj plik CSV z danymi.</li>
                <li>Ustaw datę, zmianę, NIO, sorter i stanowisko w panelu bocznym.</li>
                <li>Obejrzyj rozkład godzinowy oraz przekroje stanowisk i tac.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("📁 **Wybierz plik CSV do analizy**")
    uploaded_file = st.file_uploader(
        "Wybierz plik CSV do analizy",
        type=["csv"],
        label_visibility="collapsed",
        help="Plik powinien zawierać kolumny TimeTele, Tray Sorter, Tray Tray, NokReason i Station.",
    )

    default_mtime = DEFAULT_CSV.stat().st_mtime if DEFAULT_CSV.exists() else None
    source_token = (
        f"upload-{uploaded_file.name}-{uploaded_file.size}"
        if uploaded_file
        else f"default-{default_mtime}"
    )
    source_token = f"{FILTER_STATE_VERSION}-{source_token}"

    if uploaded_file is None and not DEFAULT_CSV.exists():
        st.info("Wgraj plik CSV, aby rozpocząć analizę.")
        st.stop()

    try:
        data = load_csv(
            uploaded_file.getvalue() if uploaded_file else None, default_mtime
        )
    except Exception as exc:
        st.error(f"Nie mogę wczytać danych: {exc}")
        st.stop()

    if data.empty:
        st.warning("CSV nie zawiera poprawnych rekordów z datą w kolumnie TimeTele.")
        st.stop()

    min_date = data["Data"].min()
    max_date = data["Data"].max()

    with st.sidebar:
        st.markdown("### Filtry")
        date_range = st.date_input(
            "Zakres dat",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"date_range_{source_token}",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = (
                date_range if isinstance(date_range, date) else min_date
            )

        shift = st.segmented_control(
            "Zmiana",
            options=["Total", "Shift 1", "Shift 2"],
            default="Total",
            key=f"shift_{source_token}",
        )

        hour_range = st.slider(
            "Fragment godzinowy",
            min_value=TIME_FILTER_START,
            max_value=TIME_FILTER_END,
            value=(TIME_FILTER_START, TIME_FILTER_END),
            step=timedelta(minutes=5),
            format="HH:mm",
            key=f"hour_range_{source_token}",
        )
        start_time_filter, end_time_filter = hour_range
        active_bucket_order = bucket_labels_for_time_range(
            start_time_filter, end_time_filter
        )
        st.caption("Domyślnie pełny zakres godzin. Suwak zawęża wszystkie widoki.")

        option_scope = data[
            (data["Data"] >= start_date) & (data["Data"] <= end_date)
        ].copy()
        option_scope = filter_by_time_window(option_scope, shift)
        option_scope = filter_by_clock_range(
            option_scope, start_time_filter, end_time_filter
        )
        sorters = with_all_option(available_values(option_scope, "Tray Sorter"))

        selected_sorter = st.selectbox(
            "Sorter",
            options=sorters,
            index=0,
            key=f"sorter_{source_token}",
        )

        reason_scope = filter_optional(option_scope, "Tray Sorter", selected_sorter)
        reasons = with_all_option(available_values(reason_scope, "NokReason"))

        selected_reason = st.selectbox(
            "NIO / NokReason",
            options=reasons,
            index=0,
            key=f"reason_{source_token}_{selected_sorter}",
        )

        station_scope = filter_optional(reason_scope, "NokReason", selected_reason)
        station_values = [
            str(v)
            for v in station_scope["Station"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        ]
        stations = with_all_option(station_values)

        selected_station = st.selectbox(
            "Station",
            options=stations,
            index=0,
            key=f"station_{source_token}_{selected_reason}_{selected_sorter}",
        )
        st.caption("Lista Station zależy od zakresu dat, zmiany, NIO i sortera.")

    filtered = data[(data["Data"] >= start_date) & (data["Data"] <= end_date)].copy()
    filtered = filter_by_time_window(filtered, shift)
    filtered = filter_by_clock_range(filtered, start_time_filter, end_time_filter)
    reason_filtered = filter_optional(filtered, "NokReason", selected_reason)
    sorter_reason = filter_optional(reason_filtered, "Tray Sorter", selected_sorter)
    station_reason = filter_optional(sorter_reason, "Station", selected_station)

    reason_label = "Total NIO" if selected_reason == ALL_LABEL else selected_reason
    sorter_label = "Total sortery" if selected_sorter == ALL_LABEL else selected_sorter
    station_label = (
        "Total stanowiska" if selected_station == ALL_LABEL else selected_station
    )

    file_label = uploaded_file.name if uploaded_file else DEFAULT_CSV.name
    st.info(
        f"Wczytany plik: **{file_label}** | Rekordy w źródle: **{len(data):,}**".replace(
            ",", " "
        )
    )
    st.markdown("---")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        metric_card("Rekordy", f"{len(filtered):,}".replace(",", " "))
    with col_b:
        metric_card(
            f"NIO: {reason_label}", f"{len(reason_filtered):,}".replace(",", " ")
        )
    with col_c:
        metric_card(
            f"Sorter: {sorter_label}", f"{len(sorter_reason):,}".replace(",", " ")
        )
    with col_d:
        metric_card(
            f"Station: {station_label}", f"{len(station_reason):,}".replace(",", " ")
        )

    if filtered.empty:
        st.warning("Brak rekordów dla wybranego zakresu dat i zmiany.")
        st.stop()

    (
        tab_hourly,
        tab_station,
        tab_tray,
        tab_station_tray,
        tab_chute,
        tab_station_chute,
        tab_extra,
        tab_data,
    ) = st.tabs(
        [
            "Rozkład godzinowy",
            "Sorter / stanowisko",
            "Sorter / taca",
            "Station / taca",
            "Zrzutnie",
            "Zrzutnie / stanowiska",
            "Dodatkowe widoki",
            "Dane",
        ]
    )

    with tab_hourly:
        st.subheader("Analiza: Rozkład godzinowy NIO/Sorter")
        bucket_order = active_bucket_order
        hourly_counts = (
            station_reason.dropna(subset=["Przedzial"])
            .groupby("Przedzial", dropna=False)
            .size()
            .reindex(bucket_order, fill_value=0)
            .reset_index(name="count")
            .rename(columns={"Przedzial": "Przedział"})
        )

        left, right = st.columns([1, 3])
        with left:
            st.dataframe(hourly_counts, width="stretch", hide_index=True)
        with right:
            if selected_sorter == ALL_LABEL:
                sorters_for_chart = (
                    station_reason["Tray Sorter"]
                    .dropna()
                    .astype(str)
                    .sort_values()
                    .unique()
                    .tolist()
                )
                hourly_by_sorter = (
                    station_reason.dropna(subset=["Przedzial"])
                    .groupby(["Przedzial", "Tray Sorter"], dropna=False)
                    .size()
                    .rename("count")
                )
                full_index = pd.MultiIndex.from_product(
                    [bucket_order, sorters_for_chart],
                    names=["Przedzial", "Tray Sorter"],
                )
                hourly_by_sorter = hourly_by_sorter.reindex(
                    full_index, fill_value=0
                ).reset_index()
                fig = px.line(
                    hourly_by_sorter,
                    x="Przedzial",
                    y="count",
                    color="Tray Sorter",
                    markers=True,
                    labels={
                        "count": "Liczba",
                        "Przedzial": "Przedział godzinowy",
                        "Tray Sorter": "Sorter",
                    },
                    color_discrete_sequence=COLOR_SEQUENCE,
                    category_orders={"Przedzial": bucket_order},
                )
            else:
                fig = px.line(
                    hourly_counts,
                    x="Przedział",
                    y="count",
                    markers=True,
                    labels={"count": "Liczba", "Przedział": "Przedział godzinowy"},
                    color_discrete_sequence=[COLOR_SEQUENCE[0]],
                    category_orders={"PrzedziaĹ‚": bucket_order},
                )
            fig = style_chart(fig, height=470)
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            fig.update_xaxes(categoryorder="array", categoryarray=bucket_order)
            st.plotly_chart(fig, width="stretch")

    with tab_station:
        st.subheader("Analiza: NIO/sorter/stanowisko/zmiana")
        station_table = make_count_table(
            station_reason,
            ["Tray Sorter", "Station", "NokReason"],
        )

        left, right = st.columns([1, 2])
        with left:
            st.dataframe(station_table, width="stretch", hide_index=True)
        with right:
            if not station_table.empty:
                chart_data = (
                    station_table.groupby("Station", dropna=False)["count"]
                    .sum()
                    .reset_index()
                )
                chart_data["Station"] = chart_data["Station"].astype(str)
                chart_data = add_pie_hover_context(
                    chart_data, station_reason, "Station"
                )
                fig = pie_chart(
                    chart_data,
                    names="Station",
                    values="count",
                    title="Udział stanowisk",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Brak danych dla tej kombinacji filtrów.")

    with tab_tray:
        st.subheader("Analiza: NIO/sorter/taca/zmiana")
        tray_table = make_count_table(
            station_reason,
            ["Tray Sorter", "Tray Tray", "NokReason"],
        )
        tray_table = add_unique_tray_label(tray_table, selected_sorter)
        tray_table = (
            tray_table.sort_values("count", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )

        left, right = st.columns([1, 2])
        with left:
            st.dataframe(tray_table, width="stretch", hide_index=True)
        with right:
            if not tray_table.empty:
                chart_data = (
                    tray_table.groupby("Tray Label", dropna=False)["count"]
                    .sum()
                    .reset_index()
                )
                hover_source = add_unique_tray_label(station_reason, selected_sorter)
                chart_data = add_pie_hover_context(
                    chart_data, hover_source, "Tray Label"
                )
                fig = pie_chart(
                    chart_data,
                    names="Tray Label",
                    values="count",
                    title="Top 20 tac dla wybranego sortera",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Brak danych dla tej kombinacji filtrów.")

    with tab_station_tray:
        st.subheader("Analiza: Station/taca/NIO")
        station_tray_table = make_count_table(
            station_reason,
            ["Tray Sorter", "Station", "Tray Tray", "NokReason"],
        )
        station_tray_table = add_unique_tray_label(station_tray_table, selected_sorter)
        station_tray_table = (
            station_tray_table.sort_values("count", ascending=False)
            .head(20)
            .reset_index(drop=True)
        )

        left, right = st.columns([1, 2])
        with left:
            st.dataframe(station_tray_table, width="stretch", hide_index=True)
        with right:
            if not station_tray_table.empty:
                chart_data = (
                    station_tray_table.groupby("Tray Label", dropna=False)["count"]
                    .sum()
                    .reset_index()
                )
                hover_source = add_unique_tray_label(station_reason, selected_sorter)
                chart_data = add_pie_hover_context(
                    chart_data, hover_source, "Tray Label"
                )
                fig = pie_chart(
                    chart_data,
                    names="Tray Label",
                    values="count",
                    title=f"Top 20 tac dla: {station_label}",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Brak danych dla tej kombinacji filtrów.")

    with tab_chute:
        st.subheader("Analiza: do jakiej zrzutni spadają NIO")
        if "Chute" not in station_reason.columns:
            st.info("Brak kolumny Chute w danych.")
        else:
            chute_scope = station_reason.copy()
            chute_scope["Chute"] = chute_scope["Chute"].fillna("brak").astype(str)

            chute_table = make_count_table(
                chute_scope,
                ["Chute", "Tray Sorter", "NokReason"],
            )
            chute_chart = (
                chute_scope.groupby(["Chute", "NokReason"], dropna=False)
                .size()
                .reset_index(name="count")
            )
            top_chutes = (
                chute_chart.groupby("Chute")["count"]
                .sum()
                .sort_values(ascending=False)
                .head(20)
                .index.tolist()
            )
            chute_chart = chute_chart[chute_chart["Chute"].isin(top_chutes)].copy()

            left, right = st.columns([1, 2])
            with left:
                st.dataframe(chute_table.head(50), width="stretch", hide_index=True)
            with right:
                if not chute_chart.empty:
                    fig = px.bar(
                        chute_chart,
                        x="count",
                        y="Chute",
                        color="NokReason",
                        orientation="h",
                        labels={
                            "count": "Liczba",
                            "Chute": "Zrzutnia",
                            "NokReason": "NIO",
                        },
                        title="Top zrzutnie NIO",
                        color_discrete_sequence=COLOR_SEQUENCE,
                        custom_data=["NokReason"],
                    )
                    fig.update_traces(
                        hovertemplate="Zrzutnia: %{y}<br>NIO: %{customdata[0]}<br>Ilość: %{x}<extra></extra>"
                    )
                    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
                    fig = style_chart(fig, height=620)
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("Brak danych zrzutni dla aktualnych filtrów.")

    with tab_station_chute:
        st.subheader("Analiza: z jakiego stanowiska i do jakiej zrzutni leci NIO")
        if "Chute" not in station_reason.columns:
            st.info("Brak kolumny Chute w danych.")
        else:
            station_chute_scope = station_reason.copy()
            station_chute_scope["Chute"] = (
                station_chute_scope["Chute"].fillna("brak").astype(str)
            )
            station_chute_scope["Station"] = (
                station_chute_scope["Station"].fillna("brak").astype(str)
            )

            station_chute_table = make_count_table(
                station_chute_scope,
                ["Chute", "Station", "Tray Sorter", "NokReason"],
            )
            station_chute_chart = (
                station_chute_scope.groupby(["Chute", "Station"], dropna=False)
                .size()
                .reset_index(name="count")
            )
            top_chutes_by_station = (
                station_chute_chart.groupby("Chute")["count"]
                .sum()
                .sort_values(ascending=False)
                .head(20)
                .index.tolist()
            )
            station_chute_chart = station_chute_chart[
                station_chute_chart["Chute"].isin(top_chutes_by_station)
            ].copy()

            left, right = st.columns([1, 2])
            with left:
                st.dataframe(
                    station_chute_table.head(75), width="stretch", hide_index=True
                )
            with right:
                if not station_chute_chart.empty:
                    fig = px.bar(
                        station_chute_chart,
                        x="Chute",
                        y="count",
                        color="Station",
                        barmode="stack",
                        labels={
                            "count": "Liczba",
                            "Chute": "Zrzutnia",
                            "Station": "Stanowisko",
                        },
                        title="Zrzutnie NIO według stanowisk",
                        color_discrete_sequence=COLOR_SEQUENCE,
                        custom_data=["Station"],
                    )
                    fig.update_traces(
                        hovertemplate=(
                            "Zrzutnia: %{x}<br>"
                            "Station: %{customdata[0]}<br>"
                            "Ilość: %{y}<extra></extra>"
                        )
                    )
                    fig.update_layout(xaxis=dict(categoryorder="total descending"))
                    fig = style_chart(fig, height=620)
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info(
                        "Brak danych stanowisko -> zrzutnia dla aktualnych filtrów."
                    )

    with tab_extra:
        st.subheader("Dodatkowe widoki")
        extra_left, extra_right = st.columns(2)

        with extra_left:
            heatmap_data = (
                station_reason.dropna(subset=["Przedzial"])
                .groupby(["Tray Sorter", "Przedzial"])
                .size()
                .reset_index(name="count")
            )
            if not heatmap_data.empty:
                pivot = heatmap_data.pivot(
                    index="Tray Sorter", columns="Przedzial", values="count"
                ).fillna(0)
                pivot = pivot.reindex(columns=active_bucket_order, fill_value=0)
                fig = px.imshow(
                    pivot,
                    aspect="auto",
                    labels=dict(x="Przedział", y="Sorter", color="Liczba"),
                    title=f"Mapa ciepła: {reason_label} według sortera i godziny",
                    color_continuous_scale="Blues",
                )
                fig = style_chart(fig)
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Brak danych do mapy ciepła.")

        with extra_right:
            reason_rank = make_count_table(station_reason, ["NokReason"], limit=15)
            if not reason_rank.empty:
                fig = px.bar(
                    reason_rank.sort_values("count"),
                    x="count",
                    y="NokReason",
                    orientation="h",
                    labels={"count": "Liczba", "NokReason": "NIO"},
                    title="Top NIO w wybranym zakresie",
                    color_discrete_sequence=[COLOR_SEQUENCE[0]],
                )
                fig = style_chart(fig)
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("Brak danych do rankingu NIO.")

        trend = (
            station_reason.groupby(["Data", "Tray Sorter"], dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values("Data")
        )
        if not trend.empty:
            fig = px.line(
                trend,
                x="Data",
                y="count",
                color="Tray Sorter",
                markers=True,
                labels={"count": "Liczba", "Data": "Data", "Tray Sorter": "Sorter"},
                title=f"Trend dzienny: {reason_label}",
                color_discrete_sequence=COLOR_SEQUENCE,
            )
            fig = style_chart(fig, height=420)
            st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        diagnostic_left, diagnostic_right = st.columns(2)

        with diagnostic_left:
            st.subheader("Pareto NIO")
            pareto = make_pareto_table(station_reason, "NokReason", limit=15)
            if not pareto.empty:
                pareto_labels = pareto["NokReason"].astype(str)
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=pareto_labels,
                        y=pareto["count"],
                        name="Ilość",
                        marker_color=COLOR_SEQUENCE[0],
                        hovertemplate="NIO: %{x}<br>Ilość: %{y}<extra></extra>",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=pareto_labels,
                        y=pareto["pct_cum"],
                        name="% narastająco",
                        mode="lines+markers",
                        yaxis="y2",
                        line=dict(color="#f59e0b", width=3),
                        hovertemplate="NIO: %{x}<br>% narastająco: %{y:.2f}%<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Które NIO robią największy udział problemu",
                    yaxis=dict(title="Ilość"),
                    yaxis2=dict(
                        title="% narastająco",
                        overlaying="y",
                        side="right",
                        range=[0, 105],
                    ),
                    xaxis=dict(title="NIO"),
                )
                fig = style_chart(fig, height=470)
                st.plotly_chart(fig, width="stretch")
                st.dataframe(pareto, width="stretch", hide_index=True)
            else:
                st.info("Brak danych do Pareto dla aktualnych filtrów.")

        with diagnostic_right:
            st.subheader("Porównanie zmian")
            shift_scope = data[
                (data["Data"] >= start_date) & (data["Data"] <= end_date)
            ].copy()
            shift_scope = filter_optional(shift_scope, "NokReason", selected_reason)
            shift_scope = filter_optional(shift_scope, "Tray Sorter", selected_sorter)
            shift_scope = filter_optional(shift_scope, "Station", selected_station)
            shift_scope = shift_scope[shift_scope["Shift"].isin(["Shift 1", "Shift 2"])]

            if not shift_scope.empty:
                top_shift_reasons = (
                    shift_scope["NokReason"]
                    .astype(str)
                    .value_counts()
                    .head(8)
                    .index.tolist()
                )
                shift_chart = (
                    shift_scope[
                        shift_scope["NokReason"].astype(str).isin(top_shift_reasons)
                    ]
                    .groupby(["Shift", "NokReason"], dropna=False)
                    .size()
                    .reset_index(name="count")
                )
                fig = px.bar(
                    shift_chart,
                    x="Shift",
                    y="count",
                    color="NokReason",
                    barmode="group",
                    labels={"count": "Ilość", "Shift": "Zmiana", "NokReason": "NIO"},
                    title="Shift 1 vs Shift 2",
                    color_discrete_sequence=COLOR_SEQUENCE,
                    custom_data=["NokReason"],
                )
                fig.update_traces(
                    hovertemplate="Zmiana: %{x}<br>NIO: %{customdata[0]}<br>Ilość: %{y}<extra></extra>"
                )
                fig = style_chart(fig, height=470)
                st.plotly_chart(fig, width="stretch")

                shift_table = shift_chart.pivot_table(
                    index="NokReason",
                    columns="Shift",
                    values="count",
                    aggfunc="sum",
                    fill_value=0,
                ).reset_index()
                for column in ["Shift 1", "Shift 2"]:
                    if column not in shift_table.columns:
                        shift_table[column] = 0
                shift_table["Różnica"] = shift_table["Shift 2"] - shift_table["Shift 1"]
                shift_table = shift_table.sort_values(
                    ["Shift 1", "Shift 2"], ascending=False
                )
                st.dataframe(shift_table, width="stretch", hide_index=True)
            else:
                st.info("Brak danych do porównania Shift 1 vs Shift 2.")

        st.markdown("---")
        st.subheader("Top kombinacje problemowe")
        combo_table = make_count_table(
            station_reason,
            ["Tray Sorter", "Station", "Tray Tray", "NokReason"],
            limit=25,
        )
        if not combo_table.empty:
            combo_table["Kombinacja"] = (
                combo_table["Tray Sorter"].astype(str)
                + " / Station "
                + combo_table["Station"].astype(str)
                + " / Taca "
                + combo_table["Tray Tray"].astype(str)
                + " / "
                + combo_table["NokReason"].astype(str)
            )
            fig = px.bar(
                combo_table.sort_values("count"),
                x="count",
                y="Kombinacja",
                orientation="h",
                labels={"count": "Ilość", "Kombinacja": "Kombinacja"},
                title="Gdzie zacząć sprawdzanie",
                color_discrete_sequence=[COLOR_SEQUENCE[1]],
            )
            fig.update_traces(
                hovertemplate=(
                    "Sorter/Station/Taca/NIO: %{y}<br>" "Ilość: %{x}<extra></extra>"
                )
            )
            fig = style_chart(fig, height=680)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(
                combo_table[
                    ["Tray Sorter", "Station", "Tray Tray", "NokReason", "count"]
                ],
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("Brak danych do rankingu kombinacji.")

    with tab_data:
        st.subheader("Dane po filtrach")
        visible_columns = [
            "Timestamp",
            "Tray Sorter",
            "Tray Tray",
            "NokReason",
            "Station",
            "Shift",
            "Przedzial",
            "Quality-Label",
            "Chute",
            "UID-Sorter",
        ]
        existing_columns = [
            col for col in visible_columns if col in station_reason.columns
        ]
        st.dataframe(station_reason[existing_columns], width="stretch", hide_index=True)
