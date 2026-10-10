from __future__ import annotations

from datetime import date, timedelta
import re

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
    filter_multi,
    make_count_table,
    make_pareto_table,
    make_station_quality_table,
    selection_label,
)
from .time_filters import (
    bucket_labels_for_time_range,
    filter_by_clock_range,
    filter_by_time_window,
    interval_label,
    interval_labels_for_time_range,
)


def natural_label_order(values: pd.Series | list[object]) -> list[str]:
    """Sort chart labels in a human-friendly order instead of by metric value."""
    labels = pd.Series(values).dropna().astype(str).unique().tolist()

    def key(label: str) -> tuple[tuple[int, object], ...]:
        parts = re.split(r"(\d+)", label)
        return tuple(
            (0, int(part), len(part)) if part.isdigit() else (1, part.casefold())
            for part in parts
        )

    return sorted(labels, key=key)


def render_app() -> None:
    """Render the full Streamlit dashboard and bind all app filters."""
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

    if uploaded_file is not None:
        celebration_key = f"balloons_shown_{source_token}"
        if not st.session_state.get(celebration_key, False):
            st.balloons()
            st.session_state[celebration_key] = True

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
        sorters = available_values(option_scope, "Tray Sorter")

        selected_sorters = st.multiselect(
            "Sorter",
            options=sorters,
            default=[],
            placeholder="Wybierz co najmniej jeden sorter",
            key=f"sorter_{source_token}",
        )

        sorter_key_token = "_".join(selected_sorters) if selected_sorters else "all"
        reason_scope = (
            filter_multi(option_scope, "Tray Sorter", selected_sorters)
            if selected_sorters
            else option_scope.iloc[0:0].copy()
        )
        nio_reason_scope = reason_scope[reason_scope["IsNIO"]].copy()
        reasons = available_values(nio_reason_scope, "NokReason")

        selected_reasons = st.multiselect(
            "NIO / NokReason",
            options=reasons,
            default=[],
            placeholder="Wszystkie NIO",
            key=f"reason_{source_token}_{sorter_key_token}",
            disabled=not selected_sorters,
        )

        reason_key_token = "_".join(selected_reasons) if selected_reasons else "all"
        station_scope = filter_multi(nio_reason_scope, "NokReason", selected_reasons)
        station_options_scope = (
            station_scope if not station_scope.empty else reason_scope
        )
        station_values = [
            str(v)
            for v in station_options_scope["Station"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        ]

        selected_stations = st.multiselect(
            "Station",
            options=station_values,
            default=[],
            placeholder="Wszystkie stanowiska",
            key=f"station_{source_token}_{sorter_key_token}_{reason_key_token}",
            disabled=not selected_sorters,
        )
        st.caption("Lista Station zależy od zakresu dat, zmiany, NIO i sortera.")

    file_label = uploaded_file.name if uploaded_file else DEFAULT_CSV.name
    st.info(
        f"Wczytany plik: **{file_label}** | Rekordy w źródle: **{len(data):,}**".replace(
            ",", " "
        )
    )

    if not selected_sorters:
        st.warning(
            "Wybierz w panelu bocznym co najmniej jeden sorter, żeby uruchomić analizę."
        )
        st.stop()

    filtered = data[(data["Data"] >= start_date) & (data["Data"] <= end_date)].copy()
    filtered = filter_by_time_window(filtered, shift)
    filtered = filter_by_clock_range(filtered, start_time_filter, end_time_filter)
    sorter_filtered = filter_multi(filtered, "Tray Sorter", selected_sorters)
    filtered = filter_multi(sorter_filtered, "Station", selected_stations)
    nio_scope = sorter_filtered[sorter_filtered["IsNIO"]].copy()
    reason_filtered = filter_multi(nio_scope, "NokReason", selected_reasons)
    sorter_reason = reason_filtered
    station_reason = filter_multi(reason_filtered, "Station", selected_stations)

    reason_label = selection_label(selected_reasons, "Total NIO", "NIO")
    sorter_label = selection_label(selected_sorters, "Total sortery", "sorterów")
    station_label = selection_label(selected_stations, "Total stanowiska", "stanowisk")
    single_sorter_label = (
        selected_sorters[0] if len(selected_sorters) == 1 else ALL_LABEL
    )
    has_ok_records = (~data["IsNIO"]).any()
    data_mode_label = "pełny strumień OK + NIO" if has_ok_records else "tylko NIO"

    st.caption(f"Tryb danych: {data_mode_label}")
    st.markdown("---")

    ok_count = int((~filtered["IsNIO"]).sum()) if "IsNIO" in filtered.columns else 0

    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        metric_card("Rekordy", f"{len(filtered):,}".replace(",", " "))
    with col_b:
        metric_card("OK", f"{ok_count:,}".replace(",", " "))
    with col_c:
        metric_card(
            f"NIO: {reason_label}", f"{len(station_reason):,}".replace(",", " ")
        )
    with col_d:
        metric_card(
            f"Sorter: {sorter_label}", f"{len(sorter_reason):,}".replace(",", " ")
        )
    with col_e:
        metric_card(
            f"Station: {station_label}", f"{len(station_reason):,}".replace(",", " ")
        )

    if filtered.empty:
        st.warning("Brak rekordów dla wybranego zakresu dat i zmiany.")
        st.stop()

    tab_labels = [
        "Rozkład w czasie",
        "Sorter / stanowisko",
        "Sorter / taca",
        "Station / taca",
        "Zrzutnie",
        "Zrzutnie / stanowiska",
        "Dodatkowe widoki",
        "Dane",
    ]
    if has_ok_records:
        tab_labels.extend(["OK / zrzutnie", "Jakość stanowisk"])

    (
        tab_hourly,
        tab_station,
        tab_tray,
        tab_station_tray,
        tab_chute,
        tab_station_chute,
        tab_extra,
        tab_data,
        *full_data_tabs,
    ) = st.tabs(tab_labels)
    tab_ok_chute = full_data_tabs[0] if has_ok_records else None
    tab_quality = full_data_tabs[1] if has_ok_records else None

    with tab_hourly:
        st.subheader("Analiza: rozklad w czasie")
        interval_options = {
            "Godzinowo": None,
            "30 minut": 30,
            "15 minut": 15,
            "10 minut": 10,
            "5 minut": 5,
        }
        col_time_mode, col_compare_mode = st.columns([1, 1])
        with col_time_mode:
            selected_interval_label = st.selectbox(
                "Agregacja czasu",
                options=list(interval_options.keys()),
                index=0,
                key=f"time_interval_{source_token}",
            )
        with col_compare_mode:
            compare_by = st.segmented_control(
                "Porownaj wedlug",
                options=["NIO", "Sorter"],
                default="NIO",
                key=f"time_compare_{source_token}",
            )

        interval_minutes = interval_options[selected_interval_label]
        time_scope = station_reason.copy()
        if interval_minutes is None:
            time_column = "Przedzial"
            time_axis_label = "Przedzial czasu"
            time_order = active_bucket_order
        else:
            time_column = "Przedzial czasu"
            time_axis_label = f"Przedzial {selected_interval_label.lower()}"
            time_order = interval_labels_for_time_range(
                start_time_filter, end_time_filter, interval_minutes
            )
            time_scope[time_column] = time_scope["Godzina"].map(
                lambda value: interval_label(value, interval_minutes)
            )

        time_counts = (
            time_scope.dropna(subset=[time_column])
            .groupby(time_column, dropna=False)
            .size()
            .reindex(time_order, fill_value=0)
            .reset_index(name="count")
        )

        left, right = st.columns([1, 3])
        with left:
            st.dataframe(time_counts, width="stretch", hide_index=True)
        with right:
            compare_column = "NokReason" if compare_by == "NIO" else "Tray Sorter"
            compare_values = (
                time_scope[compare_column].dropna().astype(str).unique().tolist()
            )
            compare_values = natural_label_order(compare_values)
            if compare_values:
                time_by_series = (
                    time_scope.dropna(subset=[time_column])
                    .groupby([time_column, compare_column], dropna=False)
                    .size()
                    .rename("count")
                )
                full_index = pd.MultiIndex.from_product(
                    [time_order, compare_values],
                    names=[time_column, compare_column],
                )
                time_by_series = time_by_series.reindex(
                    full_index, fill_value=0
                ).reset_index()
                fig = px.line(
                    time_by_series,
                    x=time_column,
                    y="count",
                    color=compare_column,
                    markers=True,
                    labels={
                        "count": "Liczba",
                        time_column: time_axis_label,
                        compare_column: compare_by,
                    },
                    color_discrete_sequence=COLOR_SEQUENCE,
                    category_orders={time_column: time_order},
                )
            else:
                fig = px.line(
                    time_counts,
                    x=time_column,
                    y="count",
                    markers=True,
                    labels={"count": "Liczba", time_column: time_axis_label},
                    color_discrete_sequence=[COLOR_SEQUENCE[0]],
                    category_orders={time_column: time_order},
                )
            fig = style_chart(fig, height=520)
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            fig.update_xaxes(categoryorder="array", categoryarray=time_order)
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
        tray_table = add_unique_tray_label(tray_table, single_sorter_label)
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
                hover_source = add_unique_tray_label(
                    station_reason, single_sorter_label
                )
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
        station_tray_table = add_unique_tray_label(
            station_tray_table, single_sorter_label
        )
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
                hover_source = add_unique_tray_label(
                    station_reason, single_sorter_label
                )
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
            chute_order = natural_label_order(chute_chart["Chute"])
            reason_order = natural_label_order(chute_chart["NokReason"])

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
                        category_orders={
                            "Chute": chute_order,
                            "NokReason": reason_order,
                        },
                    )
                    fig.update_traces(
                        hovertemplate="Zrzutnia: %{y}<br>NIO: %{customdata[0]}<br>Ilość: %{x}<extra></extra>"
                    )
                    fig.update_yaxes(
                        categoryorder="array",
                        categoryarray=chute_order,
                        autorange="reversed",
                    )
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
            station_chute_order = natural_label_order(station_chute_chart["Chute"])
            station_order = natural_label_order(station_chute_chart["Station"])

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
                        category_orders={
                            "Chute": station_chute_order,
                            "Station": station_order,
                        },
                    )
                    fig.update_traces(
                        hovertemplate=(
                            "Zrzutnia: %{x}<br>"
                            "Station: %{customdata[0]}<br>"
                            "Ilość: %{y}<extra></extra>"
                        )
                    )
                    fig.update_xaxes(
                        categoryorder="array", categoryarray=station_chute_order
                    )
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
                pivot = pivot.reindex(index=natural_label_order(pivot.index))
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
            trend_sorter_order = natural_label_order(trend["Tray Sorter"])
            fig = px.line(
                trend,
                x="Data",
                y="count",
                color="Tray Sorter",
                markers=True,
                labels={"count": "Liczba", "Data": "Data", "Tray Sorter": "Sorter"},
                title=f"Trend dzienny: {reason_label}",
                color_discrete_sequence=COLOR_SEQUENCE,
                category_orders={"Tray Sorter": trend_sorter_order},
            )
            fig = style_chart(fig, height=420)
            st.plotly_chart(fig, width="stretch")

        st.markdown("---")
        diagnostic_left, diagnostic_right = st.columns(2)

        with diagnostic_left:
            st.subheader("Pareto NIO")
            pareto = make_pareto_table(station_reason, "NokReason", limit=15)
            if not pareto.empty:
                pareto = pareto.copy()
                pareto["pct_label"] = pareto["pct"].map(lambda value: f"{value:.1f}%")
                pareto_labels = pareto["NokReason"].astype(str)
                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=pareto_labels,
                        y=pareto["count"],
                        name="Ilość",
                        marker_color=COLOR_SEQUENCE[0],
                        text=pareto["count"],
                        textposition="outside",
                        cliponaxis=False,
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
                        marker=dict(size=8),
                        text=pareto["pct_label"],
                        textposition="top center",
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
                        range=[0, 100],
                        tickmode="array",
                        tickvals=[0, 20, 40, 60, 80, 100],
                        ticksuffix="%",
                        showgrid=False,
                    ),
                    xaxis=dict(title="NIO", tickangle=-30),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                    ),
                    bargap=0.25,
                )
                fig = style_chart(fig, height=560)
                st.plotly_chart(fig, width="stretch")
                pareto_table = pareto.rename(
                    columns={
                        "NokReason": "NIO",
                        "count": "Ilość",
                        "pct": "% udział",
                        "pct_cum": "% narastająco",
                    }
                )
                st.dataframe(
                    pareto_table[["NIO", "Ilość", "% udział", "% narastająco"]],
                    width="stretch",
                    hide_index=True,
                    height=360,
                )
            else:
                st.info("Brak danych do Pareto dla aktualnych filtrów.")

        with diagnostic_right:
            st.subheader("Porównanie zmian")
            shift_scope = data[
                (data["Data"] >= start_date) & (data["Data"] <= end_date)
            ].copy()
            shift_scope = filter_multi(shift_scope, "Tray Sorter", selected_sorters)
            shift_scope = shift_scope[shift_scope["IsNIO"]].copy()
            shift_scope = filter_multi(shift_scope, "NokReason", selected_reasons)
            shift_scope = filter_multi(shift_scope, "Station", selected_stations)
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
                shift_reason_order = natural_label_order(shift_chart["NokReason"])
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
                    category_orders={
                        "Shift": ["Shift 1", "Shift 2"],
                        "NokReason": shift_reason_order,
                    },
                )
                fig.update_traces(
                    hovertemplate="Zmiana: %{x}<br>NIO: %{customdata[0]}<br>Ilość: %{y}<extra></extra>"
                )
                fig = style_chart(fig, height=560)
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
                st.dataframe(shift_table, width="stretch", hide_index=True, height=360)
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

    if has_ok_records and tab_ok_chute is not None:
        with tab_ok_chute:
            st.subheader("Analiza: dobre rzeczy według zrzutni")
            if "Chute" not in filtered.columns:
                st.info("Brak kolumny Chute w danych.")
            else:
                ok_chute_scope = filtered[~filtered["IsNIO"]].copy()
                ok_chute_scope["Chute"] = (
                    ok_chute_scope["Chute"].fillna("brak").astype(str)
                )

                if ok_chute_scope.empty:
                    st.info("Brak dobrych rekordów dla aktualnych filtrów.")
                else:
                    ok_chute_chart = (
                        ok_chute_scope.groupby(["Chute", "Tray Sorter"], dropna=False)
                        .size()
                        .reset_index(name="count")
                    )
                    top_ok_chutes = (
                        ok_chute_chart.groupby("Chute")["count"]
                        .sum()
                        .sort_values(ascending=False)
                        .head(20)
                        .index.tolist()
                    )
                    ok_chute_chart = ok_chute_chart[
                        ok_chute_chart["Chute"].isin(top_ok_chutes)
                    ].copy()
                    ok_sorter_order = natural_label_order(ok_chute_chart["Tray Sorter"])
                    ok_chute_table = make_count_table(
                        ok_chute_scope[ok_chute_scope["Chute"].isin(top_ok_chutes)],
                        ["Chute", "Tray Sorter", "Station"],
                    )

                    left, right = st.columns([1, 2])
                    with left:
                        st.dataframe(
                            ok_chute_table.head(100),
                            width="stretch",
                            hide_index=True,
                            height=620,
                        )
                    with right:
                        fig = px.bar(
                            ok_chute_chart.sort_values("count"),
                            x="count",
                            y="Chute",
                            color="Tray Sorter",
                            orientation="h",
                            labels={
                                "count": "Liczba",
                                "Chute": "Zrzutnia",
                                "Tray Sorter": "Sorter",
                            },
                            title="Top 20 zrzutni dla dobrych rekordów",
                            color_discrete_sequence=COLOR_SEQUENCE,
                            custom_data=["Tray Sorter"],
                            category_orders={"Tray Sorter": ok_sorter_order},
                        )
                        fig.update_traces(
                            hovertemplate=(
                                "Zrzutnia: %{y}<br>"
                                "Sorter: %{customdata[0]}<br>"
                                "Ilość OK: %{x}<extra></extra>"
                            )
                        )
                        fig = style_chart(fig, height=620)
                        st.plotly_chart(fig, width="stretch")

    if has_ok_records and tab_quality is not None:
        with tab_quality:
            st.subheader("Jakość stanowisk")
            quality_table = make_station_quality_table(filtered)
            if quality_table.empty:
                st.info("Brak danych jakości dla aktualnych filtrów.")
            else:
                nio_quality_scope = filtered[filtered["IsNIO"]].copy()
                if not nio_quality_scope.empty:
                    reason_counts = (
                        nio_quality_scope.groupby(
                            ["Station", "NokReason"], dropna=False
                        )
                        .size()
                        .unstack(fill_value=0)
                        .reset_index()
                    )
                    reason_counts.columns = [
                        "Station" if column == "Station" else str(column)
                        for column in reason_counts.columns
                    ]
                    reason_columns = [
                        column
                        for column in reason_counts.columns
                        if column != "Station"
                    ]
                    reason_columns = natural_label_order(reason_columns)
                    reason_counts = reason_counts[["Station", *reason_columns]]

                    quality_table = quality_table.merge(
                        reason_counts, on="Station", how="left"
                    ).fillna(0)
                    for reason in reason_columns:
                        percent_column = f"{reason} % całości"
                        quality_table[percent_column] = (
                            quality_table[reason] / quality_table["Wszystkie"] * 100
                        ).round(2)

                    ordered_columns = ["Station", "Wszystkie", "OK", "NIO", "% NIO"]
                    for reason in reason_columns:
                        ordered_columns.extend([reason, f"{reason} % całości"])
                    quality_table = quality_table[ordered_columns]

                left, right = st.columns([1, 2])
                with left:
                    st.dataframe(
                        quality_table, width="stretch", hide_index=True, height=560
                    )
                with right:
                    chart_data = quality_table.sort_values(
                        ["% NIO", "NIO"], ascending=False
                    ).head(20)
                    station_quality_order = natural_label_order(chart_data["Station"])
                    fig = px.bar(
                        chart_data,
                        x="% NIO",
                        y="Station",
                        orientation="h",
                        labels={"% NIO": "% NIO", "Station": "Station"},
                        title="Top stanowiska według % NIO",
                        color_discrete_sequence=[COLOR_SEQUENCE[1]],
                        custom_data=["Wszystkie", "OK", "NIO"],
                        category_orders={"Station": station_quality_order},
                    )
                    fig.update_traces(
                        hovertemplate=(
                            "Station: %{y}<br>"
                            "% NIO: %{x:.2f}%<br>"
                            "Wszystkie: %{customdata[0]}<br>"
                            "OK: %{customdata[1]}<br>"
                            "NIO: %{customdata[2]}<extra></extra>"
                        )
                    )
                    fig.update_yaxes(
                        categoryorder="array",
                        categoryarray=station_quality_order,
                        autorange="reversed",
                    )
                    fig = style_chart(fig, height=560)
                    st.plotly_chart(fig, width="stretch")
