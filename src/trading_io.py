# trading_io.py
import os
import tempfile
import json
import logging
from typing import Optional, Dict, Sequence, List, Tuple
import pandas as pd
from core import logger, TradeEvent
import numpy as np



# Ghi file hỗ trợ csv và json
def atomic_write(path: str, obj=None, df: Optional[pd.DataFrame]=None, fmt: Optional[str]=None) -> None:

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    dirpath = os.path.dirname(path) or "."
    if fmt is None:
        fmt = "csv" if df is not None else "json"

    fd, tmp = tempfile.mkstemp(dir=dirpath, prefix="tmp_write_", suffix=".tmp")
    os.close(fd)
    try:
        if fmt == "csv":
            if df is None:
                raise ValueError("df must be provided for csv")
            df.to_csv(tmp, index=False)
        elif fmt == "json":
            if obj is None:
                raise ValueError("obj must be provided for json")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2)
        else:
            raise ValueError("Unknown fmt")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass



# Đọc file JSON
def atomic_read_json(path: str):

    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to read JSON at %s", path)
        return None
    
# Lưu cấu hình SMA theo từng ticker
def save_per_ticker_params(per_ticker_params: Dict[str, Sequence[int]], path: str) -> None:

    serial = {t: [int(p[0]), int(p[1])] for t, p in per_ticker_params.items()}
    atomic_write(obj = serial, path = path, fmt = 'json')
    logger.info("Saved per-ticker params to %s", path)

# Tải cấu hình SMA từ file nếu có
def load_per_ticker_params(path: str) -> Optional[Dict[str, List[int]]]:

    data = atomic_read_json(path)
    if data is None:
        logger.info("No saved per-ticker params found at %s", path)
        return None
    cleaned = {}
    try:
        for t, v in data.items():
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                cleaned[t] = [int(v[0]), int(v[1])]
    except Exception:
        logger.exception("Failed to validate per-ticker params from %s", path)
        return None
    logger.info("Loaded per-ticker params from %s (tickers: %d)", path, len(cleaned))
    return cleaned

# Xuất lịch sử giao dịch (events_df) ra csv
def export_trade_history(events_df: pd.DataFrame, path: str) -> None:
    cols = ["Date", "Ticker", "Type", "Price", "Shares", "Cash_after"]
    df = events_df.copy()
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    df_to_save = df[cols].copy()
    df_to_save["Date"] = pd.to_datetime(df_to_save["Date"], errors="coerce")
    atomic_write(df = df_to_save, path = path, fmt = 'csv')
    logger.info("Exported trade history to %s", path)

# ghi performance metrics ra file csv
def export_performance_metrics(perf_df: pd.DataFrame, path: str) -> None:
   
    perf_df.to_csv(path, index=True)


# Chuyển danh sách TradeEvent -> DataFrame
def events_to_dataframe(events: Sequence[TradeEvent]) -> pd.DataFrame:
    # Nếu rỗng thì trả DataFrame trống với cột chuẩn
    if not events:
        return pd.DataFrame(columns=["Date","Ticker","Type","Price","Shares","Cash_after"])
    rows = []
    for e in events:
        rows.append({
            "Date": pd.to_datetime(e.date),
            "Ticker": e.ticker,
            "Type": e.type,
            "Price": e.price,
            "Shares": e.shares,
            "Cash_after": e.cash_after,
        })
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Price","Shares","Cash_after"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df



# Chuyển equity_curve dạng list[(date, equity), ...] -> pd.Series(index=datetime, values=equity)
def _to_series_from_equity_curve(equity_curve: List[Tuple[pd.Timestamp, float]]) -> pd.Series:
    if equity_curve is None:
        return pd.Series(dtype=float)
    dates = [pd.to_datetime(d) for d, _ in equity_curve]
    vals = [float(v) for _, v in equity_curve]
    s = pd.Series(index=pd.DatetimeIndex(dates), data=vals).sort_index()
    return s

