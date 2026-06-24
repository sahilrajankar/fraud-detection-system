"""
Data Loader - Load and merge IEEE-CIS fraud detection data
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(transaction_path='data/raw/train_transaction.csv',
              identity_path='data/raw/train_identity.csv',
              nrows=None):
    """
    Load and merge IEEE-CIS fraud detection data
    
    Args:
        transaction_path: Path to transaction CSV
        identity_path: Path to identity CSV  
        nrows: Number of rows to load (None = all)
    
    Returns:
        Merged DataFrame
    """
    print("=" * 80)
    print("Loading IEEE-CIS Fraud Detection Dataset")
    print("=" * 80)
    
    # Load transaction data
    print(f"\n1. Loading transactions from {transaction_path}...")
    if nrows:
        print(f"   (Loading first {nrows:,} rows for testing)")
    
    df_transaction = pd.read_csv(transaction_path, nrows=nrows)
    print(f"   ✓ Loaded {len(df_transaction):,} transactions")
    print(f"   ✓ {len(df_transaction.columns)} columns")
    print(f"   ✓ Fraud rate: {df_transaction['isFraud'].mean():.2%}")
    
    # Load identity data
    print(f"\n2. Loading identity data from {identity_path}...")
    df_identity = pd.read_csv(identity_path, nrows=nrows)
    print(f"   ✓ Loaded {len(df_identity):,} identity records")
    print(f"   ✓ {len(df_identity.columns)} columns")
    
    # Merge
    print(f"\n3. Merging datasets...")
    df = df_transaction.merge(df_identity, on='TransactionID', how='left')
    print(f"   ✓ Merged dataset: {len(df):,} rows, {len(df.columns)} columns")
    
    # Optimize memory usage for large datasets
    if len(df) > 100000:
        print(f"\n3b. Optimizing memory usage...")
        # Convert float64 to float32 where possible
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df[col] = df[col].astype('float32')
        print(f"   ✓ Optimized {len(float_cols)} float columns to float32")
    
    # Basic info
    print(f"\n4. Dataset Summary:")
    print(f"   - Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    print(f"   - Missing values: {df.isnull().sum().sum():,} ({(df.isnull().sum().sum() / df.size * 100):.1f}%)")
    # Skip duplicate check on large datasets (memory intensive)
    if len(df) < 100000:
        print(f"   - Duplicates: {df.duplicated().sum():,}")
    else:
        print(f"   - Duplicates: Skipped (large dataset)")
    print(f"   - Date range (TransactionDT): {df['TransactionDT'].min()} to {df['TransactionDT'].max()}")
    
    print("\n" + "=" * 80)
    print("✅ Data loading complete!")
    print("=" * 80)
    
    return df


if __name__ == "__main__":
    # Test with small sample
    print("Testing data loader with 10,000 rows...")
    df = load_data(nrows=10000)
    
    print("\nFirst few columns:")
    print(df.columns[:10].tolist())
    
    print("\nTarget distribution:")
    print(df['isFraud'].value_counts())
    
    print("\n✅ Data loader test successful!")
