import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional, Iterable
import numpy as np

# Tham số mặc định
INITIAL_CAPITAL = 100000
STOP_LOSS = -0.05    # -5%
TAKE_PROFIT = 0.05   # +5%

def ensure_datetime_index(df, date_col='Date'):
    """Đảm bảo df có DatetimeIndex; nếu có cột Date sẽ dùng nó làm index."""
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', utc=True).dt.tz_convert(None)
        df = df.dropna(subset=[date_col])
        df = df.sort_values(date_col)
        df = df.set_index(date_col)
    else:
        # nếu index là object/int, cố gắng convert index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, errors='coerce', utc=True).tz_convert(None)
            df = df.dropna(axis=0, subset=[df.columns[0]])  # giữ rows có giá
    df.index = pd.DatetimeIndex(df.index)  
    return df


def get_nearest_trading_day_after(target_date, trading_index):
    """
    Trả về ngày giao dịch đầu tiên **sau hoặc bằng target_date**.
    """
    target_date = pd.Timestamp(target_date)
    future = trading_index[trading_index >= target_date]  # chỉ lấy ngày >= target_date
    if len(future) > 0:
        return future[0]
    return None

def is_last_day_of_period(idx, i, end_m):
    """Kiểm tra xem ngày idx[i] có phải ngày cuối period không."""
    if idx[i].month != end_m:
        return False
    
    # Nếu ngày tiếp theo khác tháng → current = ngày cuối
    return (i == len(idx) - 1) or (idx[i+1].month != end_m)


# Chạy chiến lược giao dịch
def run_strategy(df,
                 initial_capital=INITIAL_CAPITAL,
                 stop_loss=STOP_LOSS,
                 take_profit=TAKE_PROFIT):

    df = ensure_datetime_index(df)

    if "Open" not in df.columns or "Close" not in df.columns:
        raise KeyError("DataFrame phải có cột Open và Close")

    idx = df.index
    periods = [(3, 5), (9, 11)]
    capital = float(initial_capital)

    trades = []

    for year in range(idx[0].year, idx[-1].year + 1):
        for start_m, end_m in periods:

            # Tìm ngày đầu period 
            raw_day = pd.Timestamp(year, start_m, 1)

            entry_date = get_nearest_trading_day_after(raw_day, idx)

            # Kiểm tra có tồn tại ngày giao dịch trong tháng start_m không
            if entry_date is None or entry_date.month != start_m:
                continue
            
            entry_price = df.loc[entry_date, "Open"]
            shares = int(capital // entry_price)
            if shares <= 0:
                continue

            # Bắt đầu kiểm tra tín hiệu từ ngày BUY (CLOSE của entry_date)
            i = idx.get_loc(entry_date)

            while i < len(idx):

                today = idx[i]

                # --- 1. End of period ---
                if is_last_day_of_period(idx, i, end_m):
                    exit_date = today
                    exit_price = df.loc[exit_date, "Open"]
                    capital = shares * exit_price

                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": exit_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": shares,
                        "return_pct": (exit_price / entry_price - 1) * 100,
                        "capital_after": capital,
                        "reason": "period_end"
                    })
                    break

                # --- 2. Stop Loss / Take profit signal  ---
                change = df.loc[today, "Close"] / entry_price - 1

                if (change <= stop_loss) or (change >= take_profit):

                    exec_i = i + 1
                    if exec_i >= len(idx):
                        exit_date = today
                        exit_price = df.loc[today, "Open"]
                    else:
                        exit_date = idx[exec_i]
                        exit_price = df.loc[exit_date, "Open"]

                    capital = shares * exit_price

                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": exit_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "shares": shares,
                        "return_pct": (exit_price / entry_price - 1) * 100,
                        "capital_after": capital,
                        "reason": "TP" if change >= take_profit else "SL"
                    })

                    # --- 3. Tái mua nếu còn trong giai đoạn ---
                    if start_m <= exit_date.month <= end_m:
                        entry_date = exit_date
                        entry_price = df.loc[entry_date, "Close"]   # giá tái mua
                        shares = int(capital // entry_price)
                        if shares <= 0:
                            break
                        i = exec_i  # tiếp tục từ ngày sau khi SELL
                        continue
                    else:
                        break

                i += 1

    return pd.DataFrame(trades)

# Trực quan lịch sử giao dịch
def plot_trades(df, trades_df):
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True).dt.tz_convert(None)
    df = df.dropna(subset=['Date']).set_index('Date').sort_index()
    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df["Open"], label="Open", linewidth=1)

    if not trades_df.empty:

        # BUY markers (always at Open)
        buy_dates = trades_df["entry_date"]
        buy_prices = df.loc[buy_dates, "Open"]
        plt.scatter(buy_dates, buy_prices, marker="^", color="green", s=90, label="Buy")

        # SELL markers (always at Open)
        sell_dates = trades_df["exit_date"]
        sell_prices = df.loc[sell_dates, "Open"]
        plt.scatter(sell_dates, sell_prices, marker="v", color="red", s=90, label="Sell")

    plt.legend()
    plt.grid(True)
    plt.show()


