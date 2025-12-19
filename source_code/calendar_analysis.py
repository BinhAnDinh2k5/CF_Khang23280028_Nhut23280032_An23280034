from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def add_calendar_columns(df: pd.DataFrame, date_col: str = 'Date') -> pd.DataFrame:
    """Thêm các cột calendar vào DataFrame. Trả về bản sao của df."""
    df = df.copy()
    if date_col not in df.columns:
        raise KeyError(f"Không tìm thấy cột ngày: {date_col}")
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    df['Month'] = df[date_col].dt.month
    df['Quarter'] = df[date_col].dt.quarter
    df['DayOfWeek'] = df[date_col].dt.dayofweek
    df['WeekDay_Name'] = df[date_col].dt.day_name()
    df['Month_Name'] = df[date_col].dt.month_name()
    df['Year'] = df[date_col].dt.year

    return df


def compute_daily_return(df: pd.DataFrame, price_col: str = 'Close', return_col: str = 'Daily_Return', percent: bool = True) -> pd.DataFrame:
    """Tính daily return nếu chưa có."""
    df = df.copy()
    if return_col not in df.columns:
        if price_col not in df.columns:
            raise KeyError(f"Không tìm thấy cột giá: {price_col}")
        df[return_col] = df[price_col].pct_change()
        if percent:
            df[return_col] = df[return_col] * 100
    return df


def analyze_monthly(df: pd.DataFrame, return_col: str = 'Daily_Return') -> pd.DataFrame:
    """Tính thống kê theo tháng và in ra kết quả giống format gốc."""
    monthly_stats = []
    for month in range(1, 13):
        month_data = df[df['Month'] == month]
        if len(month_data) > 0:
            returns = month_data[return_col].dropna()
            if len(returns) > 0:
                monthly_stats.append({
                    'Month': month,
                    'Month_Name': month_data['Month_Name'].iloc[0],
                    'Avg_Return': returns.mean(),
                    'Median_Return': returns.median(),
                    'Std_Dev': returns.std(),
                    'Positive_Days': (returns > 0).sum(),
                    'Negative_Days': (returns < 0).sum(),
                    'Total_Days': len(returns)
                })

    monthly_df = pd.DataFrame(monthly_stats).sort_values('Avg_Return', ascending=False).reset_index(drop=True)

    # In ra thông tin 
    print("=" * 70)
    print("1. PHÂN TÍCH THEO THÁNG (MONTH EFFECT)")
    print("=" * 70)
    if monthly_df.empty:
        print("Không có dữ liệu để phân tích theo tháng.")
        return monthly_df

    print("📊 Trung bình Return theo tháng:")
    print(monthly_df[['Month', 'Month_Name', 'Avg_Return', 'Std_Dev', 'Total_Days']].to_string(index=False))

    best_month = monthly_df.iloc[0]
    worst_month = monthly_df.iloc[-1]
    print(f"✓ Tháng tốt nhất: {int(best_month['Month'])} ({best_month['Month_Name']}) - Avg {best_month['Avg_Return']:.4f}%")
    print(f"✗ Tháng tồi nhất: {int(worst_month['Month'])} ({worst_month['Month_Name']}) - Avg {worst_month['Avg_Return']:.4f}%")
    print(f"  Chênh lệch: {best_month['Avg_Return'] - worst_month['Avg_Return']:.4f}%")

    return monthly_df


