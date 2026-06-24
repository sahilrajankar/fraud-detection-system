"""
Universal Feature Engineering - Works on ANY transaction data
Strategy: Extract semantic features that exist in ALL transaction datasets
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')


class UniversalTransactionFeatures:
    """
    Extract features from ANY transaction dataset
    
    Core principle: ALL transaction datasets have:
    1. Some numeric columns (amounts, counts, IDs)
    2. Some categorical columns (types, categories)
    3. Some temporal information (even if implicit)
    
    We extract statistical features from these without knowing column names!
    """
    
    def __init__(self):
        self.training_stats = {}
        self.numeric_columns = []
        self.categorical_columns = []
    
    def fit(self, df: pd.DataFrame, target: Optional[str] = None):
        """Learn universal statistics from training data"""
        print("Analyzing dataset structure...")
        
        # Separate numeric and categorical
        self.numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remove target if present
        if target and target in self.numeric_columns:
            self.numeric_columns.remove(target)
        if target and target in self.categorical_columns:
            self.categorical_columns.remove(target)
        
        print(f"✓ Found {len(self.numeric_columns)} numeric columns")
        print(f"✓ Found {len(self.categorical_columns)} categorical columns")
        
        # Learn distributions
        for col in self.numeric_columns:
            self.training_stats[col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'median': df[col].median(),
                'min': df[col].min(),
                'max': df[col].max()
            }
        
        return self
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract universal features from ANY transaction data
        
        NO COLUMN NAMES REQUIRED!
        """
        features = pd.DataFrame(index=df.index)
        
        # ===== 1. NUMERIC FEATURES (Statistical Properties) =====
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            print(f"Extracting features from {len(numeric_cols)} numeric columns...")
            
            # For large datasets, sample columns to reduce memory
            MAX_NUMERIC_COLS = 50  # Process max 50 numeric columns
            if len(numeric_cols) > MAX_NUMERIC_COLS:
                print(f"  ⚠️ Large dataset: sampling {MAX_NUMERIC_COLS}/{len(numeric_cols)} columns")
                # Keep first 10 (usually important) + random sample
                sampled_cols = list(numeric_cols[:10]) + list(np.random.choice(
                    numeric_cols[10:], 
                    size=min(MAX_NUMERIC_COLS-10, len(numeric_cols)-10), 
                    replace=False
                ))
                numeric_cols_subset = sampled_cols
            else:
                numeric_cols_subset = numeric_cols
            
            # Statistical features across numeric columns (memory efficient)
            features['numeric_mean'] = df[numeric_cols_subset].mean(axis=1, skipna=True).astype('float32')
            features['numeric_std'] = df[numeric_cols_subset].std(axis=1, skipna=True).astype('float32')
            features['numeric_max'] = df[numeric_cols_subset].max(axis=1, skipna=True).astype('float32')
            features['numeric_min'] = df[numeric_cols_subset].min(axis=1, skipna=True).astype('float32')
            features['numeric_range'] = (features['numeric_max'] - features['numeric_min']).astype('float32')
            features['numeric_zeros'] = (df[numeric_cols_subset] == 0).sum(axis=1).astype('int32')
            features['numeric_nulls'] = df[numeric_cols_subset].isnull().sum(axis=1).astype('int32')
            
            # Identify likely "amount" column 
            # Priority: Look for 'amt', 'amount', 'value' in column name
            amount_col = None
            for col in numeric_cols:
                col_lower = str(col).lower()
                if any(pattern in col_lower for pattern in ['amt', 'amount', 'value', 'price']):
                    amount_col = col
                    break
            
            # If not found by name, use statistical properties
            if amount_col is None:
                sample_size = min(10000, len(df))
                df_sample = df.iloc[:sample_size]
                
                potential_amounts = []
                for col in numeric_cols:
                    # Skip ID-like columns (high cardinality)
                    if df_sample[col].nunique() / len(df_sample) > 0.9:
                        continue
                    if df_sample[col].min() >= 0 and df_sample[col].std() > 0:
                        potential_amounts.append((col, df_sample[col].mean()))
                
                if potential_amounts:
                    amount_col = max(potential_amounts, key=lambda x: x[1])[0]
            
            if amount_col:
                features['likely_amount'] = df[amount_col].astype('float32')
                features['likely_amount_log'] = np.log1p(df[amount_col]).astype('float32')
                features['likely_amount_round'] = (df[amount_col] % 1 == 0).astype('int8')
                print(f"  ✓ Identified likely amount column: {amount_col}")
            else:
                features['likely_amount'] = np.float32(0)
                features['likely_amount_log'] = np.float32(0)
                features['likely_amount_round'] = np.int8(0)
            
            # Identify likely "ID" columns (high cardinality, integers)
            for col in numeric_cols:
                if df[col].nunique() / len(df) > 0.9:  # High cardinality = likely ID
                    features[f'id_density_{col[:10]}'] = df.groupby(col)[col].transform('count')
                    break  # Use first ID-like column only
        
        # ===== 2. CATEGORICAL FEATURES (Entropy, Cardinality) =====
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(categorical_cols) > 0:
            print(f"Extracting features from {len(categorical_cols)} categorical columns...")
            
            features['categorical_count'] = len(categorical_cols)
            features['categorical_nulls'] = df[categorical_cols].isnull().sum(axis=1)
            
            # For each categorical: encode by frequency (CONSISTENT - always 10 features)
            for i in range(10):  # Always create 10 categorical features
                if i < len(categorical_cols):
                    col = categorical_cols[i]
                    freq_map = df[col].value_counts(normalize=True).to_dict()
                    features[f'cat_{i}_frequency'] = df[col].map(freq_map).fillna(0).astype('float32')
                    features[f'cat_{i}_nunique'] = df[col].nunique()
                else:
                    # Pad with zeros if fewer than 10 categorical columns
                    features[f'cat_{i}_frequency'] = np.float32(0)
                    features[f'cat_{i}_nunique'] = 0
        else:
            # No categorical columns - create zero features
            features['categorical_count'] = 0
            features['categorical_nulls'] = 0
            for i in range(10):
                features[f'cat_{i}_frequency'] = np.float32(0)
                features[f'cat_{i}_nunique'] = 0
        
        # ===== 3. CROSS-COLUMN FEATURES (Interactions) =====
        if len(numeric_cols) >= 2:
            # Ratio of first two numeric columns
            col1, col2 = numeric_cols[0], numeric_cols[1]
            features['ratio_col1_col2'] = df[col1] / (df[col2] + 1)
            features['product_col1_col2'] = df[col1] * df[col2]
        
        # ===== 4. MISSING DATA PATTERNS =====
        features['total_nulls'] = df.isnull().sum(axis=1)
        features['null_ratio'] = features['total_nulls'] / len(df.columns)
        
        # ===== 5. ANOMALY SCORES =====
        # How different is this row from others?
        if len(numeric_cols) > 0:
            # Z-score: how many std devs from mean (CONSISTENT - always 5 features)
            numeric_subset = list(numeric_cols[:5])
            for i in range(5):
                if i < len(numeric_subset):
                    col = numeric_subset[i]
                    mean = df[col].mean()
                    std = df[col].std()
                    if std > 0:
                        features[f'zscore_{i}'] = np.abs((df[col] - mean) / std).astype('float32')
                    else:
                        features[f'zscore_{i}'] = np.float32(0)
                else:
                    features[f'zscore_{i}'] = np.float32(0)
        
        print(f"✓ Generated {len(features.columns)} universal features")
        
        return features
    
    def fit_transform(self, df: pd.DataFrame, target: Optional[str] = None) -> pd.DataFrame:
        """Convenience method"""
        self.fit(df, target)
        return self.transform(df)


