# core.py
from __future__ import annotations
from dataclasses import dataclass
from collections import deque, defaultdict
from typing import List, Dict, Optional, Sequence, Tuple
import math
import numpy as np
import pandas as pd
import logging


# Thiết lập logging (in thông tin khi chạy)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    # vốn / sizing
    initial_cash: float
    sizing_method: str
    fraction: float
    fixed_amount: float
    lot_size: int
    allow_fractional: bool
    volatility_risk_pct: float
    atr_multiplier: float

    # trade rules
    stop_loss_pct: float
    take_profit_pct: float
    sell_fraction_on_signal: float
    max_sells_per_day: Optional[int]
    max_positions_per_day: int
    max_positions_in_portfolio: Optional[int]
    max_pct_per_ticker: float

    # execution / indicators / misc
    fees_per_order: float
    atr_period: int

    # optimize
    min_trades: int
    trade_penalty_mode: str



# Dataclass lưu 1 sự kiện giao dịch 
@dataclass
class TradeEvent:
    date: pd.Timestamp
    ticker: str
    type: str  # 'BUY' or 'SELL'
    price: float
    shares: float
    cash_after: float


# Xây lại các giao dịch theo quy tắc FIFO.
# book  = các lô mua còn mở.
# per_trade_df = danh sách giao dịch đã đóng.
def replay_and_pairs(events_df: pd.DataFrame, return_book: bool = False):

    book = defaultdict(deque)
    realized = []
    if events_df is None or events_df.empty:
        if return_book:
            return book, pd.DataFrame(realized)
        return pd.DataFrame(realized)

    for _, r in events_df.sort_values("Date").iterrows():
        t = r.get("Ticker")
        typ = str(r.get("Type")).upper() if r.get("Type") is not None else None
        if t is None or typ not in {"BUY", "SELL"}:
            continue
        price = float(r.get("Price") or 0.0)
        shares = float(r.get("Shares") or 0.0)
        if shares <= 0:
            continue
        if typ == "BUY":
            book[t].append({"date": r["Date"], "price": price, "shares": shares})
        else:
            remaining = shares
            dq = book.get(t, deque())
            while remaining > 0 and dq:
                lot = dq[0]
                take = min(remaining, lot["shares"])
                realized.append({
                    "Ticker": t,
                    "EntryDate": lot.get("date"),
                    "ExitDate": r["Date"],
                    "EntryPrice": lot.get("price"),
                    "ExitPrice": price,
                    "Shares": take,
                    "RealizedPNL": (price - lot.get("price")) * take,
                    "HoldingDays": (pd.to_datetime(r["Date"]) - pd.to_datetime(lot.get("date"))).days if lot.get("date") is not None else np.nan,
                })
                lot["shares"] -= take
                remaining -= take
                if lot["shares"] <= 0:
                    dq.popleft()

    per_trade_df = pd.DataFrame(realized)
    if return_book:
        return book, per_trade_df
    return per_trade_df

# Tính unrealized PnL và market value từ events và giá hiện tại
def compute_unrealized_from_events(events_df: pd.DataFrame,
                                   universe_prices: Dict[str, pd.DataFrame],
                                   market_date: pd.Timestamp):

    unrealized = {t: 0.0 for t in universe_prices}
    market_value = {t: 0.0 for t in universe_prices}

    book, _ = replay_and_pairs(events_df, return_book=True)

    for t in universe_prices.keys():
        dq = book.get(t, deque())
        if not dq:
            continue
        price = last_price_up_to(universe_prices.get(t), market_date)
        if np.isnan(price):
            continue
        mv = sum(l["shares"] * price for l in dq)
        upnl = sum((price - l["price"]) * l["shares"] for l in dq)
        market_value[t] = float(mv)
        unrealized[t] = float(upnl)

    return unrealized, market_value

# Tính metrics từ per-trade dataframe
def realized_metrics_from_trades(per_trade_df: pd.DataFrame) -> Dict[str, float]:

    if per_trade_df is None or per_trade_df.empty:
        return {"n_trades": 0, "win_rate": np.nan, "avg_pnl": np.nan, "profit_factor": np.nan}
    
    wins = per_trade_df[per_trade_df["RealizedPNL"] > 0]
    losses = per_trade_df[per_trade_df["RealizedPNL"] < 0]
    n = len(per_trade_df)
    win_rate = len(wins) / n if n > 0 else np.nan
    avg_pnl = per_trade_df["RealizedPNL"].mean()
    profit_factor = wins["RealizedPNL"].sum() / abs(losses["RealizedPNL"].sum()) if losses["RealizedPNL"].sum() != 0 else np.nan
    return {
        "n_trades": int(n),
        "win_rate": float(win_rate),
        "avg_realized_pnl": float(avg_pnl),
        "profit_factor": float(profit_factor) if not np.isnan(profit_factor) else np.nan,
    }