def analyze_quarterly(df: pd.DataFrame, return_col: str = 'Daily_Return') -> pd.DataFrame:
    """Tính thống kê theo quý và in ra kết quả."""
    quarterly_stats = []
    for quarter in range(1, 5):
        quarter_data = df[df['Quarter'] == quarter]
        if len(quarter_data) > 0:
            returns = quarter_data[return_col].dropna()
            if len(returns) > 0:
                quarterly_stats.append({
                    'Quarter': f'Q{quarter}',
                    'Avg_Return': returns.mean(),
                    'Median_Return': returns.median(),
                    'Std_Dev': returns.std(),
                    'Positive_Days': (returns > 0).sum(),
                    'Negative_Days': (returns < 0).sum(),
                    'Total_Days': len(returns)
                })

    quarterly_df = pd.DataFrame(quarterly_stats).sort_values('Avg_Return', ascending=False).reset_index(drop=True)

    print("" + "=" * 70)
    print("2. PHÂN TÍCH THEO QUÝ (QUARTER EFFECT)")
    print("=" * 70)
    if quarterly_df.empty:
        print("Không có dữ liệu để phân tích theo quý.")
        return quarterly_df

    print("📊 Trung bình Return theo quý:")
    print(quarterly_df[['Quarter', 'Avg_Return', 'Std_Dev', 'Total_Days']].to_string(index=False))

    best_q = quarterly_df.iloc[0]
    worst_q = quarterly_df.iloc[-1]
    print(f"✓ Quý tốt nhất: {best_q['Quarter']} - Avg {best_q['Avg_Return']:.4f}%")
    print(f"✗ Quý tồi nhất: {worst_q['Quarter']} - Avg {worst_q['Avg_Return']:.4f}%")
    print(f"  Chênh lệch: {best_q['Avg_Return'] - worst_q['Avg_Return']:.4f}%")

    return quarterly_df



