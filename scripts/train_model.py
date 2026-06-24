"""
End-to-End Model Training Script
Complete pipeline: Load → Split → Features → Train → Evaluate → Save
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from pathlib import Path

from src.data.loader import load_data
from src.data.splitter import temporal_split
from src.features.pipeline import FeatureEngineeringPipeline
from src.models.trainer import ModelTrainer
from src.validation.leakage_detector import LeakageDetector
from src.validation.metrics import evaluate_model, print_evaluation_report


def train_production_model(nrows=None, detect_leakage=True):
    """
    Complete training pipeline
    
    Args:
        nrows: Number of rows to load (None = all data)
        detect_leakage: Run leakage detection (recommended!)
    """
    print("\n" + "=" * 80)
    print("PRODUCTION MODEL TRAINING PIPELINE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Load data
    print("\n" + "=" * 80)
    print("STEP 1: DATA LOADING")
    print("=" * 80)
    df = load_data(nrows=nrows)
    
    # 2. Temporal split
    print("\n" + "=" * 80)
    print("STEP 2: TEMPORAL SPLITTING (NO RANDOM!)")
    print("=" * 80)
    train_df, val_df, test_df = temporal_split(df)
    
    # 3. Feature engineering
    print("\n" + "=" * 80)
    print("STEP 3: FEATURE ENGINEERING")
    print("=" * 80)
    
    pipeline = FeatureEngineeringPipeline()
    
    print("\nFitting pipeline on training data...")
    X_train = pipeline.fit_transform(train_df, target='isFraud')
    y_train = train_df['isFraud']
    
    print("\nTransforming validation data...")
    X_val = pipeline.transform(val_df)
    y_val = val_df['isFraud']
    
    print("\nTransforming test data...")
    X_test = pipeline.transform(test_df)
    y_test = test_df['isFraud']
    
    print(f"\n✅ Feature engineering complete!")
    print(f"   Train: {X_train.shape}")
    print(f"   Val:   {X_val.shape}")
    print(f"   Test:  {X_test.shape}")
    
    # 4. Leakage detection (CRITICAL!)
    if detect_leakage:
        print("\n" + "=" * 80)
        print("STEP 4: LEAKAGE DETECTION")
        print("=" * 80)
        
        detector = LeakageDetector(X_train, y_train)
        leakage_report = detector.detect_all()
        
        # If critical leakage found, STOP
        if len(leakage_report.get('perfect_predictors', {})) > 0:
            print("\n❌ CRITICAL LEAKAGE DETECTED - STOPPING")
            print("Review and remove leaky features before proceeding!")
            return None
    
    # 5. Train model
    print("\n" + "=" * 80)
    print("STEP 5: MODEL TRAINING")
    print("=" * 80)
    
    trainer = ModelTrainer()
    model = trainer.train_lightgbm(X_train, y_train, X_val, y_val)
    
    # 6. Evaluate on all sets
    print("\n" + "=" * 80)
    print("STEP 6: MODEL EVALUATION")
    print("=" * 80)
    
    # Training set
    y_train_pred = model.predict_proba(X_train)[:, 1]
    train_results = evaluate_model(y_train, y_train_pred)
    print_evaluation_report(train_results, dataset_name='Training')
    
    # Validation set
    y_val_pred = model.predict_proba(X_val)[:, 1]
    val_results = evaluate_model(y_val, y_val_pred)
    print_evaluation_report(val_results, dataset_name='Validation')
    
    # Test set
    y_test_pred = model.predict_proba(X_test)[:, 1]
    test_results = evaluate_model(y_test, y_test_pred)
    print_evaluation_report(test_results, dataset_name='Test')
    
    # 7. Save model and pipeline
    print("\n" + "=" * 80)
    print("STEP 7: SAVING MODEL AND ARTIFACTS")
    print("=" * 80)
    
    # Create models directory
    Path('models').mkdir(exist_ok=True)
    
    # Save model
    model_path = 'models/fraud_model.pkl'
    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")
    
    # Save pipeline
    pipeline_path = 'models/feature_pipeline.pkl'
    joblib.dump(pipeline, pipeline_path)
    print(f"✅ Feature pipeline saved to {pipeline_path}")
    
    # Save results
    results_path = 'models/evaluation_results.pkl'
    joblib.dump({
        'train': train_results,
        'val': val_results,
        'test': test_results
    }, results_path)
    print(f"✅ Evaluation results saved to {results_path}")
    
    # 8. Summary
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE - SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 Final Performance:")
    print(f"   Test PR-AUC:    {test_results['pr_auc']:.4f}")
    print(f"   Test ROC-AUC:   {test_results['roc_auc']:.4f}")
    print(f"   Fraud Capture:  {test_results['fraud_capture_rate']:.2%} (top 5%)")
    
    print(f"\n📁 Artifacts Saved:")
    print(f"   - {model_path}")
    print(f"   - {pipeline_path}")
    print(f"   - {results_path}")
    
    print(f"\n✅ Ready for production deployment!")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return {
        'model': model,
        'pipeline': pipeline,
        'results': {
            'train': train_results,
            'val': val_results,
            'test': test_results
        }
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train fraud detection model')
    parser.add_argument('--nrows', type=int, default=None, 
                       help='Number of rows to load (default: all)')
    parser.add_argument('--skip-leakage', action='store_true',
                       help='Skip leakage detection (not recommended!)')
    
    args = parser.parse_args()
    
    # Train
    results = train_production_model(
        nrows=args.nrows,
        detect_leakage=not args.skip_leakage
    )
    
    if results is None:
        print("\n❌ Training failed - check logs above")
        sys.exit(1)
    else:
        print("\n✅ Training succeeded!")
        sys.exit(0)
