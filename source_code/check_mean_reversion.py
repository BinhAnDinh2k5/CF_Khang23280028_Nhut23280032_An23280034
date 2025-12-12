import numpy as np
import pandas as pd
import talib
import matplotlib.pyplot as plt
from scipy.stats import linregress
import matplotlib.dates as mdates




# Tính các indicators
def compute_indicators_mean_reversion(df):
    df = df.copy()

    # Return
    df['Return'] = df['Close'].pct_change()

    # Long-term SMA
    df['SMA50'] = df['Close'].rolling(50).mean()

    # ADX
    df['ADX'] = talib.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)

    return df


# Kiểm tra autocorrelation
def check_autocorrelation_mr(df):
    return df['Return'].autocorr(lag=1)


# Kiểm tra ADX
def check_adx_mr(df):
    return df['ADX'].median()


# Hàm tính số lần cắt SMA trung hạn
def check_cross_per_year(df, sma_col='SMA50', price_col='Close'):

    df = df.copy()
    df[sma_col] = df[price_col].rolling(50).mean()
    df = df.dropna(subset=[sma_col, price_col])

    # Số lần cắt
    prev_price = df[price_col].shift(1)
    prev_sma = df[sma_col].shift(1)
    cross_up = (prev_price < prev_sma) & (df[price_col] > df[sma_col])
    cross_down = (prev_price > prev_sma) & (df[price_col] < df[sma_col])
    total_crosses = cross_up.sum() + cross_down.sum()

    n_days = df.shape[0]

    crosses_per_year = total_crosses/n_days * 252

    return crosses_per_year

# Hàm kiểm tra pattern mean_reversion
def check_mean_reversion(df, sma_band_pct=0.02):
    df = compute_indicators_mean_reversion(df)
    results = {}

    # Điều kiện 1: Autocorrelation
    results['autocorr'] = check_autocorrelation_mr(df)

    # Điều kiện 2: ADX
    results['adx_median'] = check_adx_mr(df)

    # Điều kiện 3: Trung bình số lần cắt đường  SMA dài hạn trong năm 
    results['total_crosses_per_year'] = check_cross_per_year(df)

    return results


# Trực quan autocorrelation
def plot_autocorrelation_mr(df):
    data = df[['Return']].dropna()

    x = data['Return'][:-1]
    y = data['Return'].shift(-1)[:-1]

    slope, intercept, r, p, _ = linregress(x, y)

    plt.figure(figsize=(7,5))
    plt.scatter(x, y, alpha=0.5)
    plt.plot(x, intercept + slope*x, color='red', lw=2)
    plt.axhline(0, color='black', lw=0.5)
    plt.axvline(0, color='black', lw=0.5)

    plt.title(f"Return Autocorrelation (lag=1), slope = {slope:.3f}")
    plt.xlabel("Return[t]")
    plt.ylabel("Return[t+1]")
    plt.grid(True)
    plt.show()


# Trực quan ADX
def plot_adx_mr(df):

    df = compute_indicators_mean_reversion(df)

    if 'ADX' not in df.columns:
        print("Không tìm thấy cột 'ADX' trong DataFrame.")
        return

    adx = df['ADX'].dropna()
    if adx.empty:
        print("Không có giá trị ADX để vẽ.")
        return

    median_adx = adx.median()
    pct_below_20 = (adx < 20).mean()
    pct_above_25 = (adx > 25).mean()

    fig, axs = plt.subplots(1, 2, figsize=(14, 4))

    # (1) ADX time series + shaded LOW-ADX regime
    axs[0].plot(adx.index, adx.values, label='ADX')
    axs[0].axhline(20, color='green', linestyle='--', label='Low trend threshold = 20')
    axs[0].axhline(25, color='red', linestyle='--', label='Strong trend threshold = 25')

    # Shade where ADX < 20  (mean-reversion regime)
    low_trend_mask = adx < 20
    if low_trend_mask.any():
        axs[0].fill_between(
            adx.index,
            adx.values,
            20,
            where=low_trend_mask,
            interpolate=True,
            alpha=0.25,
            color='green',
            label='ADX < 20 (Mean-Reversion regime)'
        )

    axs[0].set_title("ADX Over Time (Mean-Reversion Check)")
    axs[0].set_xlabel("Date")
    axs[0].set_ylabel("ADX")
    axs[0].legend()
    axs[0].grid(True)

    axs[0].xaxis.set_major_locator(mdates.AutoDateLocator())
    axs[0].xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(mdates.AutoDateLocator())
    )

    # (2) ADX distribution + median
    axs[1].hist(adx.values, bins=30, edgecolor='k', alpha=0.7)
    axs[1].axvline(
        median_adx,
        color='blue',
        lw=2,
        label=f"median ADX = {median_adx:.2f}"
    )

    axs[1].set_title("ADX Distribution")
    axs[1].set_xlabel("ADX value")
    axs[1].set_ylabel("Frequency")
    axs[1].legend()
    axs[1].grid(True)

    # Annotation: interpretability
    axs[0].text(
    0.01, 0.99,
    "ADX Over Time\n(Low ADX = Mean-Reversion regime)",
    transform=axs[0].transAxes,
    verticalalignment='top',
    horizontalalignment='left',
    bbox=dict(facecolor='white', alpha=0.75, edgecolor='none')
)


    plt.tight_layout()
    plt.show()