# Trực quan lịch sử giao dịch theo năm
def plot_trades_by_year(df, trades_df, date_fmt="%m-%Y", show_legend=True):
    """
    Vẽ một biểu đồ cho mỗi năm.
    """
    df = ensure_datetime_index(df)
    if trades_df is None or trades_df.empty:
        # nếu không có lệnh thì vẫn vẽ mỗi năm giá
        years = sorted(set(df.index.year))
        trades_df = pd.DataFrame(columns=["entry_date","exit_date","entry_price","exit_price","shares","reason"])
    else:
        # đảm bảo datetime
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        years = sorted(set(df.index.year))

    for year in years:
        # subset giá của năm
        mask_year = df.index.year == year
        df_year = df.loc[mask_year]
        if df_year.empty:
            continue

        # lấy trades có entry hoặc exit trong năm này
        mask_trades = (
            (trades_df['entry_date'].dt.year == year) |
            (trades_df['exit_date'].dt.year == year)
        ) if not trades_df.empty else pd.Series([], dtype=bool)

        trades_year = trades_df[mask_trades] if not trades_df.empty else pd.DataFrame(columns=trades_df.columns)

        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(df_year.index, df_year["Open"], linewidth=1, label="Open")

        # các marker BUY (nếu có và nằm trong df_year.index)
        if not trades_year.empty:
            buy_dates = trades_year['entry_date']
            buy_in_index = df_year.index.intersection(buy_dates)
            if len(buy_in_index) > 0:
                buy_prices = df_year.loc[buy_in_index, "Open"]
                ax.scatter(buy_prices.index, buy_prices.values, marker="^", s=90, label="Buy", zorder=5, color = 'green')

            sell_dates = trades_year['exit_date']
            sell_in_index = df_year.index.intersection(sell_dates)
            if len(sell_in_index) > 0:
                sell_prices = df_year.loc[sell_in_index, "Open"]
                ax.scatter(sell_prices.index, sell_prices.values, marker="v", s=90, label="Sell", zorder=5, color = 'red')

        # format trục x
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_fmt))
        ax.set_title(f"Backtest - Year {year}")
        ax.set_xlabel("Date (dd-mm-yyyy)")
        ax.set_ylabel("Price (Open)")
        ax.grid(True)

        if show_legend:
            ax.legend()

        # xoay label, tight layout
        fig.autofmt_xdate(rotation=45, ha='right')
        fig.tight_layout()


        plt.show()

# Tính thông số cơ bản
def compute_basic_metrics(trades_df, initial_capital=INITIAL_CAPITAL):
    if trades_df.empty:
        return None

    df = trades_df.copy()

    # ---------- 1. Number of trades ----------
    n_trades = len(df)

    # ---------- 2. Total return ----------
    final_capital = df.iloc[-1]["capital_after"]
    total_return = final_capital / initial_capital - 1

    # ---------- 3. Win rate ----------
    win_rate = (df["return_pct"] > 0).mean()

    # ---------- 4. Equity curve ----------
    equity = pd.Series(
        [initial_capital] + df["capital_after"].tolist()
    )

    # ---------- 5. Max Drawdown ----------
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max
    max_drawdown = drawdown.min()   # giá trị âm

    # ---------- 6. CAGR ----------
    start_capital = equity.iloc[0]
    end_capital = equity.iloc[-1]

    start_date = df["entry_date"].iloc[0]
    end_date = df["exit_date"].iloc[-1]

    num_years = (end_date - start_date).days / 365.25

    if num_years <= 0:
        cagr = np.nan
    else:
        cagr = (end_capital / start_capital) ** (1 / num_years) - 1


    return {
        "Number of trades": n_trades,
        "Total return (%)": total_return * 100,
        "Win rate (%)": win_rate * 100,
        "CAGR (%)": cagr * 100,
        "Max drawdown (%)": max_drawdown * 100
    }

def plot_equity_curve(trades_df, initial_capital, title="Equity Curve"):
    if trades_df.empty:
        return

    df = trades_df.copy()
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    df = df.sort_values("exit_date").reset_index(drop=True)

    # Tạo equity series
    equity_dates = [df["entry_date"].iloc[0]] + df["exit_date"].tolist()
    equity_values = [initial_capital] + df["capital_after"].tolist()

    equity = pd.Series(equity_values, index=equity_dates)

    # Plot
    plt.figure(figsize=(12, 5))
    plt.plot(equity.index, equity.values, linewidth=2)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(alpha=0.3)
    plt.show()

    return equity


# Vẽ đồ thị equity & drawdown
def plot_equity_and_drawdown(trades_df, initial_capital, title="Equity & Drawdown"):
    if trades_df.empty:
        return

    df = trades_df.copy()
    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])
    df = df.sort_values("exit_date").reset_index(drop=True)

    # Equity
    equity_dates = [df["entry_date"].iloc[0]] + df["exit_date"].tolist()
    equity_values = [initial_capital] + df["capital_after"].tolist()
    equity = pd.Series(equity_values, index=equity_dates)

    # Drawdown
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max

    # Plot
    fig, ax1 = plt.subplots(figsize=(13, 6))

    ax1.plot(equity.index, equity.values, linewidth=2)
    ax1.set_ylabel("Equity")
    ax1.set_title(title)
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.fill_between(drawdown.index, drawdown.values * 100, 0, alpha=0.3)
    ax2.set_ylabel("Drawdown (%)")

    plt.show()

    return equity, drawdown
