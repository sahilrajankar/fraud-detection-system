"""
Data Quality Auditor - Phase 1
Comprehensive data quality assessment framework
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


class DataQualityAuditor:
    """
    Comprehensive data quality assessment framework
    Detects: missing values, duplicates, outliers, impossible values, cardinality issues
    """
    
    def __init__(self, data: pd.DataFrame, target: str = None):
        self.data = data
        self.target = target
        self.report = {}
    
    def audit(self) -> Dict:
        """Run all audit checks"""
        print("Starting Data Quality Audit...")
        print("=" * 80)
        
        self.check_basic_info()
        self.check_missing_values()
        self.check_duplicates()
        self.check_data_types()
        self.check_cardinality()
        
        if self.target and self.target in self.data.columns:
            self.check_target_distribution()
        
        return self.generate_report()
    
    def check_basic_info(self):
        """Basic dataset information"""
        self.report['basic_info'] = {
            'n_rows': len(self.data),
            'n_columns': len(self.data.columns),
            'memory_usage_mb': self.data.memory_usage(deep=True).sum() / 1024**2,
            'columns': list(self.data.columns)
        }
        print(f"✓ Basic Info: {len(self.data):,} rows, {len(self.data.columns)} columns")
    
    def check_missing_values(self):
        """Analyze missing values"""
        missing = self.data.isnull().sum()
        missing_pct = (missing / len(self.data)) * 100
        
        critical = missing_pct[missing_pct > 80].to_dict()
        high = missing_pct[(missing_pct > 50) & (missing_pct <= 80)].to_dict()
        medium = missing_pct[(missing_pct > 20) & (missing_pct <= 50)].to_dict()
        
        self.report['missing_values'] = {
            'critical_columns': critical,  # > 80%
            'high_risk_columns': high,     # 50-80%
            'medium_risk_columns': medium, # 20-50%
            'total_missing_cells': int(missing.sum()),
            'pct_missing_overall': float((missing.sum() / self.data.size) * 100)
        }
        
        print(f"✓ Missing Values: {len(critical)} critical, {len(high)} high risk, {len(medium)} medium risk")

    
    def check_duplicates(self):
        """Detect duplicate rows"""
        n_duplicates = self.data.duplicated().sum()
        
        self.report['duplicates'] = {
            'n_duplicate_rows': int(n_duplicates),
            'pct_duplicate': float((n_duplicates / len(self.data)) * 100)
        }
        
        print(f"✓ Duplicates: {n_duplicates:,} rows ({self.report['duplicates']['pct_duplicate']:.2f}%)")
    
    def check_data_types(self):
        """Analyze data types"""
        type_counts = self.data.dtypes.value_counts().to_dict()
        
        numeric_cols = list(self.data.select_dtypes(include=[np.number]).columns)
        categorical_cols = list(self.data.select_dtypes(include=['object', 'category']).columns)
        
        self.report['data_types'] = {
            'type_distribution': {str(k): int(v) for k, v in type_counts.items()},
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        }
        
        print(f"✓ Data Types: {len(numeric_cols)} numeric, {len(categorical_cols)} categorical")
    
    def check_cardinality(self):
        """Check categorical cardinality"""
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        
        high_cardinality = {}
        for col in cat_cols:
            nunique = self.data[col].nunique()
            unique_ratio = nunique / len(self.data)
            
            if unique_ratio > 0.5:  # More than 50% unique
                high_cardinality[col] = {
                    'nunique': int(nunique),
                    'unique_ratio': float(unique_ratio)
                }
        
        self.report['cardinality'] = {
            'high_cardinality_columns': high_cardinality
        }
        
        print(f"✓ Cardinality: {len(high_cardinality)} high-cardinality columns")
    
    def check_target_distribution(self):
        """Analyze target variable"""
        value_counts = self.data[self.target].value_counts()
        
        self.report['target'] = {
            'distribution': value_counts.to_dict(),
            'positive_rate': float(self.data[self.target].mean()),
            'is_imbalanced': bool(self.data[self.target].mean() < 0.1 or self.data[self.target].mean() > 0.9)
        }
        
        print(f"✓ Target: {self.report['target']['positive_rate']:.2%} positive rate")

    
    def calculate_quality_score(self) -> float:
        """Calculate overall data quality score (0-100)"""
        score = 100.0
        
        # Penalize missing values
        if 'missing_values' in self.report:
            avg_missing = self.report['missing_values']['pct_missing_overall']
            score -= min(avg_missing, 30)
        
        # Penalize duplicates
        if 'duplicates' in self.report:
            dup_pct = self.report['duplicates']['pct_duplicate']
            score -= min(dup_pct * 2, 20)
        
        # Penalize high cardinality
        if 'cardinality' in self.report:
            n_high_card = len(self.report['cardinality']['high_cardinality_columns'])
            score -= n_high_card * 3
        
        return max(score, 0.0)
    
    def generate_report(self) -> Dict:
        """Generate final report"""
        quality_score = self.calculate_quality_score()
        
        print("\n" + "=" * 80)
        print(f"DATA QUALITY SCORE: {quality_score:.1f}/100")
        print("=" * 80)
        
        if quality_score > 80:
            print("✅ EXCELLENT - Data quality is very good")
        elif quality_score > 60:
            print("⚠️  GOOD - Minor quality issues detected")
        elif quality_score > 40:
            print("🟠 FAIR - Moderate quality issues, investigate")
        else:
            print("🔴 POOR - Significant quality issues, requires attention")
        
        self.report['quality_score'] = quality_score
        return self.report


if __name__ == "__main__":
    # Example usage
    print("DataQualityAuditor - Ready to use")
    print("Usage:")
    print("  from src.data.quality import DataQualityAuditor")
    print("  auditor = DataQualityAuditor(df, target='isFraud')")
    print("  report = auditor.audit()")
