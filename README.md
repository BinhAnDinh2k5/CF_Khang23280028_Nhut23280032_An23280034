# PROJECT_NAME: DESIGN A TRADING STRATEGY FOR US MARKET
Description: we design a trading strategy for US market by using SMA indicator which have optimized parameter for utilize the return and winrate. Trading strategy được thử với 10 mã cổ phiếu: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP và chỉ áp dụng với phương pháp Long (mua thấp - bán cao).
## 1. MAIN USAGE:
- Apply multi-ticker backtesting.
- Sử dụng đồng thời 2 đường SMA(A) và SMA(B) (với A < B) để tìm kiếm signal, trong đó đường SMA(A) đóng vai trò là đường thể hiện sự biến động còn SMA(B) là đường nền, ổn định hơn. 
- Có tối ưu tham số A, B và lựa chọn thứ tự ưu tiên thực thi lệnh mua/bán các Equity trong Portfolio.

## 2. SETUP:

## 3. PROJECT STRUCTURE:
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
│   ├── metrics.py
│   ├── plotting.py
│── outputs/
│   ├── trade_logs/
│   ├── portfolio.png
│── README.md

## 4. RUN:
4.1. Chuẩn bị dữ liệu:
  - Chạy file yfinance_crawl_data.ipynb lấy các ticker trong khoảng 10 năm từ 1/10/2015 đến 1/10/2025 từ trang yahoo finance
  - Nạp dữ liệu của 10 ticker và thư mục data: A, AAPL, ABBV, ABT, ACGL, ACN, ADBE, ADI, ADM, ADP
  - Load dữ liệu và chia 2 tập train, validation theo tỉ lệ 8:2. 
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
## 5. PARAMETERS:

## 6. 

