"""
Feature Engineering Pipeline - Combines schema-agnostic + universal features
"""

import pandas as pd
import numpy as np
from src.features.schema_agnostic import SchemaAgnosticFeatureEngineer
from src.features.universal_features import UniversalTransactionFeatures


class FeatureEngineeringPipeline:
    """
    Complete feature engineering pipeline
    Handles ANY schema changes!
    """
    
    def __init__(self, use_schema_agnostic=True, use_universal=True):
        self.use_schema_agnostic = use_schema_agnostic
        self.use_universal = use_universal
        
        if use_schema_agnostic:
            self.schema_agnostic = SchemaAgnosticFeatureEngineer()
        
        if use_universal:
            self.universal = UniversalTransactionFeatures()
        
        self.fitted = False
    
    def fit(self, df, target='isFraud'):
        """Learn from training data"""
        print("=" * 80)
        print("Feature Engineering Pipeline - FITTING")
        print("=" * 80)
        
        # Remove target from features
        X = df.drop(columns=[target] if target in df.columns else [])
        
        if self.use_schema_agnostic:
            print("\n1. Fitting Schema-Agnostic Features...")
            self.schema_agnostic.fit(X, target)
        
        if self.use_universal:
            print("\n2. Fitting Universal Features...")
            self.universal.fit(X, target)
        
        self.fitted = True
        print("\n" + "=" * 80)
        print("✅ Pipeline fitted successfully")
        print("=" * 80)
        
        return self
    
    def transform(self, df, training_mode=False):
        """Extract features"""
        if not self.fitted:
            raise ValueError("Pipeline not fitted! Call fit() first")
        
        print(f"\nExtracting features from {len(df):,} rows...")
        
        # Remove target if present
        X = df.drop(columns=['isFraud'] if 'isFraud' in df.columns else [])
        
        features_list = []
        
        # Schema-agnostic features
        if self.use_schema_agnostic:
            schema_features = self.schema_agnostic.transform(X, training_mode)
            features_list.append(schema_features)
            print(f"  ✓ Schema-agnostic: {schema_features.shape[1]} features")
        
        # Universal features
        if self.use_universal:
            universal_features = self.universal.transform(X)
            features_list.append(universal_features)
            print(f"  ✓ Universal: {universal_features.shape[1]} features")
        
        # Combine
        if len(features_list) > 1:
            final_features = pd.concat(features_list, axis=1)
        else:
            final_features = features_list[0]
        
        # Store expected columns on first fit
        if not hasattr(self, 'expected_columns_'):
            self.expected_columns_ = final_features.columns.tolist()
            self.n_features_expected_ = len(self.expected_columns_)
        
        # Ensure consistent feature count (pad with zeros if needed)
        if len(final_features.columns) != self.n_features_expected_:
            print(f"  ⚠️  Feature count mismatch: {len(final_features.columns)} vs expected {self.n_features_expected_}")
            print(f"  ✓ Adjusting to match training schema...")
            
            # Create DataFrame with expected columns
            aligned_features = pd.DataFrame(
                index=final_features.index,
                columns=self.expected_columns_
            )
            
            # Fill with values from final_features where available
            for col in final_features.columns:
                if col in aligned_features.columns:
                    aligned_features[col] = final_features[col]
            
            # Fill remaining with zeros
            aligned_features = aligned_features.fillna(0)
            final_features = aligned_features
        
        print(f"  ✓ Total features: {final_features.shape[1]}")
        
        return final_features
    
    def fit_transform(self, df, target='isFraud'):
        """Fit and transform in one step"""
        self.fit(df, target)
        return self.transform(df, training_mode=True)


if __name__ == "__main__":
    from src.data.loader import load_data
    
    print("Testing Feature Engineering Pipeline...")
    
    # Load small sample
    df = load_data(nrows=1000)
    
    # Fit and transform
    pipeline = FeatureEngineeringPipeline()
    X_features = pipeline.fit_transform(df, target='isFraud')
    
    print(f"\n✅ Generated {X_features.shape[1]} features from {df.shape[1]} columns")
    print(f"Feature shape: {X_features.shape}")
    print(f"Sample features: {list(X_features.columns[:10])}")
