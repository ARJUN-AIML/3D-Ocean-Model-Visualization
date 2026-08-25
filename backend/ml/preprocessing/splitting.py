"""
backend/ml/preprocessing/splitting.py
Chronological Train/Validation/Test Data Splitting.
Strictly prevents temporal data leakage by partition windowing across time axis.
"""

from typing import Tuple, Optional, Union
import numpy as np
import pandas as pd


def chronological_split(
    df: pd.DataFrame,
    time_col: str = "obs_time",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame chronologically into train, validation, and test sets.

    Guarantees:
        max(train_time) < min(val_time) and max(val_time) < min(test_time).

    Args:
        df: Input DataFrame containing time_col.
        time_col: Column name representing timestamp.
        train_ratio: Proportion of temporal span for training.
        val_ratio: Proportion of temporal span for validation.
        test_ratio: Proportion of temporal span for testing.

    Returns:
        (df_train, df_val, df_test)
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-4:
        raise ValueError("Ratios train_ratio + val_ratio + test_ratio must sum to 1.0")

    if df.empty:
        return df.copy(), df.copy(), df.copy()

    df_sorted = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_sorted[time_col]):
        df_sorted[time_col] = pd.to_datetime(df_sorted[time_col])

    df_sorted = df_sorted.sort_values(by=time_col).reset_index(drop=True)

    n_total = len(df_sorted)
    n_train = int(np.round(n_total * train_ratio))
    n_val = int(np.round(n_total * val_ratio))

    df_train = df_sorted.iloc[:n_train].copy()
    df_val = df_sorted.iloc[n_train : n_train + n_val].copy()
    df_test = df_sorted.iloc[n_train + n_val :].copy()

    # Leakage check assertion
    if not df_train.empty and not df_val.empty:
        max_train_t = df_train[time_col].max()
        min_val_t = df_val[time_col].min()
        if max_train_t > min_val_t:
            raise RuntimeError(f"Data leakage detected! max(train_time)={max_train_t} > min(val_time)={min_val_t}")

    if not df_val.empty and not df_test.empty:
        max_val_t = df_val[time_col].max()
        min_test_t = df_test[time_col].min()
        if max_val_t > min_test_t:
            raise RuntimeError(f"Data leakage detected! max(val_time)={max_val_t} > min(test_time)={min_test_t}")

    return df_train, df_val, df_test


def chronological_split_by_dates(
    df: pd.DataFrame,
    val_start_date: str,
    test_start_date: str,
    time_col: str = "obs_time"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame into train, val, test using explicit date boundaries.
    """
    df_sorted = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_sorted[time_col]):
        df_sorted[time_col] = pd.to_datetime(df_sorted[time_col])

    t_val = pd.to_datetime(val_start_date)
    t_test = pd.to_datetime(test_start_date)

    if t_val >= t_test:
        raise ValueError("val_start_date must be strictly earlier than test_start_date")

    df_train = df_sorted[df_sorted[time_col] < t_val].copy()
    df_val = df_sorted[(df_sorted[time_col] >= t_val) & (df_sorted[time_col] < t_test)].copy()
    df_test = df_sorted[df_sorted[time_col] >= t_test].copy()

    return df_train, df_val, df_test
