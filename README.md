# **Chiến lược giao dịch cổ phiếu Coca-Cola**

Coca-Cola (mã cổ phiếu: KO) là một trong những thương hiệu nước giải khát lớn nhất và lâu đời nhất trên thế giới, với mạng lưới phân phối toàn cầu và danh mục sản phẩm đa dạng từ nước ngọt có ga, nước trái cây, trà, cà phê cho đến nước đóng chai. Nhờ vị thế dẫn đầu ngành cùng khả năng duy trì dòng tiền ổn định, cổ phiếu KO thường được xem là lựa chọn an toàn và hấp dẫn cho các nhà đầu tư dài hạn cũng như ngắn hạn.
Dự án này được thực hiện nhằm xây dựng chiến lược giao dịch cho cổ phiếu Coca-Cola, dựa trên phân tích dữ liệu lịch sử giá và các mô hình kỹ thuật. Việc lựa chọn KO xuất phát từ:
- Tính ổn định: Coca-Cola có lịch sử tăng trưởng bền vững và thường được coi là “cổ phiếu phòng thủ” trong thời kỳ biến động.
- Thanh khoản cao: KO là một trong những cổ phiếu blue-chip được giao dịch rộng rãi trên thị trường chứng khoán Mỹ.
Dự án sẽ tập trung vào các khía cạnh phân tích dữ liệu như xu hướng giá, hiệu ứng lịch, ngoại lệ và mô hình giao dịch theo mùa, từ đó đề xuất chiến lược tối ưu cho việc đầu tư và giao dịch cổ phiếu KO.

## **Mô tả**

Dự án này thực hiện phân tích dữ liệu khám phá trên dữ liệu giá cổ phiếu của Coca-Cola, từ đó đưa ra chiến lược giao dịch phù hợp. Các nội dung bao gồm:
- Crawl dữ liệu cổ phiếu 
- Phát hiện ngoại lệ (Outliers)
- Kiểm tra xu hướng trung bình (Mean Reversion)
- Theo dõi xu hướng (Trend Following)
- Phân tích hiệu ứng lịch (Calendar Effects)
- Phân tích mẫu lên xuống (Up-Down Patterns)
- Chiến lược giao dịch theo mùa (Seasonal Trading Strategy)

## **Yêu cầu hệ thống**

- Python 3.x
- Các thư viện: pandas, matplotlib, numpy, talib, scipy, statsmodels

## **Cài đặt**

Cài đặt các thư viện cần thiết bằng pip:

```
pip install pandas matplotlib numpy talib scipy statsmodels yfinance
```

## **Cấu trúc dự án**

- `trading_strategy_season_backtest.ipynb`: Notebook chính chứa trading strategy theo mùa cố định và backtest.
- `EDA.ipynb`: Notebook chứa các phân tích EDA của data Coca-Cola.
- `yfinance_crawl_data.ipynb`: Notebook crawl dữ liệu từ trang yahoo finance
- `check_trend_following.py`: Module kiểm tra và phân tích pattern trend-following.
- `check_mean_reversion.py`: Module kiểm tra và phân tích pattern mean_reversion.
- `calendar_analysis.py`: Module phân tích Calendar effect.
- `check_outliers.py`: Module phát hiện và phân tích ngoại lệ.
- `pattern_up_down.py`: Module phân tích pattern up down.
- `trading_strategy_season.py`: Module chạy chiến lược giao dịch theo mùa.
- `yearly_return.py`: Module chứa các trực quan hóa và tính toán các metrics đánh giá return theo năm, quý
- `Data/`: Thư mục chứa dữ liệu đầu vào (KO.csv).


## **Cách sử dụng**
1. Dùng notebook `yfinance_crawl_data.ipynb` để crawl dữ liệu cổ phiếu Coca-cola về thư mục 'Data'
2. Đảm bảo file dữ liệu `KO.csv` được đặt trong thư mục `Data` (đường dẫn tương đối từ dự án).
3. Mở file notebook EDA.ipynb để xem phân tích EDA về dữ liệu Coca-cola.
4. Khi muốn chạy để xem backtest và đánh giá kết quả của chiến lược giao dịch theo mùa, mở và chạy notebook `trading_strategy_season_backtest.ipynb` trong Jupyter Notebook hoặc JupyterLab.
5. Notebook sẽ tải dữ liệu, thực hiện phân tích và hiển thị kết quả trực quan.