def get_sma_crosses_df(df, sma_col='SMA50', price_col='Close'):
    """
    Trả về DataFrame các lần cross với cột: date, type ('up'/'down'), price, sma.
    Yêu cầu: df đã có cột SMA (ví dụ 'SMA50') hoặc sẽ tính SMA50 tại đây.
    """
    df = df.copy()
    # đảm bảo có SMA50
    if sma_col not in df.columns:
        df[sma_col] = df[price_col].rolling(50).mean()

    df = df.dropna(subset=[sma_col, price_col]).copy()
    if df.empty:
        return pd.DataFrame(columns=['date', 'type', 'price', 'sma'])

    prev_price = df[price_col].shift(1)
    prev_sma = df[sma_col].shift(1)

    cross_up_mask = (prev_price < prev_sma) & (df[price_col] > df[sma_col])
    cross_down_mask = (prev_price > prev_sma) & (df[price_col] < df[sma_col])

    # Lấy ngày/idx cho mỗi điểm cắt
    if 'Date' in df.columns:
        dates = df['Date']
    else:
        dates = df.index

    crosses = []
    for idx in df.index[cross_up_mask]:
        crosses.append({'date': dates.loc[idx] if hasattr(dates, 'loc') else dates[idx],
                        'type': 'up',
                        'price': float(df.loc[idx, price_col]),
                        'sma': float(df.loc[idx, sma_col])})
    for idx in df.index[cross_down_mask]:
        crosses.append({'date': dates.loc[idx] if hasattr(dates, 'loc') else dates[idx],
                        'type': 'down',
                        'price': float(df.loc[idx, price_col]),
                        'sma': float(df.loc[idx, sma_col])})

    crosses_df = pd.DataFrame(crosses)
    # sắp theo thời gian
    if not crosses_df.empty:
        crosses_df = crosses_df.sort_values('date').reset_index(drop=True)

    return crosses_df


def plot_price_with_sma_crosses(df, sma_window=50, marker_size=60):

    df = df.copy()
    # đảm bảo cột Date nếu có, hoặc dùng index
    if sma_window != 50:
        df['SMA'] = df['Close'].rolling(sma_window).mean()
        sma_col = 'SMA'
    else:
        df['SMA50'] = df['Close'].rolling(50).mean()
        sma_col = 'SMA50'

    # x-axis
    if 'Date' in df.columns:
        x = pd.to_datetime(df['Date'])
    else:
        x = pd.to_datetime(df.index)

    # compute crosses and crosses_per_year
    crosses_df = get_sma_crosses_df(df, sma_col=sma_col, price_col='Close')
    crosses_per_year = check_cross_per_year(df, sma_col=sma_col, price_col='Close')

    plt.figure(figsize=(14,5))
    plt.plot(x, df['Close'], label='Close', linewidth=1)
    plt.plot(x, df[sma_col], linestyle='--', label=f'SMA{sma_window}', linewidth=1.25)

    # plot crosses
    if not crosses_df.empty:
        # up
        ups = crosses_df[crosses_df['type'] == 'up']
        downs = crosses_df[crosses_df['type'] == 'down']
        if not ups.empty:
            up_x = pd.to_datetime(ups['date'])
            plt.scatter(up_x, ups['price'], marker='^', s=marker_size, label='cross up', edgecolor='k', zorder=5)
        if not downs.empty:
            down_x = pd.to_datetime(downs['date'])
            plt.scatter(down_x, downs['price'], marker='v', s=marker_size, label='cross down', edgecolor='k', zorder=5)

    plt.title(f'Price & SMA{str(sma_window)} — SMA crosses/year ≈ {crosses_per_year:.1f}')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)

    # nicer date formatting
    try:
        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
    except Exception:
        pass

    plt.tight_layout()
    plt.show()

    return crosses_df
