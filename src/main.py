# main.py 
import os
import logging
import math
from typing import Dict
import pandas as pd
import numpy as np
from trading_io import atomic_read_json, atomic_write, save_per_ticker_params, load_per_ticker_params, \
                        export_trade_history, export_performance_metrics, events_to_dataframe
from backtest import run_backtest
from plotting import plot_trades_for_ticker, plot_equity_curve
from core import replay_and_pairs, logger, BacktestConfig
from optimizer import  optimize_sma_per_ticker, optimize_sma

if __name__ == "__main__":

    config = BacktestConfig(
        initial_cash=100_000,               # Vốn ban đầu 
        sizing_method="volatility",         # Phương pháp tính khối lượng giao dịch
        fraction=None,                      # Tỷ lệ vốn cho mỗi lệnh 
        fixed_amount= None,                # Số tiền cố định cho mỗi lệnh 
        lot_size=1,                         # Kích thước lô cổ phiếu; thị trường Mỹ mua tối thiểu 1 cổ phiếu
        allow_fractional=False,             # Cho phép mua fractional shares 
        volatility_risk_pct=0.02,           # Rủi ro tối đa mỗi lệnh 
        atr_multiplier=1.0,                 # Hệ số nhân ATR 
        stop_loss_pct=0.08,                 # Mức cắt lỗ cố định 
        take_profit_pct=0.20,               # Mức chốt lời cố định 
        sell_fraction_on_signal=1.0,        # Tỷ lệ bán khi có tín hiệu SELL 
        max_sells_per_day=None,             # Giới hạn số lệnh bán mỗi ngày (None = không giới hạn)
        max_positions_per_day= math.inf,    # Số lệnh BUY tối đa được mở trong 1 ngày giao dịch
        max_positions_in_portfolio= None,    # Số lượng vị thế tối đa được giữ trong danh mục
        max_pct_per_ticker=0.5,            # Tỷ lệ vốn tối đa phân bổ cho một ticker 
        fees_per_order= 0,                  # Phí giao dịch cho mỗi lệnh (mua/bán)
        atr_period=14,                      # Chu kỳ tính ATR
        min_trades= 20,                      # Số lượng giao dịch tối thiểu yêu cầu để mô hình tối ưu được chấp nhận
        trade_penalty_mode="scale",         # Cách xử lý khi số trade < min_trades: "scale" giảm điểm hoặc "reject" loại bỏ
    )


    # Load dữ liệu
    data_folder = r"C:\Users\Dinh Binh An\OneDrive\Dai_hoc\toan_tai_chinh\giua_ki\Data"        # <<< ĐỔI THƯ MỤC TẠI ĐÂY
    base_folder = r'C:\Users\Dinh Binh An\OneDrive\Dai_hoc\toan_tai_chinh\giua_ki\SMA_trading_strategy\model_result'
    initial_cash = 100_000
    os.makedirs(base_folder, exist_ok=True)

    universe = {}
    for file in os.listdir(data_folder):
        if not file.lower().endswith(".csv"):
            continue

        ticker = os.path.splitext(file)[0]
        path = os.path.join(data_folder, file)

        try:
            df = pd.read_csv(path)
        except Exception as e:
            # Nếu file lỗi thì log và bỏ qua
            logger.error("Cannot read %s: %s", path, e)
            continue

        # Chuẩn hoá cột Date, loại NaT, sắp xếp theo ngày và đặt làm index
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc = True)
        df = df.dropna(subset=["Date"])
        df = df.sort_values("Date").set_index("Date")
        try:
            # Bỏ timezone để đồng bộ
            df.index = df.index.tz_convert(None)
        except Exception:
            pass

        df.name = ticker
        universe[ticker] = df

    if len(universe) == 0:
        raise ValueError("No valid CSV files found in folder.")

    logger.info("Loaded tickers: %s", list(universe.keys()))


    # Lấy tất cả ngày có trong universe, chia theo tỷ lệ train_ratio
    train_ratio = 0.7
    all_dates = pd.Index(sorted(set().union(*[df.index for df in universe.values()])))
    split_idx = int(len(all_dates) * train_ratio)
    train_end_date = all_dates[split_idx]


    # Chuẩn bị validation set: các ngày > train_end_date
    validation = {t: df[df.index > train_end_date].copy() for t, df in universe.items()}
    validation = {t: df for t, df in validation.items() if len(df) > 0}

    if len(validation) == 0:
        raise RuntimeError("No validation data available after train_end_date. Check split or data.")

    # Tạo grid để tối ưu tham số 
    long_grid = np.arange(50, 201, 25)
    short_grid = []
    for l in long_grid:
        s1 = max(5, int(l * 0.2))
        s2 = max(5, int(l * 0.25))
        short_grid.extend([s1, s2])
    short_grid = sorted(list(set(short_grid)))
    
    # Đường dẫn lưu các tham số tối ưu
    params_path = os.path.join(base_folder, "per_ticker_params.json")
    FORCE_REOPTIMIZE = False  # True để bỏ file đã lưu và train lại
    per_ticker_params = None
    
    if not FORCE_REOPTIMIZE:
         # Thử load params đã lưu trước đó
        per_ticker_params = load_per_ticker_params(params_path)

    if per_ticker_params is None:
        # Nếu không có params lưu sẵn thì tối ưu cho từng ticker
        logger.info("No saved params or reopt requested → running optimize_sma_per_ticker()")
        per_ticker_params = optimize_sma_per_ticker(
            universe,
            train_end_date,
            short_grid,
            long_grid,
            config=config,
            fallback_params=(10,50),   
        )

        # Lưu kết quả
        try:
            save_per_ticker_params(per_ticker_params, params_path)
        except Exception:
            logger.exception("Failed to save per-ticker params to %s", params_path)


    logger.info("Per-ticker SMA params computed for %d tickers", len(per_ticker_params))


    # Chạy backtest trên dữ liệu validation với per-ticker params đã có
    events_df, perf_df = run_backtest(
         validation,
        sma_params=per_ticker_params,
        config=config,
    )

    # Lưu lịch sử giao dịch
    events_df_path = os.path.join(base_folder, "trade_history.csv")
    perf_df_path = os.path.join(base_folder, "performance.csv")

    # Xuất lịch sử giao dịch và metrics
    export_trade_history(events_df, events_df_path)
    logger.info("Trade history saved to %s", events_df_path)

    export_performance_metrics(perf_df, perf_df_path)
    logger.info("Performance metrics saved to %s", perf_df_path)

    # Vẽ biểu đồ trực quan quá trình giao dịch
    plots_dir = os.path.join(base_folder, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # Tạo plot cho từng ticker: giá + SMA + BUY/SELL
    for ticker, df in validation.items():
        df = df.copy()
        df.name = ticker

        # Lấy tham số SMA để vẽ (nếu có)
        if isinstance(per_ticker_params, dict) and (ticker in per_ticker_params):
            s_plot, l_plot = per_ticker_params[ticker]
        elif isinstance(per_ticker_params, (tuple, list)) and len(per_ticker_params) == 2:
            s_plot, l_plot = per_ticker_params
        else:
            s_plot, l_plot = (10, 50)

        out_png = os.path.join(
            plots_dir,
            f"{ticker}_sma_{s_plot}_{l_plot}.png"
        )
        plot_trades_for_ticker(
            df, events_df,
            int(s_plot), int(l_plot),
            out_png
        )
    # Vẽ và lưu equity curve của portfolio'
    equity_curve = perf_df.attrs.get("equity_curve", [])
    out_eq = os.path.join(plots_dir, "equity_curve.png")
    plot_equity_curve(equity_curve, out_eq)

    if not events_df.empty and "Date" in events_df.columns:
        events_df["Date"] = pd.to_datetime(events_df["Date"], errors="coerce")
    
    # Tạo per-trade summary (replay các lệnh để ghép entry/exit)
    per_trade_df = replay_and_pairs(events_df,return_book= False)
    per_trade_path = os.path.join(base_folder, "per_trade_summary.csv")
    if not per_trade_df.empty:
        per_trade_df.to_csv(per_trade_path, index=False)
        logger.info("Per-trade summary saved to %s", per_trade_path)
    else:
        logger.info("No per-trades to save.")
        
    # Xuất daily returns từ equity curve nếu có
    if equity_curve:
        ec_df = pd.DataFrame(equity_curve, columns=["Date", "Equity"]).set_index("Date").sort_index()
        ec_df.index = pd.to_datetime(ec_df.index)
        ec_df["DailyReturn"] = ec_df["Equity"].pct_change().fillna(0.0)
        ec_path = os.path.join(base_folder, "portfolio_daily_returns.csv")
        ec_df.to_csv(ec_path)
        logger.info("Portfolio daily returns saved to %s", ec_path)
    else:
        logger.info("No equity curve available for daily returns export.")

    