## **Một số điểm chính trong phần thực hành:**
### **Về phân tích EDA bộ dữ liệu Coca - Cola:**
**CHI TIẾT TRONG FILE EDA.ipynb**  
Bộ dữ liệu Coca Cola dùng cho phân tích EDA lấy từ năm 2005 đến năm 2014:
1. Phát hiện các outliers:
- Bộ dữ liệu cho thấy có outliers nằm ở khoảng cuối năm 2008 gần đầu năm 2009. Điều này phù hợp với tình huống thực tế, bởi trong khoảng thời gian này xảy ra cuộc khủng hoảng kinh tế lớn (cuộc khủng hoảng kinh tế tại Hoa Kỳ năm 2008-2009) nên ảnh hưởng trực tiếp đến giá cổ phiếu dẫn đến giá cổ phiếu biến động lớn --> outliers  
<img width="1492" height="620" alt="image" src="https://github.com/user-attachments/assets/d2e5d0e1-15e0-4262-a777-6300f02de156" />

- Do đó, các outliers này hình thành phù hợp với các sự kiện lịch sử nên ta không xử lí chúng.

2. Kiểm tra Pattern trend-following của cổ phiếu:
- Về mặt tổng thể, cổ phiếu Coca Cola không thể hiện được pattern trend-following do không thỏa các điều kiện cần thiết theo chuẩn (AutoCorrelation > 0; median ADX > 25; Tỷ lệ thời gian giá trên/ dưới SMA 50):
  - autocorr = -0.07382 < 0 : giá không có xu hương duy trì đà của nó
  - adx_median = 21.24095 < 25 : Xu hướng không đủ mạnh
  - SMA50_slope: 0.00813 => Có xu hướng trung bình đang đi lên nhưng mà yếu
  - pct_close_above_SMA50 = 0.60127 => chưa đủ nhiều
  - pct_close_below_SMA50 = 0.3792  
<img width="910" height="490" alt="image" src="https://github.com/user-attachments/assets/4e7a674f-2a00-4b9a-b48d-1ee1907883f6" />
<img width="1730" height="491" alt="image" src="https://github.com/user-attachments/assets/9d1a6d73-df4f-4a13-ae7b-fc7c89e6ae72" />
<img width="1254" height="597" alt="image" src="https://github.com/user-attachments/assets/2d77ca15-8bc0-4c09-abd2-99ff0e05b16c" />


3. Kiểm tra đặc trưng mean-reversion của cổ phiếu Coca Cola:
- Về mặt tổng thể, cổ phiếu Coca Cola thể hiện yếu ở đặc trưng mean-reversion:
  - autocorr = -0.07382 < 0 : cho thấy returns có khuynh hướng đảo chiều nhẹ, không có sự nối tiếp rõ rệt.
  - adx_median = 21.24095 > 20 => ADX trung vị lớn 20 nhưng không quá nhiều, chứng tỏ xu hướng thị trường chưa quá mạnh, không bền vững.
  - total_crosses_per_year: 20.31105 => nghĩa là trung bình khoảng 1 lần cắt mỗi ~12-13 ngày giao dịch, có hơi hướng biến động ngắn hạn.  
<img width="913" height="498" alt="image" src="https://github.com/user-attachments/assets/5911d76c-4388-4507-b685-00a31a0b4cd9" />
<img width="1734" height="493" alt="image" src="https://github.com/user-attachments/assets/1ec067dd-09bf-4dad-925e-76b6bc957e3c" />
<img width="1731" height="618" alt="image" src="https://github.com/user-attachments/assets/8cace39a-f18b-4ad9-88f6-985c77836646" />