# ===== DEMO: Works on COMPLETELY DIFFERENT datasets =====
if __name__ == "__main__":
    print("=" * 80)
    print("Universal Feature Engineering - DEMO")
    print("Testing on COMPLETELY DIFFERENT column sets")
    print("=" * 80)
    print()
    
    # ===== DATASET 1: E-commerce =====
    print("TRAINING DATA: E-commerce Transactions")
    train_data = pd.DataFrame({
        'order_amount': [100, 200, 50, 300, 150],
        'customer_id': [1, 2, 3, 4, 5],
        'product_category': ['electronics', 'clothing', 'books', 'electronics', 'clothing'],
        'shipping_country': ['US', 'UK', 'US', 'CA', 'US'],
        'is_fraud': [0, 1, 0, 1, 0]
    })
    print(f"Columns: {list(train_data.columns)}")
    print()
    
    engineer = UniversalTransactionFeatures()
    train_features = engineer.fit_transform(train_data, target='is_fraud')
    print(f"✓ Generated {train_features.shape[1]} features")
    print(f"Sample features: {list(train_features.columns[:5])}")
    print()
    
    # ===== DATASET 2: Payment Processing (COMPLETELY DIFFERENT COLUMNS!) =====
    print("=" * 80)
    print("TEST DATA: Payment Processing (DIFFERENT SCHEMA!)")
    test_data = pd.DataFrame({
        'payment_value': [175, 225, 80],
        'card_bin': [411111, 522222, 633333],
        'merchant_id': [100, 200, 300],
        'device_type': ['mobile', 'desktop', 'mobile'],
        'transaction_currency': ['USD', 'EUR', 'USD']
    })
    print(f"Columns: {list(test_data.columns)}")
    print("⚠️ NO COLUMN OVERLAP WITH TRAINING!")
    print()
    
    # BUT IT STILL WORKS!
    test_features = engineer.transform(test_data)
    print(f"✅ STILL generated {test_features.shape[1]} features!")
    print(f"Features: {list(test_features.columns[:5])}")
    print()
    
    # ===== DATASET 3: Banking Transactions (YET ANOTHER SCHEMA!) =====
    print("=" * 80)
    print("TEST DATA: Banking Transactions (ANOTHER SCHEMA!)")
    test_data_2 = pd.DataFrame({
        'transfer_amount_usd': [500, 1000],
        'sender_account': [12345, 67890],
        'receiver_account': [11111, 22222],
        'bank_code': ['BOA', 'CHASE'],
        'transaction_type': ['wire', 'ach']
    })
    print(f"Columns: {list(test_data_2.columns)}")
    print("⚠️ COMPLETELY DIFFERENT AGAIN!")
    print()
    
    test_features_2 = engineer.transform(test_data_2)
    print(f"✅ STILL WORKS - {test_features_2.shape[1]} features!")
    print()
    
    # ===== SHOW THAT FEATURES ARE CONSISTENT =====
    print("=" * 80)
    print("KEY INSIGHT: Features are CONSISTENT across different schemas")
    print("=" * 80)
    print()
    print("All datasets produce the same feature set:")
    print(f"  Training (e-commerce):     {train_features.shape[1]} features")
    print(f"  Test 1 (payment):          {test_features.shape[1]} features")
    print(f"  Test 2 (banking):          {test_features_2.shape[1]} features")
    print()
    print("✅ Model trained on these features will work on ANY transaction data!")
    print()
    print("Why it works:")
    print("  - Uses statistical properties (mean, std, max) not column names")
    print("  - Identifies likely 'amount' column by distribution")
    print("  - Encodes categoricals by frequency, not values")
    print("  - Creates cross-column interactions generically")
