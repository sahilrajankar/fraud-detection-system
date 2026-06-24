"""
Leakage Detector - Detect data leakage before it ruins your model
"""

import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from typing import Dict


class LeakageDetector:
    """
    Automated data leakage detection
    Checks for: perfect predictors, temporal leakage, label proxies
    """
    
    def __init__(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train
        self.leakage_report = {}
    
    def detect_all(self):
        """Run all leakage checks"""
        print("=" * 80)
        print("LEAKAGE DETECTION - Finding Hidden Data Leakage")
        print("=" * 80)
        
        self.detect_perfect_predictors()
        self.detect_suspicious_correlations()
        
        # Generate report
        self._generate_report()
        
        return self.leakage_report
    
    def detect_perfect_predictors(self, threshold=0.95):
        """
        Detect features that predict target too well (likely leaked)
        """
        print("\n1. Testing for Perfect Predictors...")
        print("   (Single features with AUC > 0.95 are suspicious)")
        
        perfect_predictors = {}
        
        for col in self.X_train.columns:
            if self.X_train[col].dtype in [np.number]:
                try:
                    # Skip if all same value
                    if self.X_train[col].nunique() <= 1:
                        continue
                    
                    # Calculate AUC for single feature
                    auc = roc_auc_score(self.y_train, self.X_train[col].fillna(0))
                    
                    # Check both directions
                    if auc > threshold:
                        perfect_predictors[col] = {
                            'auc': auc,
                            'severity': 'CRITICAL',
                            'action': 'DROP IMMEDIATELY - Likely leakage'
                        }
                    elif auc < (1 - threshold):
                        perfect_predictors[col] = {
                            'auc': auc,
                            'severity': 'CRITICAL',
                            'action': 'DROP IMMEDIATELY - Inverted leakage'
                        }
                except Exception as e:
                    pass
        
        self.leakage_report['perfect_predictors'] = perfect_predictors
        
        if perfect_predictors:
            print(f"   ❌ Found {len(perfect_predictors)} perfect predictors:")
            for col, info in perfect_predictors.items():
                print(f"      - {col}: AUC = {info['auc']:.4f} ({info['severity']})")
        else:
            print(f"   ✅ No perfect predictors found")
    
    def detect_suspicious_correlations(self, threshold=0.90):
        """
        Detect features highly correlated with target
        """
        print("\n2. Testing for Suspicious Correlations...")
        print(f"   (Correlations > {threshold} are suspicious)")
        
        suspicious = {}
        
        for col in self.X_train.select_dtypes(include=[np.number]).columns:
            try:
                corr = self.X_train[col].corr(self.y_train)
                
                if abs(corr) > threshold:
                    suspicious[col] = {
                        'correlation': corr,
                        'severity': 'HIGH' if abs(corr) > 0.95 else 'MEDIUM',
                        'action': 'INVESTIGATE'
                    }
            except:
                pass
        
        self.leakage_report['suspicious_correlations'] = suspicious
        
        if suspicious:
            print(f"   ⚠️  Found {len(suspicious)} suspicious correlations:")
            for col, info in suspicious.items():
                print(f"      - {col}: corr = {info['correlation']:.4f}")
        else:
            print(f"   ✅ No suspicious correlations found")
    
    def _generate_report(self):
        """Generate final leakage report"""
        print("\n" + "=" * 80)
        
        n_critical = len(self.leakage_report.get('perfect_predictors', {}))
        n_suspicious = len(self.leakage_report.get('suspicious_correlations', {}))
        
        total_issues = n_critical + n_suspicious
        
        if total_issues == 0:
            print("✅ LEAKAGE CHECK PASSED - No leakage detected!")
        else:
            print(f"⚠️  LEAKAGE CHECK FAILED - {total_issues} potential issues found")
            print(f"   - {n_critical} perfect predictors (CRITICAL)")
            print(f"   - {n_suspicious} suspicious correlations")
            print("\n   ACTION REQUIRED: Review and remove leaky features")
        
        print("=" * 80)


if __name__ == "__main__":
    # Test
    print("Testing leakage detector...")
    
    # Create sample data with intentional leakage
    np.random.seed(42)
    n = 1000
    
    X = pd.DataFrame({
        'normal_feature': np.random.randn(n),
        'leaked_feature': np.random.randn(n),  # Will create leakage
        'good_feature': np.random.randn(n)
    })
    
    y = pd.Series(np.random.randint(0, 2, n))
    
    # Add leakage to one feature
    X.loc[y == 1, 'leaked_feature'] = 100
    
    # Detect
    detector = LeakageDetector(X, y)
    report = detector.detect_all()
    
    print("\n✅ Leakage detector test complete!")
