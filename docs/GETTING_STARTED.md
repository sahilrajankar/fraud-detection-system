# Getting Started - Implementation Guide

## Immediate Next Steps

### Phase 1: Environment Setup (30 minutes)

#### 1. Create Project Directory

```bash
# Create main project folder
cd d:\
mkdir risk-scoring-system
cd risk-scoring-system
```

#### 2. Initialize Git Repository

```bash
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Create .gitignore
echo "venv/
__pycache__/
*.pyc
.env
data/raw/
*.pkl
*.joblib
.ipynb_checkpoints/
.vscode/
*.log" > .gitignore
```

#### 3. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate
```

#### 4. Install Dependencies

```bash
# Create requirements.txt
echo "pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
lightgbm==4.0.0
xgboost==1.7.6
catboost==1.2
imbalanced-learn==0.11.0
shap==0.42.1
matplotlib==3.7.2
seaborn==0.12.2
plotly==5.16.0
fastapi==0.103.0
uvicorn==0.23.2
pydantic==2.3.0
streamlit==1.26.0
python-multipart==0.0.6
python-dotenv==1.0.0
pyyaml==6.0.1
mlflow==2.6.0
pytest==7.4.0
jupyter==1.0.0
kaggle==1.5.16" > requirements.txt

# Install
pip install -r requirements.txt
```

#### 5. Create Project Structure

```bash
# Create all directories
mkdir config data notebooks src tests models experiments reports streamlit_app scripts deployment docs

# Data subdirectories
mkdir data\raw data\processed data\splits data\metadata

# Source subdirectories
mkdir src\data src\features src\models src\validation src\monitoring src\inference src\utils

# Test subdirectories
mkdir tests\test_data tests\test_features tests\test_models tests\test_inference

# Streamlit subdirectories
mkdir streamlit_app\pages streamlit_app\utils streamlit_app\assets

# Deployment subdirectories
mkdir deployment\kubernetes deployment\terraform

# Create __init__.py files
type nul > src\__init__.py
type nul > src\data\__init__.py
type nul > src\features\__init__.py
type nul > src\models\__init__.py
type nul > src\validation\__init__.py
type nul > src\monitoring\__init__.py
type nul > src\inference\__init__.py
type nul > src\utils\__init__.py
type nul > tests\__init__.py
```

---

## Phase 2: Download Dataset (30 minutes)

### Option A: Using Kaggle API (Recommended)

#### 1. Set Up Kaggle API

```bash
# Install kaggle (already in requirements.txt)
pip install kaggle

# Create kaggle.json with your API credentials
# Get from: https://www.kaggle.com/settings → Create New API Token

# Windows: Place in C:\Users\YourName\.kaggle\kaggle.json
# Make sure it has your credentials:
# {
#   "username": "your_kaggle_username",
#   "key": "your_api_key"
# }
```

#### 2. Download IEEE-CIS Dataset

```bash
# Download the dataset
kaggle competitions download -c ieee-fraud-detection

# Unzip to data/raw/
# You'll get:
# - train_transaction.csv
# - train_identity.csv
# - test_transaction.csv
# - test_identity.csv
# - sample_submission.csv
```

### Option B: Manual Download

1. Go to https://www.kaggle.com/c/ieee-fraud-detection/data
2. Download all files
3. Extract to `d:\risk-scoring-system\data\raw\`

---

## Phase 3: First Code - Data Exploration (1 hour)

### Create Your First Notebook

```bash
jupyter notebook
# Create: notebooks/01_eda.ipynb
```

### Initial EDA Code

```python
# notebooks/01_eda.ipynb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
train_transaction = pd.read_csv('../data/raw/train_transaction.csv')
train_identity = pd.read_csv('../data/raw/train_identity.csv')

# Merge
train = train_transaction.merge(train_identity, on='TransactionID', how='left')

print("=" * 80)
print("DATASET OVERVIEW")
print("=" * 80)
print(f"Shape: {train.shape}")
print(f"Columns: {train.shape[1]}")
print(f"Rows: {train.shape[0]:,}")
print()

# Target distribution
fraud_rate = train['isFraud'].mean()
print(f"Fraud Rate: {fraud_rate:.2%}")
print(f"Fraud Cases: {train['isFraud'].sum():,}")
print(f"Legit Cases: {(~train['isFraud'].astype(bool)).sum():,}")
print()

# Missing values
missing = train.isnull().sum().sort_values(ascending=False)
missing_pct = (missing / len(train) * 100).round(2)
missing_df = pd.DataFrame({
    'Missing_Count': missing,
    'Missing_Pct': missing_pct
})
print("Top 10 Columns with Missing Values:")
print(missing_df.head(10))
print()

# Data types
print("Data Types:")
print(train.dtypes.value_counts())
print()

