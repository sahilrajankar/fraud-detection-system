"""
Evaluation Metrics - Production-focused metrics
NO ACCURACY! Use PR-AUC, Recall@K, etc.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_recall_curve,
    matthews_corrcoef,
    confusion_matrix
)


def recall_at_k(y_true, y_pred_proba, k_pct):
    """
    Recall at top K% of predictions
    
    Example: recall_at_k(y, pred, 0.01) = How many frauds captured in top 1%?
    """
    k = int(len(y_true) * k_pct)
    k = max(1, k)  # At least 1
    
    # Sort by predicted probability (descending)
    sorted_idx = np.argsort(y_pred_proba)[::-1][:k]
    
    # How many true frauds in top-k?
    frauds_captured = y_true.iloc[sorted_idx].sum() if isinstance(y_true, pd.Series) else y_true[sorted_idx].sum()
    total_frauds = y_true.sum()
    
    return frauds_captured / total_frauds if total_frauds > 0 else 0.0


def precision_at_k(y_true, y_pred_proba, k_pct):
    """
    Precision at top K% of predictions
    
    Example: precision_at_k(y, pred, 0.01) = What % of top 1% are frauds?
    """
    k = int(len(y_true) * k_pct)
    k = max(1, k)
    
    sorted_idx = np.argsort(y_pred_proba)[::-1][:k]
    
    frauds_in_top_k = y_true.iloc[sorted_idx].sum() if isinstance(y_true, pd.Series) else y_true[sorted_idx].sum()
    
    return frauds_in_top_k / k


def evaluate_model(y_true, y_pred_proba, thresholds=[0.01, 0.02, 0.05, 0.10]):
    """
    Comprehensive model evaluation
    
    Returns dict with all metrics
    """
    results = {
        'pr_auc': average_precision_score(y_true, y_pred_proba),
        'roc_auc': roc_auc_score(y_true, y_pred_proba),
    }
    
    # Recall at various K
    for k in thresholds:
        results[f'recall_at_{int(k*100)}pct'] = recall_at_k(y_true, y_pred_proba, k)
        results[f'precision_at_{int(k*100)}pct'] = precision_at_k(y_true, y_pred_proba, k)
    
    # Find optimal threshold (max MCC)
    precision, recall, thresholds_pr = precision_recall_curve(y_true, y_pred_proba)
    
    # Compute MCC for each threshold
    best_mcc = -1
    best_threshold = 0.5
    for thresh in np.linspace(0.01, 0.99, 50):
        y_pred_binary = (y_pred_proba >= thresh).astype(int)
        try:
            mcc = matthews_corrcoef(y_true, y_pred_binary)
            if mcc > best_mcc:
                best_mcc = mcc
                best_threshold = thresh
        except:
            pass
    
    results['best_threshold'] = best_threshold
    results['best_mcc'] = best_mcc
    
    # Confusion matrix at optimal threshold
    y_pred_binary = (y_pred_proba >= best_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred_binary).ravel()
    
    results['confusion_matrix'] = {
        'TP': int(tp),
        'FP': int(fp),
        'TN': int(tn),
        'FN': int(fn)
    }
    
    # Business metrics
    results['fraud_capture_rate'] = recall_at_k(y_true, y_pred_proba, 0.05)  # Top 5%
    results['investigation_yield'] = precision_at_k(y_true, y_pred_proba, 0.05)  # Top 5%
    
    return results


def print_evaluation_report(results, dataset_name='Validation'):
    """
    Print formatted evaluation report
    """
    print("=" * 80)
    print(f"{dataset_name} Set Evaluation")
    print("=" * 80)
    
    print(f"\n📊 Overall Metrics:")
    print(f"   PR-AUC:       {results['pr_auc']:.4f}")
    print(f"   ROC-AUC:      {results['roc_auc']:.4f}")
    print(f"   Best MCC:     {results['best_mcc']:.4f} (at threshold {results['best_threshold']:.3f})")
    
    print(f"\n🎯 Recall @ Top-K (Fraud Detection):")
    for k in [1, 2, 5, 10]:
        key = f'recall_at_{k}pct'
        if key in results:
            print(f"   Top {k}%:       {results[key]:.2%} of frauds captured")
    
    print(f"\n🔍 Precision @ Top-K (Investigation Yield):")
    for k in [1, 2, 5, 10]:
        key = f'precision_at_{k}pct'
        if key in results:
            baseline = 0.035  # 3.5% fraud rate
            improvement = results[key] / baseline if baseline > 0 else 0
            print(f"   Top {k}%:       {results[key]:.2%} ({improvement:.1f}x better than random)")
    
    print(f"\n💼 Business Metrics (Top 5%):")
    print(f"   Fraud Capture:     {results['fraud_capture_rate']:.2%}")
    print(f"   Investigation Yield: {results['investigation_yield']:.2%}")
    
    cm = results['confusion_matrix']
    print(f"\n📋 Confusion Matrix (at optimal threshold):")
    print(f"   True Positives:   {cm['TP']:,}")
    print(f"   False Positives:  {cm['FP']:,}")
    print(f"   True Negatives:   {cm['TN']:,}")
    print(f"   False Negatives:  {cm['FN']:,}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Test
    print("Testing evaluation metrics...")
    
    # Create sample predictions
    np.random.seed(42)
    n = 1000
    
    # Simulate 3.5% fraud rate
    y_true = np.random.choice([0, 1], size=n, p=[0.965, 0.035])
    
    # Simulate model that's somewhat good at predicting
    y_pred_proba = np.random.rand(n)
    y_pred_proba[y_true == 1] += 0.3  # Frauds get higher scores
    y_pred_proba = np.clip(y_pred_proba, 0, 1)
    
    # Evaluate
    results = evaluate_model(y_true, y_pred_proba)
    print_evaluation_report(results, dataset_name='Test')
    
    print("\n✅ Metrics module test complete!")
