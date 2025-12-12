import pandas as pd
import talib
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress
import matplotlib.dates as mdates

# Tính các indicators
def compute_indicators(df):
    df = df.copy()
    df['Return'] = df['Close'].pct_change()

    # ADX
    df['ADX'] = talib.ADX(df['High'], df['Low'], df['Close'], timeperiod=14)

    # Tính SMA
    df['SMA50'] = df['Close'].rolling(50).mean()

    return df

# Kiểm tra AUTOCORRELATION
def check_autocorrelation(df):
    return df['Return'].autocorr(lag=1)


# Kiểm tra ADX TREND STRENGTH

def check_adx(df):
    return df['ADX'].median()  # median để tránh outliers



# Kiểm tra pattern trend_following
def check_trend_following(df):
    df = compute_indicators(df)
    results = {}

    # Indicators
    results['autocorr'] = check_autocorrelation(df)
    results['adx_median'] = check_adx(df)
    results['pct_close_above_SMA50'] = (df['Close'] > df['SMA50']).mean()
    results['pct_close_below_SMA50'] = (df['Close'] < df['SMA50']).mean()

    # Linear regression trên SMA50 để tính slope trend
    valid_idx = ~df['SMA50'].isna()  # loại NaN đầu window
    x = np.arange(len(df[valid_idx]))
    y = df.loc[valid_idx, 'SMA50'].values
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    results['SMA50_slope'] = slope

    # Xác định trend direction
    trend_direction = None
    score = 0

    # Trend UP
    if slope > 0 and results['pct_close_above_SMA50'] > 0.6:
        trend_direction = "up"

    # Trend DOWN
    elif slope < 0 and results['pct_close_below_SMA50'] > 0.6:
        trend_direction = "down"

    else:
        trend_direction = "none"


    
    results['trend_direction'] = trend_direction
    return results




# -----------------------------------------------------------
# Plot 1: Autocorrelation scatter + regression
# -----------------------------------------------------------
def plot_autocorrelation(df):
    df = compute_indicators(df)
    # ensure Return exists
    if 'Return' not in df.columns:
        df['Return'] = df['Close'].pct_change()

    # align x = Return[t], y = Return[t+1]
    returns = df['Return'].dropna()
    if len(returns) < 2:
        print("Không đủ dữ liệu để vẽ autocorrelation.")
        return

    x = returns.iloc[:-1].values
    y = returns.iloc[1:].values

    # regression
    slope, intercept, r_value, p_value, stderr = linregress(x, y)

    plt.figure(figsize=(8,4))
    plt.scatter(x, y, alpha=0.4, s=20)
    xs = np.linspace(x.min(), x.max(), 100)
    plt.plot(xs, intercept + slope*xs, lw=2, label=f"regression (r={r_value:.3f})", color = 'red')
    plt.title("Autocorrelation: Return[t] vs Return[t+1]")
    plt.xlabel("Return[t]")
    plt.ylabel("Return[t+1]")
    plt.grid(True)
    plt.legend(loc='upper left')


    plt.show()


# -----------------------------------------------------------
# Plot 2: ADX over time + histogram with median & pct > 25
# -----------------------------------------------------------
def plot_adx(df):

    df = compute_indicators(df)
    if 'ADX' not in df.columns:
        print("Không tìm thấy cột 'ADX' trong DataFrame.")
        return

    adx = df['ADX'].dropna()
    if adx.empty:
        print("Không có giá trị ADX để vẽ.")
        return

    pct_above = (adx > 25).mean()
    median_adx = adx.median()

    fig, axs = plt.subplots(1, 2, figsize=(14,4))

    # ADX time series with shaded ADX>25
    axs[0].plot(adx.index, adx.values, label='ADX')
    axs[0].axhline(25, color='red', linestyle='--', label='Threshold = 25')
    # shade where ADX>25
    mask = adx > 25
    if mask.any():
        axs[0].fill_between(adx.index, adx.values, 25, where=mask, interpolate=True, alpha=0.25, label='ADX > 25')
    axs[0].set_title("ADX Over Time")
    axs[0].set_xlabel("Date")
    axs[0].set_ylabel("ADX")
    axs[0].legend()
    axs[0].grid(True)
    axs[0].xaxis.set_major_locator(mdates.AutoDateLocator())
    axs[0].xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))

    # Histogram + median
    axs[1].hist(adx.values, bins=30, edgecolor='k', alpha=0.7)
    axs[1].axvline(median_adx, color='red', lw=2, label=f"median = {median_adx:.2f}")
    axs[1].set_title("ADX Distribution")
    axs[1].set_xlabel("ADX value")
    axs[1].set_ylabel("Frequency")
    axs[1].legend()
    axs[1].grid(True)

    # annotation (on the histogram)
    axs[1].text(0.02, 0.95, f"% days ADX>25 = {pct_above:.2%}", transform=axs[1].transAxes,
                verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

    plt.tight_layout()
    plt.show()
# -----------------------------------------------------------
# Plot 3: Price vs SMA50 + Linear Regression Slope + Shading
# -----------------------------------------------------------
def plot_sma_trend(df):
    df = compute_indicators(df)

    # ensure SMA50 exists
    if 'SMA50' not in df.columns:
        df['SMA50'] = df['Close'].rolling(50).mean()

    sma = df['SMA50'].dropna()
    if sma.empty:
        print("Không đủ dữ liệu để vẽ SMA50.")
        return

    # ----- Linear Regression on SMA -----
    x = np.arange(len(sma))
    slope, intercept, r_value, p_value, stderr = linregress(x, sma.values)

    reg_line = intercept + slope * x

    # % price above/below SMA
    pct_above = (df['Close'] > df['SMA50']).mean()
    pct_below = 1 - pct_above

    plt.figure(figsize=(12,5))
    
    # Price and SMA
    plt.plot(df['Date'], df['Close'], label='Close Price', alpha=0.7)
    plt.plot(df['Date'], df['SMA50'], label='SMA50', linewidth=2)

    # Regression line (align indices)
    plt.plot(df['Date'].iloc[-len(reg_line):], reg_line,
             label=f"SMA50 Regression (slope={slope:.4f})",
             color='red', linewidth=2)

    # Shade price above SMA50
    plt.fill_between(df['Date'], df['Close'], df['SMA50'],
                     where=(df['Close'] > df['SMA50']),
                     color='green', alpha=0.18, label='Price > SMA50')
    
    # Shade price below SMA50
    plt.fill_between(df['Date'], df['Close'], df['SMA50'],
                     where=(df['Close'] < df['SMA50']),
                     color='red', alpha=0.18, label='Price < SMA50')

    plt.title("Trend Direction: Price vs SMA50 + SMA50 Regression Slope")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.legend()
    
    # annotation
    plt.text(0.01, 0.93, 
             f"% Above SMA50 = {pct_above:.2%}\n% Below SMA50 = {pct_below:.2%}",
             transform=plt.gca().transAxes,
             bbox=dict(facecolor='white', alpha=0.7))

    plt.show()

