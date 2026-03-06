"""screener.py — Streamlit page for multi-strategy stock screening tabs."""

from __future__ import annotations

import streamlit as st

from screeners.strategies import (
    UNIVERSE_SOURCE_LABELS,
    build_symbol_universe,
    get_strategy_specs,
    get_universe_options,
    load_snapshots,
)


DEFAULT_LIMIT = 25


def _format_universe_symbols(symbols: list[str]) -> str:
    if not symbols:
        return "(none)"
    return ", ".join(symbols)


def _prepare_results_for_display(results):
    preferred_order = [
        "symbol",
        "company_name",
        "score",
        "reason",
        "sector",
        "current_price",
        "market_cap",
    ]
    ordered = [column for column in preferred_order if column in results.columns]
    ordered += [column for column in results.columns if column not in ordered]
    return results[ordered]


def render_screener():
    st.title("Stock Screeners")
    st.caption("Strategies adapted from the imported stock-pipeline reference, integrated directly into this app.")

    options = get_universe_options()
    option_keys = [key for key, _ in options]
    option_labels = {key: label for key, label in options}

    cols = st.columns([1.3, 1, 2])
    with cols[0]:
        max_symbols = st.slider(
            "Universe size (max symbols scanned)",
            min_value=10,
            max_value=400,
            value=100,
            step=5,
            help="Maximum number of unique symbols included after combining selected universe sources and extra symbols.",
        )
    with cols[1]:
        per_tab_limit = st.slider("Rows per tab", min_value=10, max_value=100, value=DEFAULT_LIMIT, step=5)
    with cols[2]:
        extra_symbols = st.text_input("Extra symbols (comma-separated)", value="")

    selected_sources = st.multiselect(
        "Universe sources",
        options=option_keys,
        default=["watchlist", "sp500"],
        format_func=lambda key: option_labels.get(key, key),
    )

    only_meets = st.checkbox("Only show stocks meeting each strategy threshold", value=True)

    refresh_clicked = st.button("Run Screeners", type="primary")

    if refresh_clicked or "screener_snapshots" not in st.session_state:
        symbols, included_by_source, raw_counts = build_symbol_universe(
            max_symbols=max_symbols,
            selected_sources=selected_sources,
            extra_symbols=extra_symbols,
        )

        progress = st.progress(0, text=f"Loading market data: 0/{len(symbols)} symbols")
        status_text = st.empty()

        def on_progress(loaded: int, total: int, symbol: str):
            ratio = (loaded / total) if total else 1.0
            progress.progress(ratio, text=f"Loading market data: {loaded}/{total} symbols")
            status_text.caption(f"Last loaded: {symbol}")

        with st.spinner("Loading market data and building strategy inputs..."):
            snapshots = load_snapshots(symbols, progress_callback=on_progress)

        progress.progress(1.0, text=f"Loading complete: {len(symbols)}/{len(symbols)} symbols")
        status_text.caption("Snapshot load complete.")

        st.session_state["screener_symbols"] = symbols
        st.session_state["screener_snapshots"] = snapshots
        st.session_state["screener_universe_breakdown"] = included_by_source
        st.session_state["screener_universe_raw_counts"] = raw_counts
        st.session_state["screener_selected_sources"] = selected_sources

    symbols = st.session_state.get("screener_symbols", [])
    snapshots = st.session_state.get("screener_snapshots", [])
    included_by_source = st.session_state.get("screener_universe_breakdown", {})
    raw_counts = st.session_state.get("screener_universe_raw_counts", {})

    if not snapshots:
        st.info("No screener data available yet. Click 'Run Screeners' to load data.")
        return

    st.write(f"Universe loaded: {len(symbols)} symbols")
    st.caption("Universe size is a hard cap on the final deduplicated symbol list used for this run.")

    with st.expander("Universe contents", expanded=False):
        if included_by_source:
            for source, source_symbols in included_by_source.items():
                source_label = UNIVERSE_SOURCE_LABELS.get(source, source.replace("_", " ").title())
                fetched_count = raw_counts.get(source, len(source_symbols))
                st.markdown(f"**{source_label}** — included {len(source_symbols)} (fetched {fetched_count})")
                st.caption(_format_universe_symbols(source_symbols))
        st.markdown("**Final symbol list used by all tabs**")
        st.caption(_format_universe_symbols(symbols))

    strategies = get_strategy_specs()
    tabs = st.tabs([strategy.title for strategy in strategies])

    for tab, strategy in zip(tabs, strategies):
        with tab:
            st.markdown(f"**What this strategy screens for:** {strategy.description}")
            results = strategy.run(snapshots, only_meets=only_meets, limit=per_tab_limit)
            if results.empty:
                st.info("No matching results for current filters and data availability.")
            else:
                display_results = _prepare_results_for_display(results)
                st.dataframe(display_results, use_container_width=True, hide_index=True)
