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
│   ├── tickers.csv
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
│   ├── yfinance_crawl_data.ipynb
│   ├── backtest.py
│   ├── optimizer.py
│   ├── execution.py
│   ├── plotting.py
│   ├── core.py
│   ├── signals.py
│   ├── trading_io.py
│   ├── main.py
│── output/
│   ├── output_atr_min_trade_10/
│   │   ├── plots/
│   │   │   ├── A_sma_10_50.png
│   │   │   ├── AAPL_sma_10_125.png
│   │   │   ├── ABBV_sma_10_100.png
│   │   │   ├── ABT_sma_10_125.png
│   │   │   ├── ADSK_sma_10_175.png
│   │   │   ├── AEE_sma_10_75.png
│   │   │   ├── AKAM_sma_10_175.png
│   │   │   ├── ACGL_sma_10_50.png
│   │   │   ├── AME_sma_10_125.png
│   │   │   ├── ADP_sma_10_50.png
│   │   │   ├── equity_curve.png
│   │   │   ├── ...
│   │   ├── per_ticker_params.json
│   │   ├── per_trade_summary.csv
│   │   ├── performance.csv
│   │   ├── portfolio_daily_returns.csv
│   │   ├── trade_history.csv
│   ├── output_atr_min_trade_20/
│   │   ├── plots/
│   │   │   ├── A_sma_10_50.png
│   │   │   ├── AAPL_sma_10_125.png
│   │   │   ├── ABBV_sma_10_100.png
│   │   │   ├── ABT_sma_10_125.png
│   │   │   ├── ADSK_sma_10_175.png
│   │   │   ├── AEE_sma_10_75.png
│   │   │   ├── AKAM_sma_10_175.png
│   │   │   ├── ACGL_sma_10_50.png
│   │   │   ├── AME_sma_10_125.png
│   │   │   ├── ADP_sma_10_50.png
│   │   │   ├── equity_curve.png
│   │   │   ├── ...
│   │   ├── per_ticker_params.json
│   │   ├── per_trade_summary.csv
│   │   ├── performance.csv
│   │   ├── portfolio_daily_returns.csv
│   │   ├── trade_history.csv
│── README.md
```
## 4. RUN:
4.1. Chuẩn bị dữ liệu:
  - Chạy file yfinance_crawl_data.ipynb lấy các ticker trong khoảng 10 năm từ 1/10/2015 đến 1/10/2025 từ trang yahoo finance bằng API
  - Nạp dữ liệu của 50 ticker và thư mục data: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP,....
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
- Tín hiệu BUY/ SELL của ticker A (với min_trade = 10):
<img width="2800" height="1400" alt="A_sma_10_50" src="https://github.com/user-attachments/assets/02617fd2-2351-4e66-8143-523c4e4f2aa9" />
- Tín hiệu BUY/ SELL của ticker A (với min_trade = 20):
<img width="2800" height="1400" alt="A_sma_10_50" src="https://github.com/user-attachments/assets/2be12a0c-07e5-44db-8121-709517802906" />
- Tín hiệu BUY/ SELL của ticker AKAM (với min_trade = 10):
<img width="2800" height="1400" alt="AKAM_sma_10_175" src="https://github.com/user-attachments/assets/f807651f-63c3-4640-b76e-743105b1d6f3" />
- Tín hiệu BUY/ SELL của ticker AKAM (với min_trade = 20):
<img width="2800" height="1400" alt="AKAM_sma_10_175" src="https://github.com/user-attachments/assets/ce09a744-7f28-4416-b7e1-74ffc1292ead" />
- Tín hiệu BUY/ SELL của ticker AME (với min_trade = 10):
<img width="2800" height="1400" alt="AME_sma_10_125" src="https://github.com/user-attachments/assets/f785f437-4824-40e8-99b7-a4ae72756c19" />
- Tín hiệu BUY/ SELL của ticker AME (với min_trade = 20):
<img width="2800" height="1400" alt="AME_sma_10_125" src="https://github.com/user-attachments/assets/4a050b15-f7d2-4e45-b01b-e2e042792de1" />
- Tín hiệu BUY/ SELL của ticker ABBV (với min_trade = 10):
<img width="2800" height="1400" alt="ABBV_sma_10_100" src="https://github.com/user-attachments/assets/3a9dd6ea-febc-4d4d-89e7-971a1df1f4e2" />
- Tín hiệu BUY/ SELL của ticker ABBV (với min_trade = 20):
<img width="2800" height="1400" alt="ABBV_sma_10_100" src="https://github.com/user-attachments/assets/2dd0c08e-5b58-4f37-adf3-eddc28ee9238" />
- Tín hiệu BUY/ SELL của ticker ACGL (với min_trade = 10):
<img width="2800" height="1400" alt="ACGL_sma_10_50" src="https://github.com/user-attachments/assets/f25cef2d-b400-4b55-9bde-b458006ec63c" />
- Tín hiệu BUY/ SELL của ticker ACGL (với min_trade = 20):
<img width="2800" height="1400" alt="ACGL_sma_10_50" src="https://github.com/user-attachments/assets/405d6c36-3e43-4166-98dc-ca9c10026359" />
5.2. Hình Equity Curve và DrawDown chung của portfolio:
- Với min_trade 10:
<img width="2400" height="1200" alt="equity_curve" src="https://github.com/user-attachments/assets/072417f9-2bf9-4042-87ff-15320debf677" />
<img width="989" height="590" alt="drawdown" src="https://github.com/user-attachments/assets/9f41bd26-fbaa-47c1-8b48-87eb9d81d63b" />
- Với min_trade 20:
<img width="2400" height="1200" alt="equity_curve" src="https://github.com/user-attachments/assets/2be576bc-c92c-4f55-b841-463167bfff71" />
<img width="989" height="590" alt="drawdown" src="https://github.com/user-attachments/assets/bfa9297b-518d-4b3c-a260-907e99b76c5e" />

5.3. Bảng trades rút gọn
<img width="692" height="366" alt="Screenshot 2025-12-05 182518" src="https://github.com/user-attachments/assets/5afab768-ed33-42ae-b06c-8684dfac67e6" />

5.4. Performance Metrics
Bảng metrics của các ticker (Với min_trade 10)
| Ticker | NTrades | WinRate     | Realized_pnl | PNL          | Avg_realized_pnl | ProfitFactor | Remaining_share_value |
| ------ | ------- | ----------- | ------------ | ------------ | ---------------- | ------------ | --------------------- |
| A      | 9       | 0.111111111 | -1227.325121 | -1221.938102 | -136.3694579     | 0.137463882  | 123.4199982           |
| AAPL   | 2       | 0.5         | -333.3699266 | 95.81423138  | -166.6849633     | 0.366469901  | 4073.810889           |
| ABBV   | 7       | 0.142857143 | -1853.242137 | 1222.2953    | -264.7488767     | 0.146206071  | 21924.88166           |
| ABT    | 4       | 0.5         | 1375.595629  | 1452.743064  | 343.8989072      | 46.06404626  | 8333.124992           |
| ADSK   | 3       | 0.333333333 | 493.9502106  | 493.9502106  | 164.6500702      | 1.334756722  | 0                     |
| AEE    | 5       | 0.6         | 601.3588313  | 625.5439183  | 120.2717663      | 37.41354239  | 518.4999847           |
| ACGL   | 10      | 0.4         | 2451.59475   | 2451.59475   | 245.159475       | 1.889170153  | 0                     |
| AME    | 1       | 1           | 586.3180665  | 856.0867315  | 586.3180665      |              | 4482.719971           |
| ADP    | 8       | 0.375       | 84.71240477  | 84.71240477  | 10.5890506       | 1.266530005  | 0                     |


Bảng metrics của các ticker (Với min_trade 20)
| Ticker | NTrades | WinRate | Realized_pnl | PNL | Avg_realized_pnl | ProfitFactor | Remaining_share_value |
|--------|---------|---------|---------------|---------------|------------------|---------------|------------------------|
| A     | 9 | 0.111111111 | -1162.803475 | -1157.416456 | -129.2003862 | 0.13916376 | 123.4199982 |
| AAPL  | 2 | 0.5 | -378.473648 | 131.1825395 | -189.236824 | 0.337538067 | 4837.650431 |
| ABBV  | 7 | 0.142857143 | -1991.910974 | 1021.494394 | -284.5587105 | 0.067528553 | 21481.95476 |
| ABT   | 4 | 0.5 | 1074.465971 | 1171.206405 | 268.6164927 | 9.799785195 | 10449.4742 |
| ADSK  | 3 | 0.333333333 | 325.0002441 | 325.0002441 | 108.3334147 | 1.20388977 | 0 |
| AEE   | 5 | 0.6 | 307.2379128 | 336.2600172 | 61.44758255 | 8.839640398 | 622.1999817 |
| AKAM  | 2 | 0 | -1156.280472 | -1156.280472 | -578.1402359 | 0 | 0 |
| ACGL  | 10 | 0.4 | 3599.881588 | 3599.881588 | 359.9881588 | 3.916970496 | 0 |
| AME   | 1 | 1 | 561.5938107 | 1325.938361 | 561.5938107 |  | 12701.03992 |
| ADP   | 8 | 0.375 | 71.10521176 | 71.10521176 | 8.88815147 | 1.25218235 | 0 |

Bảng metrics của Portfolio (min_trade 10 và 20):
| Metric                | Value (min_trade 10)       |  Value (min_trade 20)       |
| --------------------- | ------------ |------------ |
| NTrades               | 306          | 320 |
| WinRate               | 0.395424837  | 0.390625 |
| Realized_pnl          | 11577.88058  | 7336.0698 |
| PNL                   | 19705.96798  | 12846.941 |
| Avg_realized_pnl      | 37.83621105  | 22.9252 |
| ProfitFactor          | 1.191900894  | 1.1178 |
| Remaining_share_value | 116324.2093  | 109240.448  |
| FinalCash             | 3381.758656  | 3606.492999 |
| FinalEquity           | 119705.968   | 112846.941 |
| CAGR                  | 0.061659483  | 0.041 |
| Sharpe                | 0.143332545  | -0.00582 |
| MaxDrawdown           | -0.169036298 | -0.18631 |
| Calmar                | 0.364770663  | 0.22019


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
```


