# Chiến lược giao dịch cổ phiếu Coca-Cola

Coca-Cola (mã cổ phiếu: KO) là một trong những thương hiệu nước giải khát lớn nhất và lâu đời nhất trên thế giới, với mạng lưới phân phối toàn cầu và danh mục sản phẩm đa dạng từ nước ngọt có ga, nước trái cây, trà, cà phê cho đến nước đóng chai. Nhờ vị thế dẫn đầu ngành cùng khả năng duy trì dòng tiền ổn định, cổ phiếu KO thường được xem là lựa chọn an toàn và hấp dẫn cho các nhà đầu tư dài hạn cũng như ngắn hạn.
Dự án này được thực hiện nhằm xây dựng chiến lược giao dịch cho cổ phiếu Coca-Cola, dựa trên phân tích dữ liệu lịch sử giá và các mô hình kỹ thuật. Việc lựa chọn KO xuất phát từ:
- Tính ổn định: Coca-Cola có lịch sử tăng trưởng bền vững và thường được coi là “cổ phiếu phòng thủ” trong thời kỳ biến động.
- Thanh khoản cao: KO là một trong những cổ phiếu blue-chip được giao dịch rộng rãi trên thị trường chứng khoán Mỹ.
Dự án sẽ tập trung vào các khía cạnh phân tích dữ liệu như xu hướng giá, hiệu ứng lịch, ngoại lệ và mô hình giao dịch theo mùa, từ đó đề xuất chiến lược tối ưu cho việc đầu tư và giao dịch cổ phiếu KO.

## Mô tả

Dự án này thực hiện phân tích dữ liệu khám phá trên dữ liệu giá cổ phiếu của Coca-Cola, từ đó đưa ra chiến lược giao dịch phù hợp. Các nội dung bao gồm:
- Crawl dữ liệu cổ phiếu 
- Phát hiện ngoại lệ (Outliers)
- Kiểm tra xu hướng trung bình (Mean Reversion)
- Theo dõi xu hướng (Trend Following)
- Phân tích hiệu ứng lịch (Calendar Effects)
- Phân tích mẫu lên xuống (Up-Down Patterns)
- Chiến lược giao dịch theo mùa (Seasonal Trading Strategy)

## Yêu cầu hệ thống

- Python 3.x
- Các thư viện: pandas, matplotlib, numpy, talib, scipy, statsmodels

## Cài đặt

Cài đặt các thư viện cần thiết bằng pip:

```
pip install pandas matplotlib numpy talib scipy statsmodels yfinance
```

## Cách sử dụng

1. Đảm bảo file dữ liệu `KO.csv` được đặt trong thư mục `Data` (đường dẫn tương đối từ dự án).
2. Mở và chạy notebook `main.ipynb` trong Jupyter Notebook hoặc JupyterLab.
3. Notebook sẽ tải dữ liệu, thực hiện phân tích và hiển thị kết quả trực quan.

## Cấu trúc dự án

- `main.ipynb`: Notebook chính chứa toàn bộ quy trình phân tích.
- `yfinance_crawl_data.ipynb`: Notebook crawl dữ liệu từ trang yahoo finance
- `check_trend_following.py`: Module kiểm tra và phân tích pattern trend-following.
- `check_mean_reversion.py`: Module kiểm tra và phân tích pattern mean_reversion.
- `calendar_analysis.py`: Module phân tích Calendar effect.
- `check_outliers.py`: Module phát hiện và phân tích ngoại lệ.
- `pattern_up_down.py`: Module phân tích pattern up down.
- `trading_strategy_season.py`: Module chạy chiến lược giao dịch theo mùa.
- `Data/`: Thư mục chứa dữ liệu đầu vào (KO.csv).

## Kết quả

Dự án cung cấp các biểu đồ và thống kê về:
- Phân phối giá cổ phiếu
- Phân tích xu hướng và ngoại lệ
- Các chỉ báo kỹ thuật
- Hiệu suất chiến lược giao dịch