4. Kiểm tra đặc điểm của cổ phiếu Coca Cola theo return từng tháng và từng quý:  
trung bình trong khoảng 10 năm (2005 đến 2014) thì cho ta thấy tháng 3, 9 và 11 là các tháng có trung bình return cao nhất và các khoảng thời gian từ tháng 3-5 và tháng 9-11 cũng thường xuyên có lợi nhuận dương và tăng trưởng mạnh ở các năm (Điều này có thể do các khoảng thời gian này rơi vào mùa lễ hội và các ngày nghỉ lễ lớn ở các quốc gia tiêu thụ lượng lớn Coca Cola ví dụ như các ngày lễ lớn ở Mexico vào 5/5 hay 1-2/11 hay Independence day vào 16/9,...). Do đó ta có thể xây dựng một chiến lược giao dịch theo mùa vào 2 khoảng thời gian từ tháng 3-5 và tháng 9-11 hằng năm.  
<img width="1500" height="628" alt="image" src="https://github.com/user-attachments/assets/a08bd1af-71b9-461f-805e-9e70809e6a9f" />
<img width="1496" height="624" alt="image" src="https://github.com/user-attachments/assets/0ff92725-c833-4846-befe-299b1c72651c" />
<img width="1497" height="632" alt="image" src="https://github.com/user-attachments/assets/460cdd70-60b4-44ae-b2f1-024f43d34e9b" />
<img width="1496" height="619" alt="image" src="https://github.com/user-attachments/assets/1f2a72e6-f041-411c-b234-5019dd1f7b0b" />
<img width="1496" height="627" alt="image" src="https://github.com/user-attachments/assets/05d6892f-72bd-4712-ac6d-3b87b31af1eb" />

5. Kiểm tra các đặc điểm Pattern Up Down:
- D → U = 53.23% : Sau khi giảm, giá có xác suất hồi phục không quá cao
- U → U = 52.07% : Khi đã tăng, giá có xác suất tiếp tục tăng cũng chỉ hơi nhỉnh hơn 50% một tí khoảng 2.07% (không đáng kể)
- Cả hai xác suất (D→U và U→U) đều chỉ hơi lệch khỏi 50%.
--> Điều này cho thấy hành vi giá không thiên mạnh về trend-following, và cũng không quá thiên về mean-reversion.  
<img width="1735" height="386" alt="image" src="https://github.com/user-attachments/assets/838f0426-2ccb-44cb-b776-49ba4dc9592c" />

### **Chiến lược giao dịch cổ phiếu Coca - Cola:**
Dựa trên phân tích trước về đặc điểm của cổ phiếu Coca-Cola, ta ghi nhận một số điểm quan trọng:
- Không có xu hướng mạnh: ADX thấp và autocorrelation âm cho thấy giá không duy trì trend dài hạn; do đó các chiến lược trend-following kém hiệu quả.
- Mean-reversion cũng không quá rõ ràng: không đủ mạnh để xây dựng chiến lược mean-reversion độc lập.
- Mùa vụ rõ rệt: Hiệu ứng mùa vụ thể hiện khá ổn định — cổ phiếu thường mạnh vào quý Q3 và Q4, đặc biệt các tháng 3 / 9 / 11, trong khi tháng 1 thường yếu.
Từ các quan sát này, ta quyết định ưu tiên một chiến lược mùa vụ ngắn hạn thay vì mean-reversion hoặc trend.

#### **Chiến lược giao dịch dựa trên Pattern seasonality:**
**CHI TIẾT TRONG FILE trading_strategy_season_backtest.ipynb**  

Chiến lược này chỉ hoạt động trong 2 giai đoạn: Tháng 3 - Tháng 5 và Tháng 9 - Tháng 11
1. Mua Ban Đầu (Entry)
- Thời điểm: Ngày giao dịch đầu tiên của tháng (ví dụ: ngày 1/3, 1/9)
- Hành động: MUA tại Giá Mở Cửa (OPEN).

