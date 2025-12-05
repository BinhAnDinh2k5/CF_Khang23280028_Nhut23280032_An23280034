# PROJECT_NAME: DESIGN A TRADING STRATEGY FOR US MARKET
Description: we design a trading strategy for US market by using SMA indicator which have optimized parameter for utilize the return and winrate. Trading strategy được thử với 10 mã cổ phiếu: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP và chỉ áp dụng với phương pháp Long (mua thấp - bán cao).
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
│   │   ├── AAPL_sma_10_50.png
│   │   ├── ABBV_sma_10_100.png
│   │   ├── ABT_sma_10_50.png
│   │   ├── ACGL_sma_10_50.png
│   │   ├── ACN_sma_10_50.png
│   │   ├── ADBE_sma_10_50.png
│   │   ├── ADI_sma_10_50.png
│   │   ├── ADM_sma_10_50.png
│   │   ├── ADP_sma_10_50.png
│   │   ├── equity_curve.png
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
Code:

4.3. Thực hiện Backtest
  - Thực hiện Backtest với tập validation:
Code:

4.4. Thực hiện tính toán các metrics:
  - Nạp file metrics.py và thực hiện tính toán các metrics dùng để đánh giá trading strategy như (winrate, PnL, Sharpe, CAGR)
4.5. Trực quan hóa các kết quả:
  - Nạp file plotting.py và thực hiện trực quan hóa các bảng đánh giá, hình ảnh các signal và các đường SMA(A) và SMA(B) cho từng ticker.

4.6. Xuất kết quả và lưu trữ.
## 5. Ví dụ minh họa:
5.1. Hình Equity Curve chung của portfolio

5.2. Hình tín hiệu BUY/SELL cho từng stock

5.3. Bảng trades rút gọn

5.4. Performance Metrics

5.5. Tham số tối ưu:
## 6. PARAMETERS:
 

