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

```

4.2. Thực hiện tối ưu tham số:
  - Nạp file backtest.py và optimizer.py. Sau đó thực hiện Optimize các tham số SMA(A), SMA(B) cho từng ticker

```
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

```

4.3. Thực hiện Backtest
  - Thực hiện Backtest với tập validation:

```
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

   # Chạy backtest trên dữ liệu validation với per-ticker params đã có
    events_df, perf_df = run_backtest(
         validation,
        sma_params=per_ticker_params,
        config=config,
    )

```

4.4. Thực hiện tính toán các metrics:
  - Nạp file metrics.py và thực hiện tính toán các metrics dùng để đánh giá trading strategy như (winrate, PnL, Sharpe, CAGR,...)
```
    # Lưu lịch sử giao dịch
    events_df_path = os.path.join(base_folder, "trade_history.csv")
    perf_df_path = os.path.join(base_folder, "performance.csv")

    # Xuất lịch sử giao dịch và metrics
    export_trade_history(events_df, events_df_path)
    logger.info("Trade history saved to %s", events_df_path)

    export_performance_metrics(perf_df, perf_df_path)
    logger.info("Performance metrics saved to %s", perf_df_path)

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

```
4.5. Trực quan hóa các kết quả và lưu trữ:
  - Nạp file plotting.py và thực hiện trực quan hóa các bảng đánh giá, hình ảnh các signal và các đường SMA(A) và SMA(B) cho từng ticker.
```
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
Bảng metrics của các ticker:
| Ticker | NTrades | WinRate | Realized PnL | PnL | Avg Realized PnL | ProfitFactor | Remaining Share Value|
|--------|---------|---------|---------------|---------|---------------------|----------------|------------------------|
| A     | 9  | 0.1111 | -1162.8035 | -1157.4165 | -129.2004 | 0.1392 | 123.4200 |
| AAPL  | 2  | 0.5    | -378.4736 | 131.1825    | -189.2368 | 0.3375 | 4837.6504 |
| ABBV  | 7  | 0.1429 | -1991.9110 | 1021.4944 | -284.5587 | 0.0675 | 21481.9548 |
| ABT   | 4  | 0.5    | 1074.4660 | 1171.2064 | 268.6165 | 9.7998 | 10449.4742 |
| ADSK  | 3  | 0.3333 | 325.0002 | 325.0002 | 108.3334 | 1.2039 | 0 |
| AEE   | 5  | 0.6    | 307.2379 | 336.2600 | 61.4476 | 8.8396 | 622.2000 |
| AKAM  | 2  | 0      | -1156.2805 | -1156.2805 | -578.1402 | 0 | 0 |
| ACGL  | 10 | 0.4    | 3599.8816 | 3599.8816 | 359.9882 | 3.9170 | 0 |
| AME   | 1  | 1      | 561.5938 | 1325.9384 | 561.5938 | — | 12701.0399 |
| ADP   | 8  | 0.375  | 71.1052 | 71.1052 | 8.8882 | 1.2522 | 0 |

Bảng metrics của Portfolio:
| Metric | Value |
|--------|--------------------|
| NTrades | 320 |
| WinRate | 0.390625 |
| Realized PnL | 7336.069884 |
| PnL | 12846.94102 |
| Avg Realized PnL | 22.92521839 |
| ProfitFactor | 1.117868063 |
| Remaining Share Value | 109240.448 |
| FinalCash | 3606.492999 |
| FinalEquity | 112846.941 |
| CAGR | 0.041024003 |
| Sharpe | -0.005823155 |
| MaxDrawdown | -0.186310929 |
| Calmar | 0.220191072 |

5.5. Tham số tối ưu:
| Ticker | SMA(A)| SMA(B) |
|--------|---------|---------|
| A     | 10 | 50 |
| AAPL  | 10 | 125 |
| ABBV  | 10 | 100 |
| ABT   | 10 | 125 |
| ADSK  | 10 | 175 |
| AEE   | 10 | 75 |
| AKAM  | 10 | 175 |
| ACGL  | 10 | 50 |
| AME   | 10 | 125 |
| ADP   | 10 | 50 |

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


