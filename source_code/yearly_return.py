
import pandas as pd
import matplotlib.pyplot as plt
from typing import Callable, Tuple
from matplotlib.ticker import MaxNLocator
from IPython.display import display 

# Season classification
def default_season_mapper(month: int) -> str:
    """
    Gán season dựa trên tháng entry.

    Mar–Jul  : 3–5
    Oct–Dec  : 9–11
    Other    : còn lại
    """
    if 3 <= month <= 5:
        return "Mar-May"
    if month in (9, 10, 11):
        return "Sep-Nov"
    return "Other"




# Preprocess trades (add year, season, filter)
def prepare_seasonal_trades(
    trades: pd.DataFrame,
    season_mapper: Callable[[int], str] = default_season_mapper,
    drop_other: bool = True,
) -> pd.DataFrame:
    """
    Thêm cột year, month, season và (tùy chọn) loại bỏ trades ngoài season.
    """
    df = trades.copy()

    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["exit_date"] = pd.to_datetime(df["exit_date"])

    df["year"] = df["exit_date"].dt.year
    df["month"] = df["entry_date"].dt.month
    df["season"] = df["month"].apply(season_mapper)

    if drop_other:
        df = df[df["season"] != "Other"]

    return df




# Yearly equity-based return
def compute_yearly_equity_stats(
    trades: pd.DataFrame,
    initial_capital: float,
) -> pd.DataFrame:
    """
    Tính thống kê theo năm dựa trên equity thực tế.

    Trả về DataFrame:
        index: year
        columns:
            - start_equity
            - end_equity
            - return
            - equity_change
            - contribution
    """
    df = trades.copy().sort_values("exit_date")

    records = []
    prev_equity = initial_capital

    for year, g in df.groupby("year"):
        start_equity = prev_equity
        end_equity = g.iloc[-1]["capital_after"]

        equity_change = end_equity - start_equity
        yearly_return = end_equity / start_equity - 1

        records.append({
            "year": year,
            "start_equity": start_equity,
            "end_equity": end_equity,
            "return": yearly_return,
            "equity_change": equity_change,
        })

        prev_equity = end_equity

    yearly = pd.DataFrame(records).set_index("year")

    total_gain = yearly["equity_change"].sum()
    yearly["contribution"] = (
        yearly["equity_change"] / total_gain if total_gain != 0 else 0.0
    )

    return yearly




# Consistency metrics
def metrics_yearly_consistency(yearly: pd.DataFrame) -> dict:
    """
    Đánh giá độ bền theo năm.
    """
    positive_year_ratio = (yearly["return"] > 0).mean()
    max_year_contribution = yearly["contribution"].max()

    return {
        "positive_year_ratio": positive_year_ratio,
        "max_year_contribution": max_year_contribution,
    }





# Trực quan return theo từng năm
def plot_yearly_returns(yearly: pd.DataFrame, title="Yearly Returns"):
    vals = yearly["return"]
    years = vals.index.astype(int)

    colors = ["green" if v > 0 else "red" for v in vals]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(years, vals.values, color=colors, alpha=0.6)
    ax.axhline(0)

    ax.set_title(title)
    ax.set_xlabel("Year")
    ax.set_ylabel("Return")

    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45)

    plt.tight_layout()
    plt.show()


# Trực quan % contribution return theo từng năm
def plot_yearly_contribution(yearly: pd.DataFrame):
    contrib = yearly["contribution"]
    years = contrib.index.astype(int)

    colors = ["green" if v > 0 else "red" for v in contrib]

    plt.figure(figsize=(10, 4))
    plt.bar(years, contrib.values, color=colors, alpha=0.7)
    plt.axhline(0)

    plt.title("Yearly Contribution to Total Performance")
    plt.xlabel("Year")
    plt.ylabel("Contribution")

    # ===== FIX QUAN TRỌNG =====
    plt.xticks(years, rotation=45)

    plt.tight_layout()
    plt.show()




# Hàm xuất hình ảnh trực quan return theo từng năm
def evaluate_seasonal_strategy(
    trades: pd.DataFrame,
    initial_capital: float,
    season_mapper: Callable[[int], str] = default_season_mapper,
    plot: bool = True,
) -> dict:

    prepared = prepare_seasonal_trades(trades, season_mapper)

    yearly = compute_yearly_equity_stats(
        prepared, initial_capital
    )

    metrics = metrics_yearly_consistency(yearly)

    if plot:
        plot_yearly_returns(yearly, "Seasonal Strategy – Yearly Returns")
        plot_yearly_contribution(yearly)

    return {
        "yearly": yearly,
        "metrics": metrics,
    }