def plot_calendar_effects(df: pd.DataFrame, monthly_df: pd.DataFrame, quarterly_df: pd.DataFrame, figsize: Tuple[int,int] = (12, 5)) -> Any:
    """Tạo 2 biểu đồ giống layout gốc: tháng, quý (đã loại bỏ biểu đồ theo thứ)."""
    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Plot 1: Tháng
    months_order = list(range(1, 13))
    month_names_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_returns = [monthly_df[monthly_df['Month'] == m]['Avg_Return'].values[0] if m in monthly_df['Month'].values else 0 for m in months_order]
    colors_month = ['green' if x > 0 else 'red' for x in month_returns]

    axes[0].bar(month_names_order, month_returns, color=colors_month, alpha=0.7, edgecolor='black', linewidth=1.5)
    axes[0].axhline(y=0, color='k', linestyle='-', linewidth=0.8, alpha=0.5)
    axes[0].axhline(y=df['Daily_Return'].mean(), color='blue', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Overall Avg: {df["Daily_Return"].mean():.4f}%')
    axes[0].set_title('Trung Bình Daily Return Theo Tháng', fontsize=13, fontweight='bold')
    axes[0].set_ylabel('Avg Return (%)', fontsize=11)
    axes[0].set_xlabel('Tháng', fontsize=11)
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].legend()
    for i, v in enumerate(month_returns):
        axes[0].text(i, v + (0.002 if v > 0 else -0.004), f'{v:.3f}%', ha='center', fontsize=8, fontweight='bold')

    # Plot 2: Quý
    quarters_order = ['Q1', 'Q2', 'Q3', 'Q4']
    quarter_returns = [quarterly_df[quarterly_df['Quarter'] == q]['Avg_Return'].values[0] if q in quarterly_df['Quarter'].values else 0 for q in quarters_order]
    colors_quarter = ['green' if x > 0 else 'red' for x in quarter_returns]

    axes[1].bar(quarters_order, quarter_returns, color=colors_quarter, alpha=0.7, edgecolor='black', linewidth=1.5, width=0.5)
    axes[1].axhline(y=0, color='k', linestyle='-', linewidth=0.8, alpha=0.5)
    axes[1].axhline(y=df['Daily_Return'].mean(), color='blue', linestyle='--', linewidth=1.5, alpha=0.6, label=f'Overall Avg: {df["Daily_Return"].mean():.4f}%')
    axes[1].set_title('Trung Bình Daily Return Theo Quý', fontsize=13, fontweight='bold')
    axes[1].set_ylabel('Avg Return (%)', fontsize=11)
    axes[1].set_xlabel('Quý', fontsize=11)
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].legend()
    for i, v in enumerate(quarter_returns):
        axes[1].text(i, v + (0.002 if v > 0 else -0.004), f'{v:.3f}%', ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    return fig


# Hàm tính thống kê theo tháng/quý cho từng năm và vẽ từng năm riêng biệt
def compute_monthly_stats_per_year(df: pd.DataFrame, return_col: str = 'Daily_Return') -> Dict[int, pd.DataFrame]:
    """Trả về dict: year -> monthly stats DataFrame (Month, Month_Name, Avg_Return, ...)."""
    years = sorted(df['Year'].dropna().unique().astype(int))
    out = {}
    for y in years:
        sub = df[df['Year'] == y]
        stats = []
        for m in range(1, 13):
            mdata = sub[sub['Month'] == m]
            returns = mdata[return_col].dropna()
            if len(returns) > 0:
                stats.append({
                    'Month': m,
                    'Month_Name': mdata['Month_Name'].iloc[0] if len(mdata) > 0 else pd.to_datetime(f'{y}-{m}-01').month_name(),
                    'Avg_Return': returns.mean(),
                    'Median_Return': returns.median(),
                    'Std_Dev': returns.std(),
                    'Positive_Days': (returns > 0).sum(),
                    'Negative_Days': (returns < 0).sum(),
                    'Total_Days': len(returns)
                })
        out[y] = pd.DataFrame(stats).sort_values('Month').reset_index(drop=True)
    return out

# Tính thống kê theo quý
def compute_quarterly_stats_per_year(df: pd.DataFrame, return_col: str = 'Daily_Return') -> Dict[int, pd.DataFrame]:

    years = sorted(df['Year'].dropna().unique().astype(int))
    out = {}
    for y in years:
        sub = df[df['Year'] == y]
        stats = []
        for q in range(1, 5):
            qdata = sub[sub['Quarter'] == q]
            returns = qdata[return_col].dropna()
            if len(returns) > 0:
                stats.append({
                    'Quarter': f'Q{q}',
                    'Avg_Return': returns.mean(),
                    'Median_Return': returns.median(),
                    'Std_Dev': returns.std(),
                    'Positive_Days': (returns > 0).sum(),
                    'Negative_Days': (returns < 0).sum(),
                    'Total_Days': len(returns)
                })
        out[y] = pd.DataFrame(stats).reset_index(drop=True)
    return out


# Vẽ mỗi năm một figure (Tháng + Quý).
def plot_calendar_effects_by_year(
    df: pd.DataFrame,
    return_col: str = 'Daily_Return',
    years: List[int] = None,
    figsize: Tuple[int, int] = (12, 5),
    max_years: int = 10,
    show: bool = True
) -> Dict[int, Any]:

    if years is None:
        years = sorted(df['Year'].dropna().unique().astype(int).tolist())
    else:
        # filter only years present in df
        present = set(df['Year'].dropna().unique().astype(int).tolist())
        years = [y for y in years if y in present]

    if len(years) == 0:
        raise ValueError("Không có năm hợp lệ để vẽ.")

    if len(years) > max_years:
        years = years[:max_years]  # giới hạn

    monthly_per_year = compute_monthly_stats_per_year(df, return_col=return_col)
    quarterly_per_year = compute_quarterly_stats_per_year(df, return_col=return_col)

    figs = {}
    for y in years:
        # tạo figure giống layout gốc
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        sub_df = df[df['Year'] == y]

        # Monthly
        months_order = list(range(1, 13))
        month_names_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_df_y = monthly_per_year.get(y, pd.DataFrame())
        month_return_map = monthly_df_y.set_index('Month')['Avg_Return'].to_dict() if not monthly_df_y.empty else {}
        month_returns = [month_return_map.get(m, 0) for m in months_order]
        colors_month = ['green' if x > 0 else 'red' for x in month_returns]

        axes[0].bar(month_names_order, month_returns, alpha=0.7, edgecolor='black', linewidth=1.2, color=colors_month)
        axes[0].axhline(y=0, color='k', linestyle='-', linewidth=0.8, alpha=0.5)
        year_mean = sub_df[return_col].mean() if not sub_df.empty else 0
        axes[0].axhline(y=year_mean, color='blue', linestyle='--', linewidth=1.2, alpha=0.6, label=f'Year {y} Avg: {year_mean:.4f}%')
        axes[0].set_title(f'{y} - Trung Bình Daily Return Theo Tháng', fontsize=12, fontweight='bold')
        axes[0].set_ylabel('Avg Return (%)', fontsize=10)
        axes[0].set_xlabel('Tháng', fontsize=10)
        axes[0].grid(True, alpha=0.25, axis='y')
        axes[0].legend()
        for i, v in enumerate(month_returns):
            axes[0].text(i, v + (0.002 if v > 0 else -0.004), f'{v:.3f}%', ha='center', fontsize=7, fontweight='bold')

        # Quarterly
        quarterly_df_y = quarterly_per_year.get(y, pd.DataFrame())
        quarters_order = ['Q1', 'Q2', 'Q3', 'Q4']
        quarter_return_map = quarterly_df_y.set_index('Quarter')['Avg_Return'].to_dict() if not quarterly_df_y.empty else {}
        quarter_returns = [quarter_return_map.get(q, 0) for q in quarters_order]
        colors_quarter = ['green' if x > 0 else 'red' for x in quarter_returns]

        axes[1].bar(quarters_order, quarter_returns, color=colors_quarter, alpha=0.7, edgecolor='black', linewidth=1.2, width=0.5)
        axes[1].axhline(y=0, color='k', linestyle='-', linewidth=0.8, alpha=0.5)
        axes[1].axhline(y=year_mean, color='blue', linestyle='--', linewidth=1.2, alpha=0.6, label=f'Year {y} Avg: {year_mean:.4f}%')
        axes[1].set_title(f'{y} - Trung Bình Daily Return Theo Quý', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('Avg Return (%)', fontsize=10)
        axes[1].set_xlabel('Quý', fontsize=10)
        axes[1].grid(True, alpha=0.25, axis='y')
        axes[1].legend()
        for i, v in enumerate(quarter_returns):
            axes[1].text(i, v + (0.002 if v > 0 else -0.004), f'{v:.3f}%', ha='center', fontsize=8, fontweight='bold')

        plt.tight_layout()
        if show:
            plt.show()

        figs[y] = fig

    return figs


# Phân tích hiệu ứng mùa vụ
def analyze_calendar_effects(
    df: pd.DataFrame,
    date_col: str = 'Date',
    price_col: str = 'Close',
    return_col: str = 'Daily_Return',
    plot: bool = True,
    per_year: bool = False,
    years: List[int] = None,
    max_years: int = 10
) -> Dict[str, Any]:

    df2 = add_calendar_columns(df, date_col=date_col)
    df2 = compute_daily_return(df2, price_col=price_col, return_col=return_col, percent=True)

    monthly_df = analyze_monthly(df2, return_col=return_col)
    quarterly_df = analyze_quarterly(df2, return_col=return_col)

    fig = None
    year_figs = None
    if plot:
        try:
            if per_year:
                # vẽ từng năm riêng biệt
                year_figs = plot_calendar_effects_by_year(df2, return_col=return_col, years=years, max_years=max_years)
            else:
                fig = plot_calendar_effects(df2, monthly_df, quarterly_df)
                plt.show()
        except Exception as e:
            print(f"Không thể vẽ biểu đồ: {e}")

    return {
        'df': df2,
        'monthly_df': monthly_df,
        'quarterly_df': quarterly_df,
        'fig': fig,
        'year_figs': year_figs  # dict year -> fig (hoặc None nếu không per_year)
    }
