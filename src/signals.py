# signals.py
from typing import Optional, Dict
import math
import numpy as np
import pandas as pd
from core import BacktestConfig



# Sinh tín hiệu SMA crossover (1: buy, -1: sell, 0: none)
def generate_signals(price: pd.Series, short_w: int, long_w: int) -> pd.DataFrame:
    df = pd.DataFrame(index=price.index)
    df["price"] = price
    df["sma_short"] = price.rolling(short_w, min_periods=short_w).mean()
    df["sma_long"] = price.rolling(long_w, min_periods=long_w).mean()

    prev_short = df["sma_short"].shift(1)
    prev_long = df["sma_long"].shift(1)

    # Phát hiện giao cắt 
    buy = prev_short.notna() & prev_long.notna() & (prev_short <= prev_long) & (df["sma_short"] > df["sma_long"])
    sell = prev_short.notna() & prev_long.notna() & (prev_short >= prev_long) & (df["sma_short"] < df["sma_long"])

    df["signal"] = 0
    df.loc[buy, "signal"] = 1
    df.loc[sell, "signal"] = -1

    #Việc mua/bán sẽ diễn ra vào ngày giao dịch TIẾP THEO 
    df["signal"] = df["signal"].shift(1).fillna(0).astype(int)
    
    return df

# Tính điểm ưu tiên mua cho 1 cổ theo SMA/momentum/vol
def compute_priority_score(df: pd.DataFrame, short_w: int, long_w: int, remove_last: bool = True ) -> float:
    if len(df) <= long_w:
        return 0.0
    
    df_hist = df.copy()

    if remove_last:
        # loại bỏ bar gần nhất để tránh look-ahead
        df_hist = df.iloc[:-1]

    sma_short_series = df_hist["Close"].rolling(short_w, min_periods=short_w).mean().dropna()
    sma_long_series = df_hist["Close"].rolling(long_w, min_periods=long_w).mean().dropna()
    if sma_short_series.empty or sma_long_series.empty:
        return 0.0
    
    sma_short = sma_short_series.iloc[-1]
    sma_long = sma_long_series.iloc[-1]

    sma_strength = (sma_short / sma_long) - 1

    if len(df_hist) >= 20:
        momentum = df_hist["Close"].iloc[-1] / df_hist["Close"].iloc[-20] - 1
    else:
        momentum = 0.0

    vol = df_hist["Close"].pct_change().rolling(20, min_periods=20).std().dropna()
    
    vol = vol.iloc[-1] if not vol.empty else 1.0
    if np.isnan(vol) or vol == 0:
        vol = 1.0

    # Trộn các yếu tố thành thành một điểm tổng hợp
    score = sma_strength * 0.5 + momentum * 0.4 + (1 / vol) * 0.1

    return score


# Tính điểm ưu tiên mua cho 1 cổ theo SMA/momentum/vol
def compute_priority_score(df: pd.DataFrame, short_w: int, long_w: int, remove_last: bool = True ) -> float:
    if len(df) <= long_w:
        return 0.0
    
    df_hist = df.copy()

    if remove_last:
        # loại bỏ bar gần nhất để tránh look-ahead
        df_hist = df.iloc[:-1]

    sma_short_series = df_hist["Close"].rolling(short_w, min_periods=short_w).mean().dropna()
    sma_long_series = df_hist["Close"].rolling(long_w, min_periods=long_w).mean().dropna()
    if sma_short_series.empty or sma_long_series.empty:
        return 0.0
    
    sma_short = sma_short_series.iloc[-1]
    sma_long = sma_long_series.iloc[-1]

    sma_strength = (sma_short / sma_long) - 1

    if len(df_hist) >= 20:
        momentum = df_hist["Close"].iloc[-1] / df_hist["Close"].iloc[-20] - 1
    else:
        momentum = 0.0

    vol = df_hist["Close"].pct_change().rolling(20, min_periods=20).std().dropna()
    
    vol = vol.iloc[-1] if not vol.empty else 1.0
    if np.isnan(vol) or vol == 0:
        vol = 1.0

    # Trộn các yếu tố thành thành một điểm tổng hợp
    score = sma_strength * 0.5 + momentum * 0.4 + (1 / vol) * 0.1

    return score


# Tính số cổ phiếu cần mua dựa trên các method
def compute_position_size(
    cash: float,
    price: float,
    config: BacktestConfig,
    atr: Optional[float] = None,
) -> float:
    
    method = config.sizing_method
    fraction = config.fraction
    fixed_amount = config.fixed_amount
    lot_size = config.lot_size
    allow_fractional = config.allow_fractional
    volatility_risk_pct = config.volatility_risk_pct
    atr_multiplier = config.atr_multiplier
    # Trả số cổ phiếu cần mua theo method: fraction, fixed hoặc volatility
    if price <= 0 or cash <= 0:
        return 0

    if method == "fraction":
        value = cash * fraction
    elif method == "fixed":
        value = fixed_amount
    elif method == "volatility":
        if atr is None or atr <= 0:
            return 0
        risk_capital = cash * float(volatility_risk_pct)
        risk_per_share = float(atr) * float(atr_multiplier)
        if risk_per_share <= 0:
            return 0
        shares = risk_capital / risk_per_share
        if allow_fractional:
            return shares
        return int(math.floor(shares / max(1, lot_size)) * max(1, lot_size))
    else:
        raise ValueError("Unknown position size method")

    if allow_fractional:
        return value / price

    n = int(math.floor((value / price) / max(1, lot_size)) * max(1, lot_size))
    return n

# Tính ATR (dùng High/Low nếu có, nếu không thì dùng diff Close)
def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    close = df["Close"]

    if "High" in df.columns and "Low" in df.columns:
        high = df["High"]
        low = df["Low"]
        prev_close = close.shift(1)

        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
    else:
        tr = close.diff().abs()

    # Dùng EWM để smooth 
    atr = tr.ewm(alpha=1/period, adjust=False).mean()

    atr = atr.clip(lower=1e-4)  # tránh bằng 0
    atr = atr.ffill() # fill các giá trị thiếu bằng giá trị phía trước
    return atr

