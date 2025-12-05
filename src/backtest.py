# backtest.py
from typing import Dict, Optional, Sequence, Tuple, List
import logging
import math
import numpy as np
import pandas as pd
from core import replay_and_pairs, to_equity_df, compute_unrealized_from_events, realized_metrics_from_trades, \
                    compute_portfolio_metrics, logger, compute_return_stats, TradeEvent,last_price_up_to, BacktestConfig
from signals import generate_signals, compute_atr
from execution import select_stocks_to_buy, select_stocks_to_sell, execute_orders
from trading_io import save_per_ticker_params, load_per_ticker_params, events_to_dataframe
from plotting import plot_equity_curve  # chỉ khi cần vẽ nội bộ


# Hàm chạy backtest chính: trả events_df và perf_df
def run_backtest(
    universe_prices: Dict[str, pd.DataFrame],
    sma_params,
    config: BacktestConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    initial_cash = config.initial_cash
    atr_period = config.atr_period
    fees_per_order = config.fees_per_order
    stop_loss_pct = config.stop_loss_pct
    take_profit_pct = config.take_profit_pct
    max_positions_in_portfolio = config.max_positions_in_portfolio
    max_pct_per_ticker = config.max_pct_per_ticker
    
    # Chuẩn bị signals và ATR cho mỗi ticker
    signals_map: Dict[str, pd.DataFrame] = {}
    atr_map: Dict[str, pd.Series] = {}
    for t, df in universe_prices.items():
        df = df.copy()
        s_l = sma_params.get(t, None) if isinstance(sma_params, dict) else None
        if s_l is None:
            short_w, long_w = 10, 50
        else:
            short_w, long_w = int(s_l[0]), int(s_l[1])

        signals_map[t] = generate_signals(df["Close"], short_w, long_w)

        try:
            atr_map[t] = compute_atr(df, period=atr_period)
        except Exception:
            atr_map[t] = pd.Series(0.0, index=df.index)

    # Tập hợp tất cả ngày trong universe
    all_dates = None
    for df in universe_prices.values():
        if all_dates is None:
            all_dates = df.index
        else:
            all_dates = all_dates.union(df.index)
    all_dates = all_dates.unique().sort_values()

    # Khởi tạo trạng thái
    positions: Dict[str, float] = {t: 0.0 for t in universe_prices.keys()}
    cash = float(initial_cash)
    events: List[TradeEvent] = []
    last_buy_price: Dict[str, float] = {}
    
    equity_curve: List[Tuple[pd.Timestamp, float]] = []

    # Lặp theo ngày, xử lý sell trước rồi buy
    for date in all_dates:
        price_map: Dict[str, float] = {}
        signals_today: Dict[str, Dict] = {}
        for t, df in universe_prices.items():

            if date in df.index:
                price_map[t] = float(df.loc[date, "Open"])
                
            sig_df = signals_map.get(t)
            if sig_df is None:
                continue
            if date in sig_df.index:
                row = sig_df.loc[date]

                price_for_signal = price_map.get(t)
                if price_for_signal is None:
                    price_for_signal = last_price_up_to(df, date)
                signals_today[t] = {
                    "signal": int(row.get("signal", 0)),
                    "sma_short": float(row.get("sma_short", price_for_signal if price_for_signal is not None else 0.0)),
                    "sma_long": float(row.get("sma_long", price_for_signal if price_for_signal is not None else 0.0))
                }

        # Chọn và thực hiện lệnh bán
        sell_orders = select_stocks_to_sell(
            date=date,
            universe_prices=universe_prices,
            positions=positions,
            price_map=price_map,
            signals_today=signals_today,
            last_buy_price=last_buy_price,
            config=config
        )

        positions, cash, sell_events = execute_orders(
            sell_orders, price_map, positions, cash, date,
            is_buy=False, config= config
        )
        events.extend(sell_events)

        
        # Chọn và thực hiện lệnh mua (nếu có tín hiệu buy)
        buy_orders_selected = []
        has_buy = any(info.get("signal", 0) == 1 for info in signals_today.values())
        if has_buy:
            buy_orders_selected = select_stocks_to_buy(
                date=date,
                universe_prices=universe_prices,
                signals_today=signals_today,
                cash=cash,
                sma_params=sma_params,
                atr_map=atr_map,
                config=config
            )


        # Giới hạn số vị thế mở tối đa trong portfolio
        if max_positions_in_portfolio is not None and buy_orders_selected:
            current_open = sum(1 for v in positions.values() if v > 0)
            available_slots = max(0, max_positions_in_portfolio - current_open)
            if available_slots <= 0:
                buy_orders_selected = []
            else:
                buy_orders_selected = buy_orders_selected[:available_slots]

        positions, cash, buy_events = execute_orders(
            buy_orders_selected, price_map, positions, cash, date,
             is_buy=True, config= config
        )

        
        # Cập nhật lại giá mua cuối
        for e in buy_events:
            last_buy_price[e.ticker] = e.price


        events.extend(buy_events)

        # Tính tổng giá trị tài sản (cash + market value)
        total_value = float(cash)
        for t, shares in positions.items():
            if shares <= 0:
                continue

            price = price_map.get(t)
            if price is None or np.isnan(price):
                df_t = universe_prices.get(t)
                price = last_price_up_to(df_t, date) if df_t is not None else float("nan")
            if price is None or np.isnan(price):

                continue
            total_value += float(shares) * float(price)
        equity_curve.append((date, total_value))

    # Kết thúc vòng lặp ngày -> build events_df
    if not events:
        events_df = pd.DataFrame(columns=["Date", "Ticker", "Type", "Price", "Shares", "Cash_after"])
    else:
        events_df = events_to_dataframe(events)


    last_date = all_dates.max() if hasattr(all_dates, "max") else (all_dates[-1] if len(all_dates) > 0 else None)
    if last_date is None:
        last_date = pd.Timestamp.now()

    unrealized_by_ticker, market_value_by_ticker = compute_unrealized_from_events(events_df, universe_prices, last_date)

    final_cash = cash

    per_trade_df = replay_and_pairs(events_df, return_book=False)

    logger.info("Events: %d | Per-trade pairs: %d", len(events_df) if events_df is not None else 0,
                per_trade_df.shape[0] if per_trade_df is not None else 0)


    perf_rows = []
    realized_by_ticker = {}
    if per_trade_df is not None and not per_trade_df.empty:
        grp = per_trade_df.groupby("Ticker")
        for t, g in grp:
            realized_by_ticker[t] = realized_metrics_from_trades(g)

    realized_sum = {}
    if per_trade_df is not None and not per_trade_df.empty and "Ticker" in per_trade_df.columns:
        rsum = per_trade_df.groupby("Ticker")["RealizedPNL"].sum()
        for t in rsum.index:
            realized_sum[t] = float(rsum.loc[t])

    for t in universe_prices.keys():
        realized = realized_sum.get(t, 0.0)
        unrealized_pnl = unrealized_by_ticker.get(t, 0.0)
        remaining_share_val = market_value_by_ticker.get(t, 0.0)
        
        rm = realized_by_ticker.get(t, {})
        n_trades_t = per_trade_df[per_trade_df["Ticker"] == t].shape[0] if per_trade_df is not None and "Ticker" in per_trade_df.columns else 0

        perf_rows.append({
            "Ticker": t,
            "NTrades": int(n_trades_t),
            "WinRate": float(rm.get("win_rate", np.nan)),
            "Realized_pnl": realized,
            "PNL": float(realized + unrealized_pnl),
            "Avg_realized_pnl": float(rm.get("avg_realized_pnl", np.nan)),
            "ProfitFactor": float(rm.get("profit_factor", np.nan)),
            "Remaining_share_value": float(remaining_share_val),
            "FinalCash": np.nan,
            "FinalEquity": np.nan,
            "CAGR": np.nan,
            "Sharpe": np.nan,
            "MaxDrawdown": np.nan,
            "Calmar": np.nan
        })

    final_mark = sum(float(market_value_by_ticker.get(t, 0.0)) for t in universe_prices.keys())
    
    final_equity = final_cash + final_mark



    total_realized = sum(realized_sum.values()) if realized_sum else 0.0
    total_unrealized_pnl = sum(float(unrealized_by_ticker.get(t, 0.0)) for t in universe_prices.keys())
    total_pnl = total_realized + total_unrealized_pnl
    portfolio_metrics = compute_portfolio_metrics(equity_curve, per_trade_df=per_trade_df)
    port_cagr = portfolio_metrics.get("CAGR", np.nan)
    port_maxdd = portfolio_metrics.get("MaxDrawdown", np.nan)
    calmar_port = port_cagr / abs(port_maxdd) 


    # Thêm hàng tóm tắt portfolio
    perf_rows.append({
        "Ticker": "_PORTFOLIO_",
        "Remaining_share_value": float(final_mark),
        "FinalCash": float(final_cash),
        "FinalEquity": float(final_equity),
        "CAGR": float(port_cagr),
        "Sharpe": float(portfolio_metrics.get("Sharpe", np.nan)),
        "MaxDrawdown": float(port_maxdd),
        "Calmar": float(calmar_port),
        "NTrades": int(per_trade_df.shape[0]) if per_trade_df is not None else 0,
        "WinRate": float(portfolio_metrics.get("win_rate", np.nan)),
        "Realized_pnl": total_realized,
        "PNL": float(total_pnl),
        "Avg_realized_pnl": float(portfolio_metrics.get("avg_realized_pnl", np.nan)),
        "ProfitFactor": float(portfolio_metrics.get("profit_factor", np.nan)),
    })

    perf_df = pd.DataFrame(perf_rows).set_index("Ticker")
    perf_df.attrs["equity_curve"] = equity_curve
    perf_df.attrs["per_trade_df"] = per_trade_df
    perf_df.attrs["backtest_metrics"] = portfolio_metrics

    return events_df, perf_df