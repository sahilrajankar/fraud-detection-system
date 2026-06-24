"""
Model Trainer - Train production-grade models
"""

import pandas as pd
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.metrics import average_precision_score
import joblib


class ModelTrainer:
    """
    Train and evaluate models
    Focus: LightGBM (best for production)
    """
    
    def __init__(self):
        self.model = None
        self.model_type = None
    
    def train_lightgbm(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train LightGBM model
        
        Why LightGBM:
        - Fast training
        - Handles missing values natively
        - Good calibration
        - Production-ready
        """
        print("=" * 80)
        print("Training LightGBM Model")
        print("=" * 80)
        
        # Calculate class weight
        neg_count = (y_train == 0).sum()
        pos_count = (y_train == 1).sum()
        scale_pos_weight = neg_count / pos_count
        
        print(f"\nDataset Info:")
        print(f"  Training samples: {len(X_train):,}")
        print(f"  Fraud rate: {y_train.mean():.2%}")
        print(f"  Class weight: {scale_pos_weight:.1f}")
        
        # Model configuration
        model = LGBMClassifier(
            n_estimators=200,           # More trees for better learning
            learning_rate=0.03,         # Lower learning rate
            max_depth=8,                # Deeper trees
            num_leaves=63,              # More leaves
            min_child_samples=20,
            subsample=0.8,              # Row sampling
            colsample_bytree=0.8,       # Column sampling
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            verbose=-1,
            reg_alpha=0.1,              # L1 regularization
            reg_lambda=0.1              # L2 regularization
        )
        
        print(f"\nTraining...")
        model.fit(X_train, y_train)
        
        # Evaluate
        print(f"\nEvaluation:")
        
        # Training score
        y_train_pred = model.predict_proba(X_train)[:, 1]
        train_prauc = average_precision_score(y_train, y_train_pred)
        print(f"  Train PR-AUC: {train_prauc:.4f}")
        
        # Validation score if provided
        if X_val is not None and y_val is not None:
            y_val_pred = model.predict_proba(X_val)[:, 1]
            val_prauc = average_precision_score(y_val, y_val_pred)
            print(f"  Val PR-AUC: {val_prauc:.4f}")
            
            # Check for overfitting
            if train_prauc - val_prauc > 0.1:
                print(f"  ⚠️  Warning: Possible overfitting (gap: {train_prauc - val_prauc:.4f})")
            else:
                print(f"  ✅ Good generalization (gap: {train_prauc - val_prauc:.4f})")
        
        self.model = model
        self.model_type = 'lightgbm'
        
        print("\n" + "=" * 80)
        print("✅ Model training complete!")
        print("=" * 80)
        
        return model
    
    def save_model(self, path='models/model.pkl'):
        """Save trained model"""
        if self.model is None:
            raise ValueError("No model to save! Train first.")
        
        joblib.dump(self.model, path)
        print(f"✅ Model saved to {path}")
    
    def load_model(self, path='models/model.pkl'):
        """Load trained model"""
        self.model = joblib.load(path)
        print(f"✅ Model loaded from {path}")
        return self.model


if __name__ == "__main__":
    from src.data.loader import load_data
    from src.data.splitter import temporal_split
    from src.features.pipeline import FeatureEngineeringPipeline
    
    print("Testing Model Trainer...")
    
    # Load data
    df = load_data(nrows=5000)
    
    # Split
    train, val, test = temporal_split(df)
    
    # Extract features
    pipeline = FeatureEngineeringPipeline()
    X_train = pipeline.fit_transform(train, target='isFraud')
    X_val = pipeline.transform(val)
    
    y_train = train['isFraud']
    y_val = val['isFraud']
    
    # Train
    trainer = ModelTrainer()
    model = trainer.train_lightgbm(X_train, y_train, X_val, y_val)
    
    print("\n✅ Model trainer test complete!")