# Chuyển equity curve list -> dataframe
def to_equity_df(equity_curve: List[Tuple[pd.Timestamp, float]]) -> pd.DataFrame:

    df = pd.DataFrame(equity_curve, columns=["Date", "Equity"]).set_index("Date").sort_index()
    df.index = pd.to_datetime(df.index)
    return df


# Tính các thống kê returns/Sharpe/CAGR/MaxDD/Calmar
def compute_return_stats(equity_series: pd.Series, annual_rf: float = 0.05) -> Dict[str, float]:

    out = {}
    if equity_series is None or len(equity_series) < 2:
        out.update({"returns": pd.Series(dtype=float), "AnnVol": np.nan, "Sharpe": np.nan, "CAGR": np.nan, "MaxDrawdown": np.nan, "Calmar": np.nan})
        return out

    returns = equity_series.pct_change().dropna()
    out["returns"] = returns
    out["AnnVol"] = float(returns.std() * math.sqrt(252)) if len(returns) > 1 else np.nan

    rf_daily = annual_rf / 252
    excess = returns - rf_daily
    vol = excess.std()
    out["Sharpe"] = float((excess.mean() / vol) * math.sqrt(252)) if (vol and not np.isnan(vol)) else np.nan

    # CAGR
    try:
        start = float(equity_series.iloc[0])
        end = float(equity_series.iloc[-1])
        span_days = (equity_series.index[-1] - equity_series.index[0]).days
        years = span_days / 365.25
        out["CAGR"] = float((end / start) ** (1.0 / years) - 1.0) if (years > 0 and start > 0 and end > 0) else np.nan
    except Exception:
        out["CAGR"] = np.nan

    # Max drawdown
    try:
        cummax = equity_series.cummax()
        out["MaxDrawdown"] = float((equity_series / cummax - 1).min())
    except Exception:
        out["MaxDrawdown"] = np.nan

    out["Calmar"] = out["CAGR"] / abs(out["MaxDrawdown"]) if (not np.isnan(out["CAGR"]) and not np.isnan(out["MaxDrawdown"]) and out["MaxDrawdown"] < 0) else np.nan

    return out

# Tính các metrics portfolio từ equity_curve và per_trade_df
def compute_portfolio_metrics(equity_curve, per_trade_df: Optional[pd.DataFrame] = None) -> Dict[str, float]:

    if not equity_curve:
        return {}

    ec = to_equity_df(equity_curve)
    equity = ec["Equity"]


    stats = compute_return_stats(equity)
    returns = stats.get("returns")


    out = {
    "CAGR": float(stats.get("CAGR", np.nan)) if not np.isnan(stats.get("CAGR", np.nan)) else np.nan,
    "Sharpe": float(stats.get("Sharpe", np.nan)) if not np.isnan(stats.get("Sharpe", np.nan)) else np.nan,
    "AnnVol": float(stats.get("AnnVol", np.nan)) if not np.isnan(stats.get("AnnVol", np.nan)) else np.nan,
    "MaxDrawdown": float(stats.get("MaxDrawdown", np.nan)) if not np.isnan(stats.get("MaxDrawdown", np.nan)) else np.nan,
    "Calmar": float(stats.get("Calmar", np.nan)) if not np.isnan(stats.get("Calmar", np.nan)) else np.nan,
    }

    # Nếu có per-trade, thêm các metric realized
    if per_trade_df is not None and hasattr(per_trade_df, "empty") and not per_trade_df.empty:
        out.update(realized_metrics_from_trades(per_trade_df))

    return out


# Lấy giá mở cửa mới nhất tới ngày date 
def last_price_up_to(df: pd.DataFrame, date: pd.Timestamp) -> float:

    if df is None or len(df) == 0:
        return float("nan")

    # Lọc các ngày <= date
    df2 = df.loc[df.index <= date]

    if df2.empty:
        return float("nan")

    return float(df2["Open"].iloc[-1])
