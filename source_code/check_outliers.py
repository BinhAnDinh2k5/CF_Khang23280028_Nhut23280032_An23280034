import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. Compute returns
# ---------------------------------------------------------
def compute_returns(df: pd.DataFrame, price_col: str = 'Close') -> pd.DataFrame:
    """
    Tính return dựa trên cột giá.
    """
    df = df.copy()
    df['return'] = df[price_col].pct_change()
    return df.dropna()


# ---------------------------------------------------------
# 2. Detect outliers bằng QQ-plot deviation
# ---------------------------------------------------------
def detect_outliers_qq(df: pd.DataFrame, column: str = 'return', threshold: float = 3.0) -> pd.DataFrame:
    """
    Phát hiện outlier dựa trên extreme deviation khỏi đường chuẩn QQ-plot.
    """
    df = df.copy()
    
    r = df[column].values
    n = len(r)

    # sort actual returns
    sorted_r = np.sort(r)

    # theoretical normal quantiles
    probs = (np.arange(1, n + 1) - 0.5) / n
    theoretical = stats.norm.ppf(probs)

    # standardize actual data
    r_mean = sorted_r.mean()
    r_std = sorted_r.std()
    z_actual = (sorted_r - r_mean) / r_std

    # deviation khỏi đường 45°
    deviation = z_actual - theoretical

    # extreme deviation = outlier
    outlier_mask_sorted = np.abs(deviation) > threshold

    # chuyển về index ban đầu
    idx_sorted = np.argsort(df[column].values)
    outlier_mask = np.zeros(n, dtype=bool)
    outlier_mask[idx_sorted] = outlier_mask_sorted

    df['is_outlier'] = outlier_mask
    df['qq_deviation'] = np.abs(deviation)[np.argsort(np.argsort(df[column].values))]

    return df



# Pipeline chính
def detect_outliers(df: pd.DataFrame, price_col: str = 'Close', threshold: float = 3.0) -> dict:
    """
    Tính returns, phát hiện outlier và trả về dict kết quả.
    """
    df = df.copy()
    df.index = pd.to_datetime(df['Date']).dt.date
    df = df.drop(columns=['Date'])

    df = compute_returns(df, price_col)
    df = detect_outliers_qq(df, 'return', threshold)

    outliers = df[df['is_outlier']]

    return {
        'df': df,
        'outliers': outliers,
    }


# Trực quan hóa outlier
def plot_outliers(df: pd.DataFrame, column: str = 'return'):
    """
    Vẽ return theo thời gian và đánh dấu outlier màu đỏ.
    """
    returns = df[column]
    outliers = df[df['is_outlier']]

    plt.figure(figsize=(12,5))
    plt.plot(df.index, returns, linewidth=0.6, label='Returns')
    plt.scatter(outliers.index, outliers[column], color='red', label='Outliers')
    plt.title("Outliers theo thời gian")
    plt.xlabel("Date")
    plt.ylabel("Return")
    plt.legend()
    plt.tight_layout()
    plt.show()