def compute_seasonal_returns(trades: pd.DataFrame,
                             initial_capital: float,
                             season_mapper: Callable[[int], str] = default_season_mapper) -> pd.DataFrame:
    """
    Tính tổng return và equity change theo season.
    """
    df = prepare_seasonal_trades(trades, season_mapper)

    # Sắp xếp theo exit_date để tính equity tuần tự
    df = df.sort_values("exit_date").copy()
    prev_equity = initial_capital
    records = []

    for season, g in df.groupby("season"):
        start_equity = prev_equity
        end_equity = g.iloc[-1]["capital_after"]
        equity_change = end_equity - start_equity
        season_return = end_equity / start_equity - 1

        records.append({
            "season": season,
            "start_equity": start_equity,
            "end_equity": end_equity,
            "equity_change": equity_change,
            "return": season_return,
        })

        prev_equity = end_equity  # tiếp tục cho season tiếp theo

    seasonal_df = pd.DataFrame(records).sort_values("return", ascending=False)
    return seasonal_df


def plot_seasonal_returns(seasonal_df: pd.DataFrame):
    """
    Vẽ biểu đồ return theo season.
    """
    seasons = seasonal_df["season"]
    returns = seasonal_df["return"]
    colors = ["green" if r > 0 else "red" for r in returns]

    plt.figure(figsize=(8, 4))
    plt.bar(seasons, returns.values, color=colors, alpha=0.7)
    plt.axhline(0, color='k', linestyle='--')
    plt.title("Total Return by Season")
    plt.ylabel("Return")
    plt.xlabel("Season")
    plt.tight_layout()
    plt.show()



def compute_seasonal_return_by_year(
    trades: pd.DataFrame,
    initial_capital: float,
    season_mapper: Callable[[int], str] = default_season_mapper,
) -> pd.DataFrame:
    """
    Tính return theo từng SEASON trong từng NĂM (equity-based).
    """
    df = prepare_seasonal_trades(trades, season_mapper)
    df = df.sort_values("exit_date").copy()

    records = []

    for year, year_df in df.groupby("year"):
        prev_equity = initial_capital

        for season, g in year_df.groupby("season"):
            start_equity = prev_equity
            end_equity = g.iloc[-1]["capital_after"]

            equity_change = end_equity - start_equity
            season_return = end_equity / start_equity - 1

            records.append({
                "year": year,
                "season": season,
                "start_equity": start_equity,
                "end_equity": end_equity,
                "equity_change": equity_change,
                "return": season_return,
            })

            prev_equity = end_equity  # sang season tiếp theo

    df_out = pd.DataFrame(records)

    # Contribution trong từng năm
    df_out["contribution"] = (
        df_out.groupby("year")["equity_change"]
        .transform(lambda x: x / x.sum() if x.sum() != 0 else 0)
    )

    return df_out.sort_values(["year", "return"], ascending=[True, False])



def plot_seasonal_return_by_year(seasonal_df: pd.DataFrame):
    """
    Vẽ return theo season, mỗi năm một hình.
    """
    for year, g in seasonal_df.groupby("year"):
        seasons = g["season"]
        returns = g["return"]

        colors = ["green" if r > 0 else "red" for r in returns]

        plt.figure(figsize=(7, 4))
        plt.bar(seasons, returns, color=colors, alpha=0.7)
        plt.axhline(0, color="black", linewidth=1)

        plt.title(f"Seasonal Return – {year}", fontsize=12, fontweight="bold")
        plt.xlabel("Season")
        plt.ylabel("Return")

        for i, r in enumerate(returns):
            plt.text(i, r, f"{r:.1%}",
                     ha="center",
                     va="bottom" if r > 0 else "top",
                     fontsize=9)

        plt.tight_layout()
        plt.show()



# Xuất kết quả return theo giai đoạn của từng năm
def pretty_print_seasonal_by_year(seasonal_df: pd.DataFrame):
    for year, g in seasonal_df.groupby("year"):
        print("=" * 70)
        print(f"SEASONAL PERFORMANCE – YEAR {year}")
        print("=" * 70)

        display(
            g[["season", "return", "equity_change", "contribution"]]
            .sort_values("return", ascending=False)
            .style.format({
                "return": "{:.2%}",
                "equity_change": "{:,.0f}",
                "contribution": "{:.2%}",
            })
        )

        best = g.sort_values("return", ascending=False).iloc[0]
        print(
            f"✓ Best season: {best['season']} "
            f"(Return {best['return']:.2%}, "
            f"Contribution {best['contribution']:.2%})"
        )


# Xuất kết quả thống kê
def pretty_print_result(result):
    yearly = result["yearly"]

    print("=" * 60)
    print("YEARLY PERFORMANCE")
    print("=" * 60)

    display(
        yearly[["return", "contribution"]]
        .style.format({
            "return": "{:.2%}",
            "contribution": "{:.2%}",
        })
    )

    print("\n" + "=" * 60)
    print("CONSISTENCY METRICS")
    print("=" * 60)

    for k, v in result["metrics"].items():
        print(f"{k:30s}: {v:.2%}")
