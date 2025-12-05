# PROJECT_NAME: DESIGN A TRADING STRATEGY FOR US MARKET
Description: Thiết kế trading strategy của thị trường US bằng SMA technical indicator có kết hợp tối ưu tham số về timeframe và độ ưu tiên của từng ticker khi giao dịch. Trading strategy được thử với 50 mã cổ phiếu: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP... và chỉ áp dụng với phương pháp Long (mua thấp - bán cao).
## 1. MAIN USAGE:
- Apply multi-ticker backtesting.
- Sử dụng đồng thời 2 đường SMA(A) và SMA(B) (với A < B) để tìm kiếm signal, trong đó đường SMA(A) đóng vai trò là đường thể hiện sự biến động còn SMA(B) là đường nền, ổn định hơn. 
- Có tối ưu tham số A, B và lựa chọn thứ tự ưu tiên thực thi lệnh mua/bán các Equity trong Portfolio.
## 2. SETUP:

## 3. PROJECT STRUCTURE:
```
project/
│── data/
│   ├── A.csv
│   ├── AAPL.csv
│   ├── ABBV.csv
│   ├── ABT.csv
│   ├── ACGL.csv
│   ├── ACN.csv
│   ├── ADBE.csv
│   ├── ADI.csv
│   ├── ADM.csv
│   ├── ADP.csv
│   ├── ...
│── src/
│   ├── backtest.py
│   ├── optimizer.py
│   ├── execution.py
│   ├── plotting.py
│   ├── core.py
│   ├── signals.py
│   ├── trading_io.py
│   ├── main.py
│── outputs/
│   ├── plot/
│   │   ├── A_sma_10_50.png
│   │   ├── AAPL_sma_10_125.png
│   │   ├── ABBV_sma_10_100.png
│   │   ├── ABT_sma_10_125.png
│   │   ├── ADSK_sma_10_175.png
│   │   ├── AEE_sma_10_75.png
│   │   ├── AKAM_sma_10_175.png
│   │   ├── ACGL_sma_10_50.png
│   │   ├── AME_sma_10_125.png
│   │   ├── ADP_sma_10_50.png
│   │   ├── equity_curve.png
│   │   ├── ...
│   ├── per_ticker_params.json
│   ├── per_trade_summary.csv
│   ├── performance.csv
│   ├── portfolio_daily_returns.csv
│   ├── trade_history.csv
│── README.md
```
## 4. RUN:
4.1. Chuẩn bị dữ liệu:
  - Chạy file yfinance_crawl_data.ipynb lấy các ticker trong khoảng 10 năm từ 1/10/2015 đến 1/10/2025 từ trang yahoo finance
  - Nạp dữ liệu của 10 ticker và thư mục data: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP
  - Load dữ liệu và chia 2 tập train, validation theo tỉ lệ 7:3.
```
    data_folder = r"C:\Users\Dinh Binh An\OneDrive\Dai_hoc\toan_tai_chinh\giua_ki\Data"        # <<< ĐỔI THƯ MỤC TẠI ĐÂY
    base_folder = r'C:\Users\Dinh Binh An\OneDrive\Dai_hoc\toan_tai_chinh\giua_ki\model_result'
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
```

4.2. Thực hiện tối ưu tham số:
  - Nạp file backtest.py và optimizer.py. Sau đó thực hiện Optimize các tham số SMA(A), SMA(B) cho từng ticker

```
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
            initial_cash=initial_cash,
            run_kwargs=run_kwargs,
            min_trades=20,
            trade_penalty_mode="scale",
            fallback_params=(10, 50),
        )
        # Lưu kết quả
        try:
            save_per_ticker_params(per_ticker_params, params_path)
        except Exception:
            logger.exception("Failed to save per-ticker params to %s", params_path)


    logger.info("Per-ticker SMA params computed for %d tickers", len(per_ticker_params))
```

4.3. Thực hiện Backtest
  - Thực hiện Backtest với tập validation:

```
    events_df, perf_df = run_backtest(
        validation,
        initial_cash,
        sma_params=per_ticker_params,
        fees_per_order=1.0,
        stop_loss_pct=0.08,
        take_profit_pct=0.20,
        sizing_method="volatility",
        atr_period=14,
        max_positions_in_portfolio=10,
        sell_fraction_on_signal= 1,
        fixed_amount= 100000
    )
```

4.4. Thực hiện tính toán các metrics:
  - Nạp file metrics.py và thực hiện tính toán các metrics dùng để đánh giá trading strategy như (winrate, PnL, Sharpe, CAGR)
