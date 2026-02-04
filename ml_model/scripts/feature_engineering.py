"""
Feature Engineering for Request Rate Forecasting
Xây dựng các features từ request rate time series
"""

import pandas as pd
import numpy as np


def build_request_rate(df: pd.DataFrame, window: str = "60s") -> pd.DataFrame:
    """
    Build request rate từ raw log data
    Nhóm theo time window và đếm số request
    
    Args:
        df: DataFrame với cột 'timestamp'
        window: Pandas resample window (e.g., '60S' = 1 minute)
    
    Returns:
        DataFrame với timestamp và request_rate
    """
    df_raw = df.copy()
    
    rate_df = (
        df_raw
        .set_index("timestamp")
        .resample(window)
        .size()
        .rename("request_rate")
        .reset_index()
    )
    
    return rate_df


def build_baseline(rate_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build baseline using Exponential Weighted Moving Average (EWMA)
    Phân tách trend từ noise
    
    Args:
        rate_df: DataFrame với cột 'request_rate'
    
    Returns:
        DataFrame với baseline, residual, và lag features
    """
    df = rate_df.sort_values("timestamp").reset_index(drop=True)
    y = df["request_rate"]
    
    # EWMA slow (long memory) - capture trend
    df["ewma_slow"] = y.shift(1).ewm(alpha=0.02, adjust=False).mean()
    
    # EWMA fast (medium memory) - capture medium-term changes
    df["ewma_fast"] = y.shift(1).ewm(alpha=0.15, adjust=False).mean()
    
    # Combined baseline
    df["baseline"] = 0.7 * df["ewma_slow"] + 0.3 * df["ewma_fast"]
    
    # Residual = deviation từ baseline
    df["residual"] = y - df["baseline"]
    
    return df


def build_features(rate_df: pd.DataFrame) -> tuple:
    """
    Build comprehensive features từ residual series
    Captures bursts, volatility, momentum
    
    Args:
        rate_df: DataFrame với cột 'request_rate'
    
    Returns:
        Tuple: (X, y, df_with_features)
    """
    df = build_baseline(rate_df)
    r = df["residual"]
    
    # ========== Lag Features ==========
    lags = [1, 2, 3, 5]
    for lag in lags:
        df[f"lag_{lag}"] = r.shift(lag)
    
    # ========== Volatility & Local Range ==========
    for win in [3, 5]:
        df[f"roll_std_{win}"] = r.shift(1).rolling(win).std()
        df[f"roll_max_{win}"] = r.shift(1).rolling(win).max()
        df[f"roll_min_{win}"] = r.shift(1).rolling(win).min()
    
    # ========== Burst Dynamics ==========
    df["diff_1"] = r.shift(1) - r.shift(2)
    df["diff_2"] = r.shift(1) - r.shift(3)
    df["acceleration"] = df["diff_1"] - df["diff_2"]
    df["abs_diff_1"] = df["diff_1"].abs()
    
    # Burst intensity normalized by volatility
    df["burst_strength"] = df["abs_diff_1"] / (df["roll_std_3"] + 1e-5)
    
    # Range expansion
    df["range_expand"] = df["roll_max_5"] - df["roll_min_5"]
    
    # ========== Drop NaN rows ==========
    df = df.dropna().reset_index(drop=True)
    
    # ========== Prepare X, y ==========
    X = df.drop(columns=[
        "timestamp",
        "request_rate",
        "baseline",
        "residual"
    ])
    
    y = df["residual"]
    
    return X, y, df


def prepare_data(log_df: pd.DataFrame, window: str = "60s") -> tuple:
    """
    Full pipeline: raw logs → request rate → features
    
    Args:
        log_df: Raw log DataFrame
        window: Resample window
    
    Returns:
        Tuple: (X, y, df_with_all_info)
    """
    rate_df = build_request_rate(log_df, window)
    X, y, df = build_features(rate_df)
    return X, y, df