2. Chu Kỳ Thoát/Vào Lại (Buy-Sell Cycle)
Mỗi ngày, hãy kiểm tra Giá Đóng Cửa (CLOSE) so với Giá Mua Ban Đầu (Entry Price) của vị thế hiện tại:
- Nếu Lời >= 5% HOẶC Lỗ <= 5%:
  - BÁN tại giá mở cửa (OPEN) của NGÀY HÔM SAU.
  - Sau đó, MUA LẠI ngay tại giá đóng cửa (CLOSE) của chính ngày bán đó.
3. Kết Thúc Giai Đoạn (Exit)
- Thời điểm: Ngày giao dịch cuối cùng của tháng 5 hoặc tháng 11.
- Hành động: Luôn BÁN tại Giá Mở Cửa (OPEN) của ngày cuối cùng đó để kết thúc vị thế và chờ đợi mùa giao dịch tiếp theo.


Hình ảnh giao dịch từng năm:
<img width="834" height="364" alt="image" src="https://github.com/user-attachments/assets/9796a5c0-477d-4c56-b789-c29c5b0deddd" />
<img width="839" height="361" alt="image" src="https://github.com/user-attachments/assets/c9ba7c93-3724-48cd-994b-857543b977ab" />
<img width="1116" height="474" alt="image" src="https://github.com/user-attachments/assets/d57b85ab-b27c-42ef-be58-619ea8e30dd1" />
(Ghi chú: Vì dữ liệu có một vài năm không đủ số tháng trong giai đoạn nên chiến lược sẽ không thực hiên mua/bán trong các giai đoạn đó (VD: tháng 10 năm 2015 và tháng 9 năm 2025))

## **Phân tích kết quả và đánh giá chiến lược:**

| Metric              | Value   |
|---------------------|---------|
| Number of trades    | 61      |
| Total return (%)    | 74.34   |
| Win rate (%)        | 59.02   |
| CAGR (%)            | 6.20    |
| Max drawdown (%)    | -26.57  |

**Nhận xét**
- Tổng lợi nhuận đạt 74.34%, chứng tỏ chiến lược có khả năng sinh lời. Tỷ lệ thắng 59.02% ở mức khá, cho thấy các tín hiệu giao dịch có độ tin cậy tương đối tốt.
- Tuy nhiên, CAGR chỉ đạt 6.20% mỗi năm, trong khi mức drawdown tối đa lên tới -26.57%, cho thấy chiến lược vẫn chịu rủi ro giảm vốn tương đối lớn so với mức tăng trưởng đạt được.

**Yearly Performance:**
| Year | Return (%) | Contribution (%) |
|------|------------|------------------|
| 2016 | 0.19       | 0.26             |
| 2017 | 10.57      | 14.25            |
| 2018 | 14.94      | 22.27            |
| 2019 | 8.54       | 14.63            |
| 2020 | 5.35       | 9.94             |
| 2021 | 7.97       | 15.62            |
| 2022 | 12.77      | 27.01            |
| 2023 | 0.08       | 0.20             |
| 2024 | -5.13      | -12.25           |
| 2025 | 3.57       | 8.07             |

**Consistency Metrics:**
| Metric                    | Value   |
|---------------------------|---------|
| Positive year ratio (%)   | 90.00   |
| Max year contribution (%) | 27.01   |

**Nhận xét:**
- Positive year ratio: 90.00% --> Khoảng 9/10 số năm có lợi nhuận dương, thể hiện sự ổn định tương đối của chiến lược qua các năm. Năm duy nhất có return âm là năm 2024, nguyên nhân có thể do yếu tố bên ngoài.
- Max year contribution: 27.01% --> phần trăm lợi nhuận của năm cao nhất lên tới 27.01% nhưng không áp đảo với các năm còn lại.
- Với hầu hết các lợi nhuần đều từ 8% đến hơn 20% thì cao hơn so với lãi suất gửi ngân hàng bình quân ở Việt Nam --> Có thể đánh giá chiến lược giao dịch này vẫn mang lại lợi nhuận tốt hơn, nhưng vẫn chịu rủi ro cao hơn so với khi thực hiện các biện pháp đầu tư sinh lời khác như gửi tiệt kiệm,...

