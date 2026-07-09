from __future__ import annotations

import streamlit as st


def configure_page() -> None:
    """Configure Streamlit page metadata and inject shared CSS."""
    st.set_page_config(
        page_title="Analiza Inconso NIO",
        page_icon="",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        :root {
            --app-bg: #0e1117;
            --panel-bg: #262730;
            --panel-border: #3a3d49;
            --text-main: #f8fafc;
            --text-muted: #cbd5e1;
            --accent: #60a5fa;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: var(--app-bg);
            color: var(--text-main);
        }
        .block-container {
            max-width: 1400px;
            padding-top: 5.6rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: var(--panel-bg);
            border-right: 1px solid #565968;
        }
        [data-testid="stSidebar"] * {
            color: var(--text-main);
        }
        [data-testid="stSidebar"] hr,
        .section-divider {
            border: 0;
            border-top: 1px solid var(--panel-border);
            margin: 2rem 0;
        }
        .app-hero {
            margin-bottom: 3.4rem;
        }
        .app-title {
            display: flex;
            align-items: center;
            gap: 1.1rem;
            font-size: clamp(2.4rem, 5vw, 4.1rem);
            font-weight: 800;
            letter-spacing: 0;
            line-height: 1.05;
        }
        .hero-icon {
            font-size: clamp(2rem, 4vw, 3.4rem);
            line-height: 1;
        }
        .app-subtitle {
            margin-top: 1.4rem;
            font-size: 1.25rem;
            font-style: italic;
            color: var(--text-main);
        }
        .intro-block {
            margin: 0.5rem 0 2.6rem;
        }
        .intro-block h2 {
            font-size: 2rem;
            margin-bottom: 1.2rem;
        }
        .intro-block li {
            margin: 0.55rem 0;
            font-size: 1.05rem;
            font-weight: 650;
        }
        .upload-heading {
            margin-bottom: 0.7rem;
            font-weight: 700;
            color: var(--text-main);
        }
        [data-testid="stFileUploader"] section {
            background: var(--panel-bg);
            border: 1px solid var(--panel-bg);
            border-radius: 8px;
            min-height: 86px;
            padding: 1rem;
        }
        [data-testid="stFileUploader"] button {
            border-radius: 8px;
            border: 1px solid #475569;
            background: #111827;
            color: var(--text-main);
            padding: 0.75rem 1.2rem;
        }
        [data-testid="stTabs"] button {
            color: var(--text-muted);
        }
        [data-testid="stTabs"] button[aria-selected="true"] {
            color: var(--text-main);
        }
        div[data-baseweb="popover"] {
            max-height: calc(100vh - 1rem) !important;
            overflow-y: auto !important;
        }
        div[data-baseweb="popover"] [role="listbox"],
        div[data-baseweb="popover"] ul,
        div[data-baseweb="menu"] {
            max-height: min(240px, 45vh) !important;
            overflow-y: auto !important;
            overscroll-behavior: contain;
        }
        h1, h2, h3, h4, h5, h6, p, li, label, span {
            color: var(--text-main);
        }
        div[data-testid="stMetric"] {
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 1rem 1.05rem;
        }
        div[data-testid="stMetric"] label {
            color: var(--text-muted);
        }
        div[data-testid="stMetricValue"] {
            color: var(--text-main);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--panel-border);
            border-radius: 8px;
        }
        [data-testid="stAlert"] {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
