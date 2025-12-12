
from typing import Dict, Any, Tuple
import pandas as pd
import matplotlib.pyplot as plt


def add_calendar_columns(df: pd.DataFrame, date_col: str = 'Date') -> pd.DataFrame:
    """Thêm các cột calendar vào DataFrame. Trả về bản sao của df.
    """
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
    """Tính daily return nếu chưa có.
    """
    df = df.copy()
    if return_col not in df.columns:
        if price_col not in df.columns:
            raise KeyError(f"Không tìm thấy cột giá: {price_col}")
        df[return_col] = df[price_col].pct_change()
        if percent:
            df[return_col] = df[return_col] * 100
    return df


def analyze_monthly(df: pd.DataFrame, return_col: str = 'Daily_Return') -> pd.DataFrame:
    """Tính thống kê theo tháng và in ra kết quả giống format gốc.
    """
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
    """Tính thống kê theo quý và in ra kết quả.
    """
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
    """Tạo 2 biểu đồ giống layout gốc: tháng, quý (đã loại bỏ biểu đồ theo thứ).
    """
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


def analyze_calendar_effects(df: pd.DataFrame, date_col: str = 'Date', price_col: str = 'Close', return_col: str = 'Daily_Return', plot: bool = True) -> Dict[str, pd.DataFrame]:
    """Tiện lợi: thực hiện đầy đủ các bước (thêm cột, tính return, phân tích, và tùy chọn vẽ).
    """
    df2 = add_calendar_columns(df, date_col=date_col)
    df2 = compute_daily_return(df2, price_col=price_col, return_col=return_col, percent=True)

    monthly_df = analyze_monthly(df2, return_col=return_col)
    quarterly_df = analyze_quarterly(df2, return_col=return_col)

    fig = None
    if plot:
        try:
            fig = plot_calendar_effects(df2, monthly_df, quarterly_df)
            plt.show()
        except Exception as e:
            print(f"Không thể vẽ biểu đồ: {e}")

    return {
        'df': df2,
        'monthly_df': monthly_df,
        'quarterly_df': quarterly_df,
        'fig': fig
    }