**Seasonal Performance Summary:**
| Year | Season   | Return (%) | Equity Change | Contribution (%) |
|------|----------|------------|---------------|------------------|
| 2016 | Mar-May  | 3.88       | 3,884         | 1992.97          |
| 2016 | Sep-Nov  | -3.55      | -3,689        | -1892.97         |
| 2017 | Mar-May  | 10.24      | 10,238        | 94.93            |
| 2017 | Sep-Nov  | 0.50       | 547           | 5.07             |
| 2018 | Mar-May  | 13.85      | 13,855        | 50.67            |
| 2018 | Sep-Nov  | 11.85      | 13,487        | 49.33            |
| 2019 | Mar-May  | 38.97      | 38,975        | 101.99           |
| 2019 | Sep-Nov  | -0.55      | -760          | -1.99            |
| 2020 | Mar-May  | 39.38      | 39,377        | 86.34            |
| 2020 | Sep-Nov  | 4.47       | 6,229         | 13.66            |
| 2021 | Mar-May  | 65.42      | 65,417        | 114.34           |
| 2021 | Sep-Nov  | -4.96      | -8,203        | -14.34           |
| 2022 | Mar-May  | 67.79      | 67,788        | 87.71            |
| 2022 | Sep-Nov  | 5.66       | 9,502         | 12.29            |
| 2023 | Mar-May  | 81.07      | 81,070        | 104.69           |
| 2023 | Sep-Nov  | -2.00      | -3,630        | -4.69            |
| 2024 | Mar-May  | 85.05      | 85,052        | 124.46           |
| 2024 | Sep-Nov  | -9.03      | -16,717       | -24.46           |
| 2025 | Mar-May  | 74.34      | 74,337        | 100.00           |

Theo tóm tắt return_pct theo mùa (ở 2 giai đoạn tháng 3-5 và tháng 9-11) ở các năm, thì tháng 3-5 luôn đóng góp phần lớn trong việc giao dịch đem lại lợi nhuận và tháng 9-11 có nhiều năm đem lại lợi nhuận âm. --> Ta có hướng phát triển tiếp theo, có thể chỉ sử dụng giao dịch theo mùa vụ ở tháng 3-5 để tối ưu hơn và tránh rủi ro hơn cho giao dịch ở các năm tiếp theo và với các tháng khác ta có thể xây dựng thêm một chiến lược giao dịch mới, phù hợp hơn.

## **Cải tiến và đánh giá**
Nhóm em có 2 hướng cải tiến cho bài toán xây dựng chiến lược giao dịch cho cổ phiếu Coca Cola như sau:
- Thứ nhất, với chiến lược giao dịch theo mùa, thì ta có thể thay đổi bằng cách chỉ giao dịch tại giai đoạn 3-5 để tránh rủi ro và xây dựng thêm một chiến lược giao dịch mới, phù hợp hơn cho các tháng còn lại.
- Thứ hai, theo quan sát được khi trực quan về giá cổ phiếu (OPEN) của Coca Cola thì nhóm em vẫn thấy được đặc điểm theo trend và mean-reversion của cổ phiếu này ở các khoảng thời gian nhỏ hơn. Do đó, nhóm em dự định sẽ:
  - Trực quan thêm ở các timeframe nhỏ hơn như một tuần (7 ngày) hay một tháng (21 ngày) để quan sát thêm.
  - Hoặc có thể kết hợp cả 2 chiến lược giao dịch theo trend following và mean-reversion vào thành một chiến lược giao dịch mới cho cổ phiếu Coca Cola. Bởi nhóm em quan sát được trong khoảng năm 2006-2010 thì giá cổ phiếu của Coca Cola dao động quanh giá 15 (có thể vẽ được đường mean tại giá 15 --> áp dụng được mean-reversion) và từ năm 2010 đến năm 2015 thì giá cổ phiếu hầu như tăng trưởng và tăng trường với xu hướng nhanh do đó có thể thử áp dụng chiến lược giao dịch theo trend-following.  
    **CHÈN HÌNH ẢNH**
