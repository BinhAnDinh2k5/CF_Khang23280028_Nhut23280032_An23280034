from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re
import time
import json
import pandas as pd
import os

chrome_options = Options() # Tạo đối tượng cấu hình cho Chrome
chrome_options.add_argument("--headless=new") # chạy trình duyệt ẩn
chrome_options.add_argument("--disable-gpu") # Tắt tăng tốc GPU để giảm lỗi khi chạy trên server
chrome_options.add_argument("--no-sandbox") # Tắt sandbox để tránh lỗi khi chạy trong môi trường không root
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Không tải ảnh
chrome_options.add_argument("--window-size=1920,1080")  # thêm kích thước cửa sổ
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36")

url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
# Khởi tạo trình điều khiển Chrome với cấu hình trên

driver = webdriver.Chrome(options=chrome_options) # Mở URL chỉ định

driver.get(url)

# Chờ trang load xong (có thể dùng WebDriverWait nếu trang load chậm)
import time
time.sleep(3)


base_folder = r'C:\Users\Dinh Binh An\OneDrive\Dai_hoc\toan_tai_chinh\giua_ki'

# Lấy tất cả các thẻ <tr> trong bảng
rows = driver.find_elements(By.CSS_SELECTOR, "table.wikitable.sortable tbody tr")

tickers = []

for row in rows:
    try:
        # Ticker nằm trong <td> đầu tiên, lấy text của <a>
        ticker = row.find_element(By.CSS_SELECTOR, "td:nth-child(1) a").text
        tickers.append(ticker)
    except:
        # Nếu row không có <td> hợp lệ (ví dụ header phụ) thì bỏ qua
        continue

driver.quit()

print(tickers)
print("Số lượng ticker: ",len(tickers))

ticker_file_csv = os.path.join(base_folder, 'tickers.csv')
try: 
    with open(ticker_file_csv, 'w') as file:
        header = 'Ticker\n'
        file.write(header)
        for ticker in tickers:
            file.write(f"{ticker}\n")
    print(f"Lưu {ticker_file_csv} thành công !")
except: 
    print(f"Lưu {ticker_file_csv} thất bại !")
