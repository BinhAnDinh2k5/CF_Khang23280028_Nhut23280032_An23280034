from typing import Dict, Optional, Sequence, Tuple
import math
import numpy as np
import pandas as pd
from core import logger, BacktestConfig
from backtest import run_backtest


# Tìm cặp (short, long) tốt nhất 
def optimize_sma(
    universe_prices: Dict[str, pd.DataFrame],
    train_end: pd.Timestamp,
    short_grid: Sequence[int],
    long_grid: Sequence[int],
    config: BacktestConfig,
) -> Tuple[int, int]:

    # Lấy cấu hình từ config 
    min_trades = config.min_trades
    trade_penalty_mode = config.trade_penalty_mode
     # Chỉ lấy dữ liệu trước ngày train_end
    train_prices = {t: df[df.index <= train_end].copy() for t, df in universe_prices.items()}

    if all(len(df) == 0 for df in train_prices.values()):
        raise RuntimeError("No training data available up to train_end — check train_end or inputs.")

    best_score = -math.inf
    best_params: Optional[Tuple[int, int]] = None
    any_grid_evaluated = False

    # Các trọng số (tự set up)
    w1 = 1.0   # Sharpe
    w2 = 0.5   # Profit Factor
    w3 = 2.0   # Max Drawdown 
    w4 = 0.5   # Win rate

    for s in short_grid:
        for l in long_grid:
            if s >= l:
                continue # SMA ngắn phải nhỏ hơn SMA dài

            # Kiểm tra có đủ dữ liệu để tính SMA dài không
            if not any(len(df) >= (l + 1) for df in train_prices.values()):
                logger.debug("Skipping s=%d l=%d: insufficient_history", s, l)
                continue

            any_grid_evaluated = True
            try:
                events_df, perf_df = run_backtest(train_prices, (s, l), config=config)
            except Exception as e:
                logger.warning("run_backtest error for s=%d l=%d: %s", s, l, e)
                logger.info("Grid s=%d l=%d score=%s trades=%d note=%s", s, l, "nan", 0, f"run_error: {e}")
                continue

            # Lấy bảng trade
            per_trade_df_local = None
            try:
                per_trade_df_local = perf_df.attrs.get("per_trade_df") if perf_df is not None else None
            except Exception:
                per_trade_df_local = None

            # Đếm số trade
            if per_trade_df_local is not None and not per_trade_df_local.empty:
                n_trades = int(per_trade_df_local.shape[0])
            else:
                if events_df is not None and not events_df.empty and "Type" in events_df.columns:
                    n_trades = int((events_df["Type"] == "SELL").sum())
                else:
                    n_trades = 0

            # Lấy các metrics cần thiết
            sharpe = float(perf_df.loc["_PORTFOLIO_", "Sharpe"]) if perf_df is not None else np.nan
            maxdd = float(perf_df.loc["_PORTFOLIO_", "MaxDrawdown"]) if perf_df is not None else np.nan
            winrate = float(perf_df.loc["_PORTFOLIO_", "WinRate"]) if perf_df is not None else np.nan
            pf = float(perf_df.loc["_PORTFOLIO_", "ProfitFactor"]) if perf_df is not None else np.nan

            score = (
                w1 * sharpe +
                w2 * pf -
                w3 * abs(maxdd) +
                w4 * winrate
            )

            note = ""
            # Phạt nếu số trade quá ít
            if n_trades < min_trades:
                if trade_penalty_mode == "reject":
                    score = float("nan")
                    note = f"too_few_trades<{min_trades}"
                elif trade_penalty_mode == "scale":
                    factor = (n_trades / min_trades)
                    score = float(score) * float(factor)
                    note = f"penalty_trades({n_trades}/{min_trades})"

            logger.info("Grid s=%d l=%d score=%s trades=%d note=%s", s, l, repr(score), n_trades, note)

            # Cập nhật best score
            if best_params is None or score > best_score:
                best_score = score
                best_params = (int(s), int(l))

    if not any_grid_evaluated or  best_params is None:
        raise RuntimeError("No valid grid results.")  
    
    return best_params


# Tối ưu SMA riêng cho từng ticker 
def optimize_sma_per_ticker(
    universe_prices: Dict[str, pd.DataFrame],
    train_end: pd.Timestamp,
    short_grid: Sequence[int],
    long_grid: Sequence[int],
    config: BacktestConfig,
    fallback_params: Tuple[int, int] = (10, 50),
):
  

    per_ticker_params = {}
    
    # Lấy danh sách tickers
    tickers = list(universe_prices.keys())

    for t in tickers:
        df = universe_prices[t]
        # Chuẩn bị dữ liệu train (các ngày <= train_end)
        train_prices = {t: df[df.index <= train_end].copy()}
        try:
            # Gọi optimize_sma trên dữ liệu 1 ticker
            best_params = optimize_sma(
                train_prices,
                train_end,
                short_grid,
                long_grid,
                config=config
            )
            per_ticker_params[t] = best_params
          
            logger.info("Ticker %s optimized -> s=%d l=%d", t, best_params[0], best_params[1])
        except Exception as e:
            # Nếu tối ưu thất bại, dùng fallback và log cảnh báo
            logger.warning("Optimize failed for %s: %s. Using fallback %s", t, e, fallback_params)
            per_ticker_params[t] = fallback_params
        
    return per_ticker_params