"""Screener strategy implementations adapted from stock-pipeline concepts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import pandas as pd

from config import DB_PATH
from fmp_api import (
    get_analyst_recommendations,
    get_historical_daily,
    get_insider_trading,
    get_key_metrics_ttm,
    get_profile,
    get_quote,
    get_ratios_ttm,
    get_stock_screener_universe,
    make_authorised_request,
)
from store import PersistentDict


@dataclass(frozen=True)
class StrategySpec:
    key: str
    title: str
    description: str
    run: Callable[[list[dict], bool, int], pd.DataFrame]


SnapshotProgressCallback = Callable[[int, int, str], None]


UNIVERSE_SOURCE_LABELS = {
    "watchlist": "Watchlist",
    "sp500": "S&P 500",
    "russell2000": "Russell 2000",
    "nasdaq100": "NASDAQ 100",
    "dowjones": "Dow Jones",
    "ftse100": "FTSE 100",
    "fmp_large_cap": "FMP Large-Cap Sample",
    "extra_symbols": "Extra symbols",
}


def get_universe_options() -> list[tuple[str, str]]:
    return [
        ("watchlist", UNIVERSE_SOURCE_LABELS["watchlist"]),
        ("sp500", UNIVERSE_SOURCE_LABELS["sp500"]),
        ("russell2000", UNIVERSE_SOURCE_LABELS["russell2000"]),
        ("nasdaq100", UNIVERSE_SOURCE_LABELS["nasdaq100"]),
        ("dowjones", UNIVERSE_SOURCE_LABELS["dowjones"]),
        ("ftse100", UNIVERSE_SOURCE_LABELS["ftse100"]),
        ("fmp_large_cap", UNIVERSE_SOURCE_LABELS["fmp_large_cap"]),
    ]


def _safe_float(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick_float(data: dict, keys: list[str]) -> float | None:
    for key in keys:
        if key in data:
            value = _safe_float(data.get(key))
            if value is not None:
                return value
    return None


def _as_percent(value: float | None) -> float | None:
    if value is None:
        return None
    if abs(value) <= 1.0:
        return value * 100
    return value


def _compute_daily_returns(closes: list[float]) -> list[float]:
    if len(closes) < 2:
        return []
    returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:]):
        if previous > 0:
            returns.append((current - previous) / previous)
    return returns


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _symbols_from_fmp_constituent_endpoint(endpoint: str) -> list[str]:
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}"
    payload = make_authorised_request(url)
    if not isinstance(payload, list):
        return []
    symbols: list[str] = []
    for item in payload:
        symbol = str(item.get("symbol", "")).strip().upper()
        if symbol:
            symbols.append(symbol)
    return symbols


def _symbols_from_wikipedia(url: str, symbol_candidates: list[str]) -> list[str]:
    try:
        tables = pd.read_html(url)
    except Exception:
        return []

    for table in tables:
        renamed = {str(column).strip().lower(): column for column in table.columns}
        for candidate in symbol_candidates:
            if candidate in renamed:
                symbol_col = renamed[candidate]
                values = table[symbol_col].dropna().astype(str).str.strip().str.upper().tolist()
                return [value for value in values if value and value != "NAN"]
    return []


def _fetch_source_symbols(source_key: str, fmp_large_cap_limit: int) -> list[str]:
    if source_key == "watchlist":
        db = PersistentDict(DB_PATH)
        watchlist = db.get("watchlist", {})
        return [symbol.upper() for symbol in watchlist.keys()]

    if source_key == "sp500":
        return _symbols_from_fmp_constituent_endpoint("sp500_constituent")

    if source_key == "russell2000":
        return _symbols_from_fmp_constituent_endpoint("russell2000_constituent")

    if source_key == "dowjones":
        return _symbols_from_fmp_constituent_endpoint("dowjones_constituent")

    if source_key == "nasdaq100":
        symbols = _symbols_from_wikipedia(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            symbol_candidates=["ticker", "ticker symbol"],
        )
        if symbols:
            return symbols
        return _symbols_from_fmp_constituent_endpoint("nasdaq_constituent")

    if source_key == "ftse100":
        symbols = _symbols_from_wikipedia(
            "https://en.wikipedia.org/wiki/FTSE_100_Index",
            symbol_candidates=["epic", "ticker", "symbol"],
        )
        if symbols:
            return symbols
        return _symbols_from_fmp_constituent_endpoint("ftse100_constituent")

    if source_key == "fmp_large_cap":
        rows = get_stock_screener_universe(limit=fmp_large_cap_limit, exchange="NASDAQ,NYSE")
        return [str(item.get("symbol", "")).strip().upper() for item in rows if item.get("symbol")]

    return []


def build_symbol_universe(
    max_symbols: int,
    selected_sources: list[str],
    extra_symbols: str = "",
) -> tuple[list[str], dict[str, list[str]], dict[str, int]]:
    fetched_by_source: dict[str, list[str]] = {}

    for source in selected_sources:
        fetched_by_source[source] = _fetch_source_symbols(source, fmp_large_cap_limit=max_symbols)

    extra_list: list[str] = []
    if extra_symbols.strip():
        for raw in extra_symbols.split(","):
            symbol = raw.strip().upper()
            if symbol:
                extra_list.append(symbol)
    fetched_by_source["extra_symbols"] = extra_list

    raw_counts = {source: len(symbols) for source, symbols in fetched_by_source.items()}

    final_symbols: list[str] = []
    included_by_source: dict[str, list[str]] = {source: [] for source in fetched_by_source.keys()}
    seen = set()

    for source in selected_sources + ["extra_symbols"]:
        symbols = fetched_by_source.get(source, [])
        for symbol in symbols:
            if symbol in seen:
                continue
            seen.add(symbol)
            final_symbols.append(symbol)
            included_by_source[source].append(symbol)
            if len(final_symbols) >= max_symbols:
                break
        if len(final_symbols) >= max_symbols:
            break

    fallback = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK.B", "JPM", "XOM"]
    if not final_symbols:
        final_symbols = fallback[:max_symbols]
        included_by_source = {"fallback": final_symbols.copy()}
        raw_counts = {"fallback": len(final_symbols)}

    return final_symbols, included_by_source, raw_counts


def load_snapshots(symbols: list[str], progress_callback: SnapshotProgressCallback | None = None) -> list[dict]:
    snapshots: list[dict] = []
    total = len(symbols)

    for index, symbol in enumerate(symbols, start=1):
        profile = get_profile(symbol) or {}
        quote = get_quote(symbol) or {}
        ratios = get_ratios_ttm(symbol) or {}
        metrics = get_key_metrics_ttm(symbol) or {}
        history = get_historical_daily(symbol, timeseries=260) or []
        analyst = get_analyst_recommendations(symbol, limit=60) or []
        insider = get_insider_trading(symbol, limit=100) or []

        closes = [
            _safe_float(candle.get("close"))
            for candle in reversed(history)
            if _safe_float(candle.get("close")) is not None
        ]
        highs = [
            _safe_float(candle.get("high"))
            for candle in reversed(history)
            if _safe_float(candle.get("high")) is not None
        ]
        lows = [
            _safe_float(candle.get("low"))
            for candle in reversed(history)
            if _safe_float(candle.get("low")) is not None
        ]

        roe = _pick_float(ratios, ["returnOnEquityTTM", "roeTTM"])
        operating_margin = _pick_float(ratios, ["operatingProfitMarginTTM", "operatingMarginTTM"])
        profit_margin = _pick_float(ratios, ["netProfitMarginTTM", "netProfitMargin", "profitMarginTTM"])

        snapshot = {
            "symbol": symbol,
            "company_name": profile.get("companyName") or quote.get("name") or symbol,
            "sector": profile.get("sector") or "Unknown",
            "current_price": _pick_float(quote, ["price"]),
            "market_cap": _pick_float(quote, ["marketCap"]) or _pick_float(profile, ["mktCap"]),
            "pe_ratio": _pick_float(ratios, ["peRatioTTM", "peRatio"]),
            "pb_ratio": _pick_float(ratios, ["priceToBookRatioTTM", "priceToBookRatio"]),
            "peg_ratio": _pick_float(ratios, ["pegRatioTTM", "pegRatio"]),
            "ev_ebitda": _pick_float(ratios, ["enterpriseValueOverEBITDATTM", "evToEbitdaTTM", "evToEbitda"]),
            "fcf_yield": _pick_float(metrics, ["freeCashFlowYieldTTM", "freeCashFlowYield"]),
            "roe": _as_percent(roe),
            "profit_margin": _as_percent(profit_margin),
            "operating_margin": _as_percent(operating_margin),
            "debt_to_equity": _pick_float(ratios, ["debtEquityRatioTTM", "debtToEquityTTM", "debtToEquity"]),
            "current_ratio": _pick_float(ratios, ["currentRatioTTM", "currentRatio"]),
            "quick_ratio": _pick_float(ratios, ["quickRatioTTM", "quickRatio"]),
            "revenue_growth": _as_percent(_pick_float(ratios, ["revenueGrowthTTM", "revenueGrowth"])),
            "eps_growth": _as_percent(_pick_float(ratios, ["epsGrowthTTM", "epsGrowth"])),
            "roa": _as_percent(_pick_float(ratios, ["returnOnAssetsTTM", "roaTTM"])),
            "beta": _pick_float(profile, ["beta"]),
            "dividend_yield": _as_percent(_pick_float(ratios, ["dividendYieldTTM", "dividendYield"])),
            "payout_ratio": _pick_float(ratios, ["payoutRatioTTM", "payoutRatio"]),
            "history_closes": [value for value in closes if value is not None],
            "history_highs": [value for value in highs if value is not None],
            "history_lows": [value for value in lows if value is not None],
            "analyst": analyst,
            "insider": insider,
        }
        snapshots.append(snapshot)

        if progress_callback is not None:
            progress_callback(index, total, symbol)

    return snapshots


def _build_dataframe(rows: list[dict], sort_by: str, ascending: bool, only_meets: bool, limit: int) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)
    if only_meets and "meets_threshold" in frame.columns:
        frame = frame[frame["meets_threshold"] == True]  # noqa: E712
    frame = frame.sort_values(sort_by, ascending=ascending)
    return frame.head(limit)


def _strategy_pe_ratio(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        pe = row.get("pe_ratio")
        if pe is None or pe <= 0:
            continue
        meets = pe <= 10
        rows.append({**row, "score": pe, "meets_threshold": meets, "reason": f"P/E = {pe:.2f}"})
    return _build_dataframe(rows, "score", True, only_meets, limit)


def _strategy_price_to_book(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        pb = row.get("pb_ratio")
        if pb is None or pb <= 0:
            continue
        meets = pb <= 1.2
        rows.append({**row, "score": pb, "meets_threshold": meets, "reason": f"P/B = {pb:.2f}"})
    return _build_dataframe(rows, "score", True, only_meets, limit)


def _strategy_peg(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        peg = row.get("peg_ratio")
        if peg is None or peg <= 0:
            continue
        meets = peg <= 1.0
        rows.append({**row, "score": peg, "meets_threshold": meets, "reason": f"PEG = {peg:.2f}"})
    return _build_dataframe(rows, "score", True, only_meets, limit)


def _strategy_fcf_yield(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        fcf_yield = row.get("fcf_yield")
        if fcf_yield is None:
            continue
        meets = fcf_yield >= 8
        rows.append(
            {
                **row,
                "score": fcf_yield,
                "meets_threshold": meets,
                "reason": f"FCF Yield = {fcf_yield:.2f}%",
            }
        )
    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_quality(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        score = 0
        metrics_present = 0

        roe = row.get("roe")
        if roe is not None:
            metrics_present += 1
            if roe > 15:
                score += 3
            elif roe > 10:
                score += 1

        debt_to_equity = row.get("debt_to_equity")
        if debt_to_equity is not None:
            metrics_present += 1
            if debt_to_equity < 0.5:
                score += 2
            elif debt_to_equity < 1.0:
                score += 1

        profit_margin = row.get("profit_margin")
        if profit_margin is not None:
            metrics_present += 1
            if profit_margin > 20:
                score += 2
            elif profit_margin > 10:
                score += 1

        operating_margin = row.get("operating_margin")
        if operating_margin is not None:
            metrics_present += 1
            if operating_margin > 15:
                score += 2
            elif operating_margin > 10:
                score += 1

        ev_ebitda = row.get("ev_ebitda")
        if ev_ebitda is not None:
            metrics_present += 1
            if ev_ebitda < 10:
                score += 1

        if metrics_present < 3:
            continue

        meets = score >= 6
        rows.append({**row, "score": float(score), "meets_threshold": meets, "reason": f"Quality score {score}/10"})

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_enhanced_quality(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        score = 0.0

        roe = row.get("roe")
        if roe is not None:
            if roe >= 30:
                score += 25
            elif roe >= 25:
                score += 22
            elif roe >= 20:
                score += 19
            elif roe >= 15:
                score += 15
            elif roe >= 12:
                score += 12
            elif roe >= 10:
                score += 8
            elif roe >= 8:
                score += 5

        operating_margin = row.get("operating_margin")
        if operating_margin is not None:
            if operating_margin >= 30:
                score += 12
            elif operating_margin >= 20:
                score += 8
            elif operating_margin >= 15:
                score += 6
            elif operating_margin >= 10:
                score += 4

        profit_margin = row.get("profit_margin")
        if profit_margin is not None:
            if profit_margin >= 25:
                score += 8
            elif profit_margin >= 20:
                score += 7
            elif profit_margin >= 15:
                score += 5
            elif profit_margin >= 10:
                score += 3

        debt_to_equity = row.get("debt_to_equity")
        if debt_to_equity is not None:
            if debt_to_equity <= 0.1:
                score += 10
            elif debt_to_equity <= 0.3:
                score += 6
            elif debt_to_equity <= 0.5:
                score += 4
            elif debt_to_equity <= 0.8:
                score += 2

        current_ratio = row.get("current_ratio")
        if current_ratio is not None:
            if current_ratio >= 3.0:
                score += 8
            elif current_ratio >= 2.5:
                score += 7
            elif current_ratio >= 2.0:
                score += 5
            elif current_ratio >= 1.5:
                score += 3
            elif current_ratio >= 1.2:
                score += 1

        quick_ratio = row.get("quick_ratio")
        if quick_ratio is not None:
            if quick_ratio >= 1.5:
                score += 4
            elif quick_ratio >= 1.2:
                score += 3
            elif quick_ratio >= 1.0:
                score += 2

        revenue_growth = row.get("revenue_growth")
        if revenue_growth is not None:
            if revenue_growth >= 20:
                score += 8
            elif revenue_growth >= 15:
                score += 6
            elif revenue_growth >= 10:
                score += 4
            elif revenue_growth >= 5:
                score += 2

        eps_growth = row.get("eps_growth")
        if eps_growth is not None:
            if eps_growth >= 25:
                score += 8
            elif eps_growth >= 20:
                score += 6
            elif eps_growth >= 15:
                score += 4
            elif eps_growth >= 10:
                score += 2

        roa = row.get("roa")
        if roa is not None:
            if roa >= 15:
                score += 5
            elif roa >= 12:
                score += 4
            elif roa >= 8:
                score += 3
            elif roa >= 5:
                score += 2

        dividend_yield = row.get("dividend_yield")
        payout_ratio = row.get("payout_ratio")
        if dividend_yield is not None and dividend_yield > 0:
            if payout_ratio is not None and 0 < payout_ratio < 0.6:
                score += 4
            elif payout_ratio is not None and 0.6 <= payout_ratio < 0.8:
                score += 2
            else:
                score += 1

        meets = score >= 50
        rows.append({**row, "score": score, "meets_threshold": meets, "reason": f"Enhanced quality {score:.1f}/100"})

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_momentum(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        closes = row.get("history_closes", [])
        if len(closes) < 90:
            continue

        skip_days = min(21, len(closes) // 7)
        if len(closes) <= skip_days + 1:
            continue

        reference_price = closes[-(skip_days + 1)]

        six_month_return = None
        six_month_idx = 126 + skip_days
        if len(closes) > six_month_idx:
            six_month_price = closes[-(six_month_idx + 1)]
            if six_month_price > 0:
                six_month_return = ((reference_price - six_month_price) / six_month_price) * 100

        three_month_return = None
        three_month_idx = 63 + skip_days
        if len(closes) > three_month_idx:
            three_month_price = closes[-(three_month_idx + 1)]
            if three_month_price > 0:
                three_month_return = ((reference_price - three_month_price) / three_month_price) * 100

        if six_month_return is None and three_month_return is None:
            continue

        if six_month_return is not None and three_month_return is not None:
            score = six_month_return * 0.6 + three_month_return * 0.4
        else:
            score = six_month_return if six_month_return is not None else three_month_return

        meets = score >= 15
        rows.append({**row, "score": score, "six_month_return": six_month_return, "three_month_return": three_month_return, "meets_threshold": meets, "reason": f"Momentum score {score:.1f}%"})

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_sharpe(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    risk_free_rate = 0.04
    for row in data:
        closes = row.get("history_closes", [])
        daily_returns = _compute_daily_returns(closes)
        if len(daily_returns) < 30:
            continue

        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((item - mean_return) ** 2 for item in daily_returns) / (len(daily_returns) - 1)
        volatility = variance ** 0.5
        if volatility == 0:
            continue

        annualized_return = mean_return * 252
        annualized_volatility = volatility * (252 ** 0.5)
        sharpe = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility > 0 else None
        if sharpe is None:
            continue

        meets = sharpe >= 1.0
        rows.append({**row, "score": sharpe, "annualized_return": annualized_return * 100, "annualized_volatility": annualized_volatility * 100, "meets_threshold": meets, "reason": f"Sharpe {sharpe:.2f}"})

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_52_week_lows(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        lows = row.get("history_lows", [])
        highs = row.get("history_highs", [])
        closes = row.get("history_closes", [])
        if not lows or not highs or not closes:
            continue

        low_52 = min(lows)
        high_52 = max(highs)
        current = closes[-1]
        if low_52 <= 0 or high_52 <= 0:
            continue

        pct_above_low = ((current - low_52) / low_52) * 100
        pct_off_high = ((high_52 - current) / high_52) * 100
        score = max(0.0, 100 - (pct_above_low * 2))
        meets = pct_above_low <= 20

        rows.append(
            {
                **row,
                "score": score,
                "52_week_low": low_52,
                "52_week_high": high_52,
                "pct_above_low": pct_above_low,
                "pct_off_high": pct_off_high,
                "meets_threshold": meets,
                "reason": f"{pct_above_low:.2f}% above 52-week low",
            }
        )

    return _build_dataframe(rows, "pct_above_low", True, only_meets, limit)


def _strategy_historic_value(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []

    for row in data:
        pe = row.get("pe_ratio")
        pb = row.get("pb_ratio")
        ev_ebitda = row.get("ev_ebitda")
        market_cap = row.get("market_cap")

        if pe is None or pe <= 0 or pe > 50:
            continue
        if market_cap is None or market_cap < 500_000_000:
            continue
        debt_to_equity = row.get("debt_to_equity")
        if debt_to_equity is not None and debt_to_equity > 3.0:
            continue

        sector = row.get("sector", "")
        valuation_score = 0.0
        metrics_count = 0

        if pe is not None:
            if "Technology" in sector:
                historic_pe = max(pe * 1.4, 22)
            elif "Utilities" in sector or "Consumer Staples" in sector:
                historic_pe = max(pe * 1.2, 16)
            elif "Financial" in sector:
                historic_pe = max(pe * 1.15, 14)
            else:
                historic_pe = max(pe * 1.3, 18)

            pe_discount = (historic_pe - pe) / historic_pe
            if pe_discount > 0.25:
                valuation_score += 25
            elif pe_discount > 0.15:
                valuation_score += 20
            elif pe_discount > 0.10:
                valuation_score += 15
            elif pe_discount > 0.05:
                valuation_score += 8
            metrics_count += 1

        if pb is not None and pb > 0:
            roe = row.get("roe") or 12
            historic_pb = max((roe / 100) * 8, pb * 1.2)
            pb_discount = (historic_pb - pb) / historic_pb
            if pb_discount > 0.30:
                valuation_score += 15
            elif pb_discount > 0.20:
                valuation_score += 12
            elif pb_discount > 0.10:
                valuation_score += 8
            elif pb_discount > 0.05:
                valuation_score += 4
            metrics_count += 1

        if ev_ebitda is not None and ev_ebitda > 0:
            if "Technology" in sector:
                historic_ev = max(ev_ebitda * 1.3, 20)
            elif "Utilities" in sector:
                historic_ev = max(ev_ebitda * 1.15, 12)
            else:
                historic_ev = max(ev_ebitda * 1.25, 15)

            ev_discount = (historic_ev - ev_ebitda) / historic_ev
            if ev_discount > 0.25:
                valuation_score += 10
            elif ev_discount > 0.15:
                valuation_score += 7
            elif ev_discount > 0.10:
                valuation_score += 5
            elif ev_discount > 0.05:
                valuation_score += 3
            metrics_count += 1

        if metrics_count < 2:
            continue

        quality_score = 0.0
        if debt_to_equity is not None:
            if debt_to_equity < 0.3:
                quality_score += 20
            elif debt_to_equity < 0.6:
                quality_score += 15
            elif debt_to_equity < 1.0:
                quality_score += 10
            elif debt_to_equity < 1.5:
                quality_score += 5

        roe = row.get("roe")
        profit_margin = row.get("profit_margin")
        if roe is not None:
            if roe > 15:
                quality_score += 8
            elif roe > 10:
                quality_score += 5
            elif roe > 5:
                quality_score += 2
        if profit_margin is not None:
            if profit_margin > 15:
                quality_score += 7
            elif profit_margin > 8:
                quality_score += 4
            elif profit_margin > 3:
                quality_score += 2

        market_score = 0.0
        if market_cap > 10_000_000_000:
            market_score += 15
        elif market_cap > 2_000_000_000:
            market_score += 12
        elif market_cap > 1_000_000_000:
            market_score += 8
        else:
            market_score += 5

        beta = row.get("beta")
        if beta is not None:
            if 0.8 <= beta <= 1.2:
                market_score += 10
            elif 0.6 <= beta <= 1.4:
                market_score += 7
            elif beta < 2.0:
                market_score += 3

        total_score = (valuation_score * 0.40) + (quality_score * 0.35) + (market_score * 0.25)
        meets = total_score >= 60

        rows.append({**row, "score": total_score, "valuation_score": valuation_score, "quality_score": quality_score, "market_score": market_score, "meets_threshold": meets, "reason": f"Historic value score {total_score:.1f}/100"})

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _strategy_insider_buying(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    for row in data:
        trades = row.get("insider") or []
        if not trades:
            continue

        buy_count = 0
        sell_count = 0
        buy_value = 0.0
        sell_value = 0.0
        unique_insiders = set()

        for trade in trades:
            unique_insiders.add(str(trade.get("reportingName", "")))
            acquisition = str(trade.get("acquisitionOrDisposition", "")).upper()
            transaction_type = str(trade.get("transactionType", "")).upper()
            shares = _safe_float(trade.get("securitiesTransacted")) or 0
            price = _safe_float(trade.get("price")) or 0
            value = shares * price

            if acquisition == "A" and ("PURCHASE" in transaction_type or "BUY" in transaction_type) and price > 0:
                buy_count += 1
                buy_value += value
            elif acquisition == "D" and ("SALE" in transaction_type or "SELL" in transaction_type):
                sell_count += 1
                sell_value += value

        if buy_count == 0:
            score = 0.0
        else:
            activity_score = min(40.0, buy_count * 10)
            acceleration_score = 0.0
            recent_cutoff = datetime.utcnow() - timedelta(days=30)
            recent_trades = 0
            for trade in trades:
                trade_date = _parse_date(trade.get("transactionDate"))
                if trade_date and trade_date >= recent_cutoff:
                    recent_trades += 1
            if recent_trades >= 2:
                acceleration_score = min(25.0, recent_trades * 4)

            net_millions = max(0.0, (buy_value - sell_value) / 1_000_000)
            technical_proxy_score = min(35.0, net_millions * 5 + min(10.0, len(unique_insiders) * 2))
            score = min(100.0, activity_score + acceleration_score + technical_proxy_score)

        meets = score >= 65
        rows.append(
            {
                **row,
                "score": score,
                "buy_trades": buy_count,
                "sell_trades": sell_count,
                "buy_value": buy_value,
                "sell_value": sell_value,
                "unique_insiders": len(unique_insiders),
                "meets_threshold": meets,
                "reason": f"Insider score {score:.1f}/100 ({buy_count} buys, {sell_count} sells)",
            }
        )

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _grade_to_score(grade: str) -> int:
    normalized = grade.strip().lower()
    mapping = {
        "strong buy": 5,
        "buy": 4,
        "overweight": 4,
        "outperform": 4,
        "hold": 3,
        "neutral": 3,
        "sell": 2,
        "underperform": 2,
        "strong sell": 1,
    }
    return mapping.get(normalized, 3)


def _strategy_analyst_sentiment(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    rows = []
    recent_cutoff = datetime.utcnow() - timedelta(days=90)

    for row in data:
        recommendations = row.get("analyst") or []
        if not recommendations:
            continue

        upgrades = 0
        downgrades = 0
        activity = 0

        for entry in recommendations:
            entry_date = _parse_date(entry.get("publishedDate") or entry.get("date"))
            if entry_date and entry_date < recent_cutoff:
                continue

            new_grade = _grade_to_score(str(entry.get("newGrade", "")))
            prev_grade = _grade_to_score(str(entry.get("previousGrade", "")))
            activity += 1
            if new_grade > prev_grade:
                upgrades += 1
            elif new_grade < prev_grade:
                downgrades += 1

        if activity == 0:
            continue

        upgrade_ratio = upgrades / max(1, upgrades + downgrades)
        rating_score = min(100.0, (upgrade_ratio * 80.0) + min(20.0, max(0, upgrades - downgrades) * 5.0))
        coverage_score = min(100.0, activity * 4.0)
        score = (rating_score * 0.75) + (coverage_score * 0.25)

        meets = score >= 60
        rows.append(
            {
                **row,
                "score": score,
                "upgrades": upgrades,
                "downgrades": downgrades,
                "analyst_activity": activity,
                "meets_threshold": meets,
                "reason": f"Analyst momentum {score:.1f}/100",
            }
        )

    return _build_dataframe(rows, "score", False, only_meets, limit)


def _normalize_value_score(row: dict) -> float | None:
    values = []
    pe = row.get("pe_ratio")
    if pe and 0 < pe < 100:
        values.append(max(0.0, min(100.0, 100 - (pe - 5) * 2.2)))
    pb = row.get("pb_ratio")
    if pb and 0 < pb < 20:
        values.append(max(0.0, min(100.0, 100 - (pb - 0.5) * 22.0)))
    fcf = row.get("fcf_yield")
    if fcf is not None:
        values.append(max(0.0, min(100.0, fcf * 10.0)))
    ev = row.get("ev_ebitda")
    if ev and 0 < ev < 50:
        values.append(max(0.0, min(100.0, 100 - (ev - 3) * 5.8)))
    return sum(values) / len(values) if values else None


def _normalize_growth_score(row: dict) -> float | None:
    values = []
    rev = row.get("revenue_growth")
    if rev is not None:
        values.append(max(0.0, min(100.0, 50 + rev * 1.67)))
    eps = row.get("eps_growth")
    if eps is not None:
        values.append(max(0.0, min(100.0, 50 + eps * 1.67)))
    return sum(values) / len(values) if values else None


def _normalize_momentum_score(row: dict) -> float | None:
    closes = row.get("history_closes", [])
    if len(closes) < 63:
        return None
    current = closes[-1]
    values = []
    if len(closes) >= 126 and closes[-126] > 0:
        sixm = ((current - closes[-126]) / closes[-126]) * 100
        values.append(max(0.0, min(100.0, 50 + sixm * 2.5)))
    if closes[-63] > 0:
        threem = ((current - closes[-63]) / closes[-63]) * 100
        values.append(max(0.0, min(100.0, 50 + threem * 2.5)))
    returns = _compute_daily_returns(closes[-60:])
    if returns:
        up_days = len([item for item in returns if item > 0])
        values.append((up_days / len(returns)) * 100)
    return sum(values) / len(values) if values else None


def _strategy_composite_score(data: list[dict], only_meets: bool, limit: int) -> pd.DataFrame:
    quality_df = _strategy_enhanced_quality(data, only_meets=False, limit=len(data) or 1)
    quality_lookup = {item["symbol"]: item["score"] for _, item in quality_df.iterrows()} if not quality_df.empty else {}

    analyst_df = _strategy_analyst_sentiment(data, only_meets=False, limit=len(data) or 1)
    analyst_lookup = {item["symbol"]: item["score"] for _, item in analyst_df.iterrows()} if not analyst_df.empty else {}

    lows_df = _strategy_52_week_lows(data, only_meets=False, limit=len(data) or 1)
    technical_lookup = {item["symbol"]: item["score"] for _, item in lows_df.iterrows()} if not lows_df.empty else {}

    rows = []
    for row in data:
        factor_scores = {
            "value": _normalize_value_score(row),
            "quality": quality_lookup.get(row["symbol"]),
            "growth": _normalize_growth_score(row),
            "momentum": _normalize_momentum_score(row),
            "analyst": analyst_lookup.get(row["symbol"]),
            "technical": technical_lookup.get(row["symbol"]),
        }

        weights = {
            "value": 0.25,
            "quality": 0.25,
            "growth": 0.15,
            "momentum": 0.15,
            "analyst": 0.10,
            "technical": 0.10,
        }

        valid = [name for name, value in factor_scores.items() if value is not None]
        if len(valid) < 3:
            continue

        total_weight = sum(weights[name] for name in valid)
        score = sum((factor_scores[name] or 0) * weights[name] for name in valid) / total_weight
        meets = score >= 65

        rows.append(
            {
                **row,
                "score": score,
                "factor_count": len(valid),
                "meets_threshold": meets,
                "reason": f"Composite score {score:.1f}/100 across {len(valid)} factors",
            }
        )

    return _build_dataframe(rows, "score", False, only_meets, limit)


def get_strategy_specs() -> list[StrategySpec]:
    return [
        StrategySpec("pe_ratio", "P/E Ratio", "Finds lower-valuation stocks by ranking Price/Earnings (score = P/E, lower is better). Threshold highlights P/E <= 10.", _strategy_pe_ratio),
        StrategySpec("price_to_book", "Price-to-Book", "Screens for companies trading close to book value (score = P/B, lower is better). Threshold highlights P/B <= 1.2.", _strategy_price_to_book),
        StrategySpec("peg_ratio", "PEG Ratio", "Compares valuation to growth via PEG (score = PEG, lower is better). Threshold highlights PEG <= 1.0.", _strategy_peg),
        StrategySpec("free_cash_flow_yield", "FCF Yield", "Ranks stocks by free cash flow yield (score = FCF yield %, higher is better). Threshold highlights FCF yield >= 8%.", _strategy_fcf_yield),
        StrategySpec("quality", "Quality", "Simple financial-strength model combining ROE, leverage, margins and EV/EBITDA (score 0-10, higher is better; threshold >= 6).", _strategy_quality),
        StrategySpec("enhanced_quality", "Enhanced Quality", "Expanded quality framework across profitability, leverage/liquidity and growth factors (score 0-100, higher is better; threshold >= 50).", _strategy_enhanced_quality),
        StrategySpec("momentum", "Momentum", "Uses weighted 6-month and 3-month returns while skipping the latest month (score in %, higher is better; threshold >= 15%).", _strategy_momentum),
        StrategySpec("sharpe_ratio", "Sharpe Ratio", "Measures risk-adjusted return using annualized return vs volatility (score = Sharpe ratio, higher is better; threshold >= 1.0).", _strategy_sharpe),
        StrategySpec("fifty_two_week_lows", "52-Week Lows", "Finds stocks close to yearly lows (score 0-100 from proximity to low; threshold highlights <= 20% above 52-week low).", _strategy_52_week_lows),
        StrategySpec("historic_value", "Historic Value", "Blends valuation discount, quality and market-structure checks into a mean-reversion score (0-100, higher is better; threshold >= 60).", _strategy_historic_value),
        StrategySpec("insider_buying", "Insider Buying", "Looks for meaningful insider purchase activity and acceleration patterns (score 0-100, higher is better; threshold >= 65).", _strategy_insider_buying),
        StrategySpec("analyst_sentiment_momentum", "Analyst Sentiment Momentum", "Evaluates upgrade/downgrade momentum and analyst activity intensity (score 0-100, higher is better; threshold >= 60).", _strategy_analyst_sentiment),
        StrategySpec("composite_score", "Composite Score", "Weighted blend of value, quality, growth, momentum, analyst and technical factors (score 0-100, higher is better; threshold >= 65).", _strategy_composite_score),
    ]