```
    events_df_path = os.path.join(base_folder, "trade_history.csv")
    perf_df_path = os.path.join(base_folder, "performance.csv")

    # Xuất lịch sử giao dịch và metrics
    export_trade_history(events_df, events_df_path)
    logger.info("Trade history saved to %s", events_df_path)

    export_performance_metrics(perf_df, perf_df_path)
    logger.info("Performance metrics saved to %s", perf_df_path)
```
4.5. Trực quan hóa các kết quả và lưu trữ:
  - Nạp file plotting.py và thực hiện trực quan hóa các bảng đánh giá, hình ảnh các signal và các đường SMA(A) và SMA(B) cho từng ticker.
```
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
```
## 5. Ví dụ minh họa:
5.1. Hình tín hiệu BUY/SELL cho từng stock
- Tín hiệu BUY/ SELL của ticker A:
<img width="2800" height="1400" alt="A_sma_10_50" src="https://github.com/user-attachments/assets/1f6e4268-12a7-4a44-afb2-e73a3382ed4b" />
- Tín hiệu BUY/ SELL của ticker AKAM:
<img width="2800" height="1400" alt="AKAM_sma_10_175" src="https://github.com/user-attachments/assets/4e5b77fd-b7f0-407c-a10a-2660427e8cb0" />
- Tín hiệu BUY/ SELL của ticker AME:
<img width="2800" height="1400" alt="AME_sma_10_125" src="https://github.com/user-attachments/assets/7b16a903-e12e-464d-ba61-cbe1132db68e" />
- Tín hiệu BUY/ SELL của ticker ABBV:
<img width="2800" height="1400" alt="ABBV_sma_10_100" src="https://github.com/user-attachments/assets/314c07cd-661a-4aec-8de9-bad285f776e0" />
- Tín hiệu BUY/ SELL của ticker ACGL:
<img width="2800" height="1400" alt="ACGL_sma_10_50" src="https://github.com/user-attachments/assets/972ccdc8-4da6-438c-af98-c619042c14f7" />

5.2. Hình Equity Curve chung của portfolio
<img width="2400" height="1200" alt="equity_curve" src="https://github.com/user-attachments/assets/3b9f2811-15b0-4b03-892b-d02c9c972e95" />

5.3. Bảng trades rút gọn
<img width="692" height="366" alt="Screenshot 2025-12-05 182518" src="https://github.com/user-attachments/assets/5afab768-ed33-42ae-b06c-8684dfac67e6" />

5.4. Performance Metrics
| Ticker | NTrades | WinRate | Realized PnL | PnL | Avg Realized PnL | ProfitFactor | Remaining Share Value | FinalCash | FinalEquity | CAGR | Sharpe | MaxDrawdown | Calmar |
|--------|---------|---------|---------------|---------|---------------------|----------------|------------------------|-----------|---------------|----------|---------|---------------|---------|
| A     | 9  | 0.1111 | -1162.8035 | -1157.4165 | -129.2004 | 0.1392 | 123.4200 |  |  |  |  |  |  |
| AAPL  | 2  | 0.5    | -378.4736 | 131.1825    | -189.2368 | 0.3375 | 4837.6504 | | | | | | |
| ABBV  | 7  | 0.1429 | -1991.9110 | 1021.4944 | -284.5587 | 0.0675 | 21481.9548 | | | | | | |
| ABT   | 4  | 0.5    | 1074.4660 | 1171.2064 | 268.6165 | 9.7998 | 10449.4742 | | | | | | |
| ADSK  | 3  | 0.3333 | 325.0002 | 325.0002 | 108.3334 | 1.2039 | 0 | | | | | | |
| AEE   | 5  | 0.6    | 307.2379 | 336.2600 | 61.4476 | 8.8396 | 622.2000 | | | | | | |
| AKAM  | 2  | 0      | -1156.2805 | -1156.2805 | -578.1402 | 0 | 0 | | | | | | |
| ACGL  | 10 | 0.4    | 3599.8816 | 3599.8816 | 359.9882 | 3.9170 | 0 | | | | | | |
| AME   | 1  | 1      | 561.5938 | 1325.9384 | 561.5938 | — | 12701.0399 | | | | | | |
| ADP   | 8  | 0.375  | 71.1052 | 71.1052 | 8.8882 | 1.2522 | 0 | | | | | | |
5.5. Tham số tối ưu:
## 6. PARAMETERS:
```
     run_kwargs = {
        "sizing_method": "volatility",
        "atr_period": 14,
        "fees_per_order": 0,
        "stop_loss_pct": 0.08,
        "take_profit_pct": 0.20,
        "max_pct_per_ticker": 0.10,
    }
```


