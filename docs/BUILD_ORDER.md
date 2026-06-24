# Build Order - Next Steps

## ✅ What's Already Done

1. Project structure created
2. DataQualityAuditor (src/data/quality.py)
3. SchemaAgnosticFeatureEngineer (src/features/schema_agnostic.py)
4. UniversalTransactionFeatures (src/features/universal_features.py)
5. ConfidenceScorer (src/inference/confidence_scorer.py)

---

## 🚀 BUILD THESE NEXT (In Order)

### Priority 1: Data Loading & Splitting (30 minutes)

**File:** `src/data/loader.py`
```python
# Load IEEE-CIS data
# Merge transaction + identity tables
# Basic cleaning
```

**File:** `src/data/splitter.py`
```python
# Temporal split with gap period
# Train: Days 0-108 (60%)
# Gap: Days 108-122 (14 days)
# Val: Days 122-144 (20%)
# Test: Days 144-180 (20%)
```

**Test it:**
```python
from src.data.loader import load_data
from src.data.splitter import temporal_split

df = load_data('data/raw/train_transaction.csv')
train, val, test = temporal_split(df)
print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
```

---

### Priority 2: Leakage Detection (30 minutes)

**File:** `src/validation/leakage_detector.py`
```python
class LeakageDetector:
    def detect_perfect_predictors(self, threshold=0.95):
        # Check each feature's AUC
        # Flag if AUC > 0.95
    
    def detect_temporal_leakage(self):
        # Check if features use future data
```

**Test it:**
```python
from src.validation.leakage_detector import LeakageDetector

detector = LeakageDetector(X_train, y_train)
report = detector.detect_all()
print(report)  # Should show no leakage
```

---

### Priority 3: Feature Engineering Pipeline (1 hour)

**File:** `src/features/pipeline.py`
```python
class FeatureEngineeringPipeline:
    """Combines schema-agnostic + universal features"""
    
    def __init__(self):
        self.schema_agnostic = SchemaAgnosticFeatureEngineer()
        self.universal = UniversalTransactionFeatures()
    
    def fit_transform(self, df, target):
        # Extract both types of features
        # Combine them
        # Return final feature matrix
```

**Test it:**
```python
pipeline = FeatureEngineeringPipeline()
X_train_features = pipeline.fit_transform(train_df, target='isFraud')
X_val_features = pipeline.transform(val_df)
print(f"Features: {X_train_features.shape}")
```

---

### Priority 4: Model Training (1 hour)

**File:** `src/models/trainer.py`
```python
from lightgbm import LGBMClassifier

class ModelTrainer:
    def train_lightgbm(self, X, y):
        model = LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=7,
            scale_pos_weight=27,  # For 3.5% fraud rate
            random_state=42
        )
        model.fit(X, y)
        return model
```

**Test it:**
```python
from src.models.trainer import ModelTrainer

trainer = ModelTrainer()
model = trainer.train_lightgbm(X_train, y_train)

# Predict
y_pred = model.predict_proba(X_val)[:, 1]
from sklearn.metrics import average_precision_score
pr_auc = average_precision_score(y_val, y_pred)
print(f"PR-AUC: {pr_auc:.3f}")
```

---

### Priority 5: Evaluation (30 minutes)

**File:** `src/validation/metrics.py`
```python
def evaluate_model(y_true, y_pred_proba):
    from sklearn.metrics import average_precision_score, matthews_corrcoef
    
    results = {
        'pr_auc': average_precision_score(y_true, y_pred_proba),
        'recall_at_1pct': recall_at_k(y_true, y_pred_proba, k=int(len(y_true)*0.01)),
        'recall_at_5pct': recall_at_k(y_true, y_pred_proba, k=int(len(y_true)*0.05)),
    }
    return results

def recall_at_k(y_true, y_pred_proba, k):
    sorted_idx = np.argsort(y_pred_proba)[::-1][:k]
    return y_true.iloc[sorted_idx].sum() / y_true.sum()
```

---

### Priority 6: Inference API (1 hour)

**File:** `src/inference/api.py`
```python
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.post("/predict")
def predict(data: dict):
    # Convert to DataFrame
    df = pd.DataFrame([data])
    
    # Schema handling
    # Feature extraction
    # Prediction
    # Confidence score
    
    return {
        "fraud_probability": 0.75,
        "risk_level": "HIGH",
        "confidence": 0.85
    }
```

**Test it:**
```bash
uvicorn src.inference.api:app --reload
# Visit: http://localhost:8000/docs
```

---

### Priority 7: End-to-End Script (30 minutes)

**File:** `scripts/train_model.py`
```python
"""
Complete training pipeline
"""

# 1. Load data
# 2. Run quality audit
# 3. Check for leakage
# 4. Temporal split
# 5. Feature engineering
# 6. Train model
# 7. Evaluate
# 8. Save model
```

**Run it:**
```bash
python scripts/train_model.py
```

---

## 📊 Timeline

| Task | Time | Priority |
|------|------|----------|
| Data loading & splitting | 30 min | P0 |
| Leakage detection | 30 min | P0 |
| Feature pipeline | 1 hour | P0 |
| Model training | 1 hour | P0 |
| Evaluation metrics | 30 min | P0 |
| Inference API | 1 hour | P1 |
| End-to-end script | 30 min | P1 |
| **TOTAL** | **5.5 hours** | |

---

## ✅ Success Criteria

After building these, you should be able to:

1. ✅ Load IEEE-CIS data
2. ✅ Split it temporally (no leakage)
3. ✅ Detect any data leakage
4. ✅ Extract 50+ features (schema-agnostic + universal)
5. ✅ Train a LightGBM model
6. ✅ Get PR-AUC > 0.30
7. ✅ Make predictions via API
8. ✅ Handle schema changes gracefully

---

## 🎯 What to Build TODAY

**Minimum (3 hours):**
- Data loading & splitting
- Feature pipeline
- Model training
- Basic evaluation

**Ideal (5 hours):**
- Above + Leakage detection
- Above + Inference API

**Tomorrow:**
- Streamlit dashboard
- Monitoring & drift detection
- Documentation & testing

---

## 📝 Quick Command Reference

```bash
# Activate environment
venv\Scripts\activate

# Test components
python src\features\schema_agnostic.py
python src\features\universal_features.py

# Train model (once built)
python scripts\train_model.py

# Start API (once built)
uvicorn src.inference.api:app --reload

# Run tests (once built)
pytest tests/
```

---

## 🆘 If You Get Stuck

1. **Data not loading?** Check data/raw/ has CSV files
2. **Import errors?** Make sure venv is activated
3. **Out of memory?** Load first 100k rows: `nrows=100000`
4. **Model not training?** Check for NaN values in features
5. **Low performance?** Check for data leakage first

---

## Next: Choose Your Path

**Path A: Build Everything (Recommended)**
- Follow the build order above
- Takes 5-6 hours total
- Production-ready system

**Path B: Quick Prototype (Faster)**
- Skip leakage detection for now
- Skip API for now
- Just: Load → Features → Train → Evaluate
- Takes 2-3 hours
- Good for testing approach

**Path C: Guided Step-by-Step (Safest)**
- I'll create each file for you one by one
- You test each one
- Takes 6-8 hours but guaranteed to work

Which path do you want? Tell me and I'll guide you!
