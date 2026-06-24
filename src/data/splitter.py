"""
Temporal Data Splitter - Split data by time with gap period
CRITICAL: No random splits! Time-based only!
"""

import pandas as pd
import numpy as np


def temporal_split(df, time_col='TransactionDT', 
                   train_pct=0.6, val_pct=0.2, gap_pct=0.1, test_pct=0.1):
    """
    Split data temporally with gap period to prevent leakage
    
    Args:
        df: DataFrame with time column
        time_col: Name of time column
        train_pct: % for training (default 60%)
        val_pct: % for validation (default 20%)
        gap_pct: % for gap period (default 10%)
        test_pct: % for test (default 10%)
    
    Returns:
        train, val, test DataFrames
    """
    print("=" * 80)
    print("Temporal Data Splitting (NO RANDOM SPLITS!)")
    print("=" * 80)
    
    # Sort by time
    df_sorted = df.sort_values(time_col).reset_index(drop=True)
    n = len(df_sorted)
    
    # Calculate split points
    train_end = int(n * train_pct)
    gap_end = int(n * (train_pct + gap_pct))
    val_end = int(n * (train_pct + gap_pct + val_pct))
    
    # Split
    train = df_sorted.iloc[:train_end].copy()
    val = df_sorted.iloc[gap_end:val_end].copy()
    test = df_sorted.iloc[val_end:].copy()
    
    print(f"\n✓ Total records: {n:,}")
    print(f"\n1. TRAIN Period ({train_pct:.0%}):")
    print(f"   Records: {len(train):,}")
    print(f"   Time range: {train[time_col].min()} to {train[time_col].max()}")
    print(f"   Fraud rate: {train['isFraud'].mean():.2%}")
    
    print(f"\n2. GAP Period ({gap_pct:.0%}):")
    print(f"   Records: {gap_end - train_end:,} (EXCLUDED - prevents label leakage)")
    print(f"   ⚠️  Critical: Fraud discovered late won't leak into validation")
    
    print(f"\n3. VALIDATION Period ({val_pct:.0%}):")
    print(f"   Records: {len(val):,}")
    print(f"   Time range: {val[time_col].min()} to {val[time_col].max()}")
    print(f"   Fraud rate: {val['isFraud'].mean():.2%}")
    
    print(f"\n4. TEST Period ({test_pct:.0%}):")
    print(f"   Records: {len(test):,}")
    print(f"   Time range: {test[time_col].min()} to {test[time_col].max()}")
    print(f"   Fraud rate: {test['isFraud'].mean():.2%}")
    
    print("\n" + "=" * 80)
    print("✅ Temporal split complete - NO DATA LEAKAGE")
    print("=" * 80)
    
    return train, val, test


if __name__ == "__main__":
    from src.data.loader import load_data
    
    # Test
    print("Testing temporal split...")
    df = load_data(nrows=10000)
    
    train, val, test = temporal_split(df)
    
    print("\n✅ Split test successful!")