# Temporal coverage
print("Temporal Information:")
print(f"TransactionDT range: {train['TransactionDT'].min()} to {train['TransactionDT'].max()}")
print(f"Time span: {train['TransactionDT'].max() - train['TransactionDT'].min()} time units")
```

---

## Phase 4: First Real Code - Data Quality Auditor (2 hours)

### Create `src/data/quality.py`

```python
# src/data/quality.py

import pandas as pd
import numpy as np
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

class DataQualityAuditor:
    """
    Comprehensive data quality assessment framework
    """
    
    def __init__(self, data: pd.DataFrame, target: str = None):
        self.data = data
        self.target = target
        self.report = {}
    
    def audit(self) -> Dict:
        """Run all audit checks"""
        print("Starting Data Quality Audit...")
        
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
            'total_missing_cells': missing.sum(),
            'pct_missing_overall': (missing.sum() / self.data.size) * 100
        }
        
        print(f"✓ Missing Values: {len(critical)} critical, {len(high)} high risk")
    
    def check_duplicates(self):
        """Detect duplicate rows"""
        n_duplicates = self.data.duplicated().sum()
        
        self.report['duplicates'] = {
            'n_duplicate_rows': n_duplicates,
            'pct_duplicate': (n_duplicates / len(self.data)) * 100
        }
        
        print(f"✓ Duplicates: {n_duplicates:,} rows ({self.report['duplicates']['pct_duplicate']:.2f}%)")
    
    def check_data_types(self):
        """Analyze data types"""
        type_counts = self.data.dtypes.value_counts().to_dict()
        
        self.report['data_types'] = {
            'type_distribution': {str(k): v for k, v in type_counts.items()},
            'numeric_columns': list(self.data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(self.data.select_dtypes(include=['object', 'category']).columns)
        }
        
        print(f"✓ Data Types: {len(self.report['data_types']['numeric_columns'])} numeric, "
              f"{len(self.report['data_types']['categorical_columns'])} categorical")
    
    def check_cardinality(self):
        """Check categorical cardinality"""
        cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
        
        high_cardinality = {}
        for col in cat_cols:
            nunique = self.data[col].nunique()
            unique_ratio = nunique / len(self.data)
            
            if unique_ratio > 0.5:  # More than 50% unique
                high_cardinality[col] = {
                    'nunique': nunique,
                    'unique_ratio': unique_ratio
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
            'positive_rate': self.data[self.target].mean(),
            'is_imbalanced': self.data[self.target].mean() < 0.1 or self.data[self.target].mean() > 0.9
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

# Example usage
if __name__ == "__main__":
    # Test with sample data
    df = pd.read_csv('../data/raw/train_transaction.csv', nrows=10000)
    
    auditor = DataQualityAuditor(df, target='isFraud')
    report = auditor.audit()
```

### Test It

```bash
cd d:\risk-scoring-system
python src\data\quality.py
```

---

## Phase 5: Next 48 Hours - Follow the Roadmap

Now that you have the foundation, follow **IMPLEMENTATION_ROADMAP.md** hour by hour:

### Hours 4-8: Leakage Detection
- Implement `src/validation/leakage_detector.py`
- Test on the dataset

### Hours 8-14: Temporal Splits & Validation
- Implement `src/data/splitter.py`
- Create train/val/gap/test splits

### Hours 14-24: Feature Engineering
- Implement `src/features/schema_agnostic.py`
- Build 50-100 features

### Hours 24-32: Modeling
- Train 5 models
- Compare and select best

### Hours 32-44: Production API
- Build FastAPI endpoint
- Test schema drift handling

### Hours 44-48: Dashboard & Docs
- Create Streamlit app
- Final testing

---

## Quick Commands Reference

```bash
# Activate environment
cd d:\risk-scoring-system
venv\Scripts\activate

# Run tests
pytest tests/

# Start Jupyter
jupyter notebook

# Train model
python scripts/train_model.py

# Start API
uvicorn src.inference.api:app --reload

# Start Streamlit
streamlit run streamlit_app/app.py

# Run quality audit
python src/data/quality.py
```

---

## 🆘 If You Get Stuck

**Data issues?** → Check data/raw/ folder has the CSV files  
**Import errors?** → Make sure venv is activated  
**Kaggle API?** → Check credentials in ~/.kaggle/kaggle.json  
**Code questions?** → Refer to QUICK_REFERENCE.md  
**Design questions?** → Refer to TECHNICAL_DESIGN_DOCUMENT.md  

---

## ✅ Success Checklist - First 4 Hours

- [ ] Environment set up
- [ ] Dependencies installed
- [ ] Project structure created
- [ ] Dataset downloaded
- [ ] Initial EDA completed
- [ ] DataQualityAuditor working
- [ ] Git repository initialized

After this, you're ready for the main implementation!

