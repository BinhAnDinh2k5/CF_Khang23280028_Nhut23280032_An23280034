from typing import Dict, Any, List, Tuple, Optional
from collections import Counter
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_sign_series(df: pd.DataFrame, return_col: str = 'Daily_Return', price_col: str = 'Close', percent: bool = True) -> pd.Series:
    """Đảm bảo cột return tồn tại, trả về series dấu: 1 (Up), -1 (Down), 0 (Neutral).
    """
    df = df.copy()
    if return_col not in df.columns:
        if price_col not in df.columns:
            raise KeyError(f"Không tìm thấy cột giá: {price_col}")
        df[return_col] = df[price_col].pct_change()
        if percent:
            df[return_col] = df[return_col] * 100

    sign_series = df[return_col].dropna().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)).astype(int)
    return sign_series


def run_length_encoding(vals: List[int]) -> List[Tuple[int, int]]:
    """Run-length encoding: trả về list of (value, length)."""
    runs = []
    for key, group in itertools.groupby(vals):
        length = sum(1 for _ in group)
        runs.append((int(key), length))
    return runs


def summarize_runs(lst: List[int]) -> Dict[str, float]:
    """Trả về thống kê cơ bản cho danh sách độ dài chuỗi."""
    if len(lst) == 0:
        return {'count': 0, 'mean': 0.0, 'median': 0.0, 'max': 0}
    arr = np.array(lst)
    return {'count': int(len(arr)), 'mean': float(arr.mean()), 'median': float(np.median(arr)), 'max': int(arr.max())}


def compute_transitions(sign_series: pd.Series) -> Optional[pd.DataFrame]:
    """Tính ma trận xác suất chuyển trạng thái giữa -1 và 1, bỏ qua 0 (neutral).
    """
    sign_no0 = sign_series[sign_series != 0]
    if len(sign_no0) < 2:
        return None
    prev = sign_no0.shift(1).dropna()
    curr = sign_no0.loc[prev.index]
    if len(prev) == 0:
        return None
    trans_df = pd.crosstab(prev, curr, normalize='index')
    return trans_df


def top_short_patterns(vals: List[int], length: int = 3, top_n: int = 10) -> List[Tuple[str, int]]:
    """Đếm các pattern ngắn (ví dụ length=3). Trả về danh sách (pattern_str, count)."""
    patterns = []
    for i in range(len(vals) - length + 1):
        pattern = tuple(vals[i:i + length])
        patterns.append(pattern)
    counts = Counter(patterns)

    def pat_to_str(p: Tuple[int, ...]) -> str:
        return ''.join('U' if x == 1 else 'D' if x == -1 else 'N' for x in p)

    return [(pat_to_str(k), v) for k, v in counts.most_common(top_n)]


def plot_pattern_results(up_runs: List[int], down_runs: List[int], trans_df: Optional[pd.DataFrame]) -> Optional[plt.Figure]:
    """Vẽ 3 biểu đồ (up-run dist, down-run dist, transition probs). Trả về figure."""
    try:
        fig, axes = plt.subplots(1, 3, figsize=(18, 4))

        # Up histogram
        bins_up = range(1, max(up_runs) + 2) if up_runs else [0, 1]
        axes[0].hist(up_runs, bins=bins_up, alpha=0.7, color='green', edgecolor='black')
        axes[0].set_title('Distribution of Up-run Lengths')
        axes[0].set_xlabel('Consecutive Up Days')
        axes[0].set_ylabel('Count')

        # Down histogram
        bins_down = range(1, max(down_runs) + 2) if down_runs else [0, 1]
        axes[1].hist(down_runs, bins=bins_down, alpha=0.7, color='red', edgecolor='black')
        axes[1].set_title('Distribution of Down-run Lengths')
        axes[1].set_xlabel('Consecutive Down Days')

        # Transitions
        if trans_df is not None and not trans_df.empty:
            labels = []
            probs = []
            for prev_state in trans_df.index:
                for curr_state in trans_df.columns:
                    labels.append(f"{ 'U' if prev_state==1 else 'D' }→{ 'U' if curr_state==1 else 'D' }")
                    probs.append(trans_df.loc[prev_state, curr_state])
            colors = ['#2ca02c' if 'U→U' in l or 'D→U' in l else '#d62728' for l in labels]
            axes[2].bar(labels, probs, color=colors)
            axes[2].set_title('Transition Probabilities')
            axes[2].set_ylabel('Probability')
            axes[2].set_ylim(0, 1)
        else:
            axes[2].text(0.5, 0.5, 'Not enough transitions', ha='center')
            axes[2].set_axis_off()

        plt.tight_layout()
        return fig
    except Exception:
        return None


def _format_stats_table(up_stats: Dict[str, float], down_stats: Dict[str, float]) -> str:
    """Trả về chuỗi dạng bảng ngắn gọn cho up/down stats."""
    header = f"{'Metric':<12} | {'Up':>10} | {'Down':>10}\n{'-'*36}"
    rows = []
    for k in ['count', 'mean', 'median', 'max']:
        up_val = up_stats.get(k, 0)
        down_val = down_stats.get(k, 0)
        if isinstance(up_val, float):
            up_s = f"{up_val:.2f}" if k != 'count' and k != 'max' else f"{int(up_val)}"
        else:
            up_s = f"{up_val}"
        if isinstance(down_val, float):
            down_s = f"{down_val:.2f}" if k != 'count' and k != 'max' else f"{int(down_val)}"
        else:
            down_s = f"{down_val}"
        rows.append(f"{k:<12} | {up_s:>10} | {down_s:>10}")
    return header + "\n" + "\n".join(rows)


def analyze_up_down(df: pd.DataFrame, price_col: str = 'Close', return_col: str = 'Daily_Return', percent: bool = True, plot: bool = True, print_summary: bool = True) -> Dict[str, Any]:
    # signs
    sign_series = compute_sign_series(df, return_col=return_col, price_col=price_col, percent=percent)
    vals = sign_series.tolist()

    # runs
    runs = run_length_encoding(vals)
    up_runs = [l for k, l in runs if k == 1]
    down_runs = [l for k, l in runs if k == -1]
    neutral_runs = [l for k, l in runs if k == 0]

    up_stats = summarize_runs(up_runs)
    down_stats = summarize_runs(down_runs)
    neutral_stats = summarize_runs(neutral_runs)

    # transitions
    trans_df = compute_transitions(sign_series)

    # Print concise, pretty summary
    if print_summary:
        print("\n=== Up/Down Pattern Summary ===\n")
        print(f"Total days analyzed: {len(sign_series)}\n")

        # stats table
        print(_format_stats_table(up_stats, down_stats) + "\n")

        # transitions
        if trans_df is not None and not trans_df.empty:
            trans_pct = (trans_df * 100).round(2)
            print("Transition probabilities (rows=Prev state, cols=Curr state) in %:")
            print(trans_pct.to_string())
            print()
        else:
            print("Transition probabilities: not enough non-zero data to compute.\n")

    fig = None
    if plot:
        fig = plot_pattern_results(up_runs, down_runs, trans_df)
        if fig is not None:
            plt.show()

    pattern_results = {
        'sign_series': sign_series,
        'up_runs': up_runs,
        'down_runs': down_runs,
        'neutral_runs': neutral_runs,
        'up_stats': up_stats,
        'down_stats': down_stats,
        'neutral_stats': neutral_stats,
        'transitions': trans_df,
        'fig': fig
    }

    return pattern_results
