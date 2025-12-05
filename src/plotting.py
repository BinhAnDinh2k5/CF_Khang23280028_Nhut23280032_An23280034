# plotting.py
import os
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from core import logger, compute_drawdown
from trading_io import _to_series_from_equity_curve


# Vẽ biểu đồ giá + SMA short/long + đánh dấu điểm BUY/SELL dựa trên events_df
def plot_trades_for_ticker(price_df: pd.DataFrame, events_df: pd.DataFrame, short_w: int, long_w: int, out_path: str) -> None:


    t = price_df.copy()

     # Tính SMA ngắn và dài
    t["SMA_short"] = t["Close"].rolling(short_w, min_periods=short_w).mean()
    t["SMA_long"] = t["Close"].rolling(long_w, min_periods=long_w).mean()

    # Lấy các event mua/bán cho ticker hiện tại
    df_buy = events_df[(events_df.Ticker == price_df.name) & (events_df.Type == "BUY")]
    df_sell = events_df[(events_df.Ticker == price_df.name) & (events_df.Type == "SELL")]

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor("#F9FAFB")

    # Vẽ đường giá
    ax.plot(
        t.index, t["Open"],
        label="Price",
        linewidth=1.2,
        color="#444444",
        zorder=2
    )

    # Vẽ SMA ngắn
    ax.plot(
        t.index, t["SMA_short"],
        label=f"SMA {short_w}",
        linewidth=2.0,
        color="#1D4ED8",
        alpha=0.9,
        zorder=3
    )

    # Vẽ SMA dài
    ax.plot(
        t.index, t["SMA_long"],
        label=f"SMA {long_w}",
        linewidth=2.0,
        color="#F59E0B",
        alpha=0.9,
        zorder=3
    )

     # Nếu có lệnh BUY, vẽ marker mũi tên lên
    if not df_buy.empty:

        buy_dates = pd.to_datetime(df_buy["Date"], errors="coerce").dropna()

        try:
            # Loại timezone để khỏi mismatch khi reindex
            if buy_dates.dt.tz is not None:
                buy_dates = buy_dates.dt.tz_convert(None)
        except Exception:

            pass
        if len(buy_dates) > 0:
            # Lấy giá tại các ngày buy 
            buy_prices = price_df.reindex(buy_dates.values)["Open"]
            buy_prices = buy_prices.dropna()

            
            if not buy_prices.empty:
                ax.scatter(
                    buy_prices.index, buy_prices.values,
                    marker="^",
                    s=160,
                    color="#22C55E",
                    edgecolor="black",
                    linewidth=1,
                    label="BUY",
                    zorder=10,
                    alpha = 0.6
                )

    # Nếu có lệnh SELL, vẽ marker mũi tên xuống
    if not df_sell.empty:
        sell_dates = pd.to_datetime(df_sell["Date"], errors="coerce").dropna()
        try:
            if sell_dates.dt.tz is not None:
                sell_dates = sell_dates.dt.tz_convert(None)
        except Exception:
            pass
        if len(sell_dates) > 0:
            sell_prices = price_df.reindex(sell_dates.values)["Open"]
            sell_prices = sell_prices.dropna()
            if not sell_prices.empty:
                ax.scatter(
                    sell_prices.index, sell_prices.values,
                    marker="v",
                    s=160,
                    color="#EF4444",
                    edgecolor="black",
                    linewidth=1,
                    label="SELL",
                    zorder=10,
                    alpha = 0.6
                )

    # Trang trí biểu đồ: tiêu đề, nhãn, lưới, format trục x
    ax.set_title(f"{price_df.name} — SMA {short_w}/{long_w} Strategy Trades", fontsize=16, pad=15)
    ax.set_ylabel("Price", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.25)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    plt.xticks(rotation=45)
    plt.legend(frameon=True)

    # Lưu ảnh ra đường dẫn out_path
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

def plot_equity_curve(equity_curve: List[Tuple[pd.Timestamp, float]], out_path: str) -> None:
    
    # Vẽ đường equity của portfolio theo thời gian (Equity curve)
    if not equity_curve:
        logger.warning("Empty equity curve, nothing to plot")
        return
    df = pd.DataFrame(equity_curve, columns=["Date", "Equity"]).set_index("Date").sort_index()
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["Equity"], linewidth=1.5)
    plt.title("Portfolio Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.grid(True, linestyle="--", alpha=0.3)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


# Hàm vẽ biểu đồ Drawdown Curve
def plot_drawdown_curve(equity_curve: List[Tuple[pd.Timestamp, float]],
                        title: str = "Drawdown Curve",
                        out_path: Optional[str] = None,
                        show: bool = True) -> None:

    equity = _to_series_from_equity_curve(equity_curve)
    if equity.empty:
        raise ValueError("Equity curve is empty")

    dd = compute_drawdown(equity)

    plt.figure(figsize=(10, 6))
    plt.plot(dd.index, dd.values)
    plt.axhline(0, linestyle="--", linewidth=0.7)
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Drawdown (fraction)")
    plt.grid(True)
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path, bbox_inches="tight")
