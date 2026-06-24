# Quick Reference Guide

## 📂 Document Navigation

**START HERE:** [README.md](README.md) - Overview and quick start

### For Different Needs:

**"What should I build?"**  
→ [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)

**"How do I implement this?"**  
→ [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)

**"What could go wrong?"**  
→ [RISK_REGISTER.md](RISK_REGISTER.md)

**"How is it structured?"**  
→ [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

**"How does it work?"**  
→ [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)

**"How do I evaluate the model?"**  
→ [MODEL_EVALUATION_FRAMEWORK.md](MODEL_EVALUATION_FRAMEWORK.md)

**"How do I defend my design?"**  
→ [INTERVIEW_DEFENSE_NOTES.md](INTERVIEW_DEFENSE_NOTES.md)

**"Show me visually"**  
→ [DIAGRAMS_AND_VISUALS.md](DIAGRAMS_AND_VISUALS.md)

**"What's the complete spec?"**  
→ [TECHNICAL_DESIGN_DOCUMENT.md](TECHNICAL_DESIGN_DOCUMENT.md)

---

## ⚡ Critical Concepts (Don't Forget!)

### 1. NO RANDOM SPLITS!
```python
# ❌ WRONG
X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

# ✅ CORRECT
train_mask = df['TransactionDT'] < train_cutoff
test_mask = df['TransactionDT'] >= test_cutoff
X_train = X[train_mask]
X_test = X[test_mask]
```

### 2. ALWAYS CHECK FOR LEAKAGE
```python
# Before using any feature
leakage_detector = LeakageDetector(X_train, y_train)
report = leakage_detector.detect_all()

# If any feature has AUC > 0.95 → DROP IT!
```

### 3. GAP PERIOD IS MANDATORY
```
Train: Days 0-108
Gap:   Days 108-122  ← This is critical!
Test:  Days 122-140

Without gap: Fraud labels leak from late discoveries
```

### 4. DON'T USE ACCURACY
```python
# ❌ WRONG
accuracy = accuracy_score(y_true, y_pred)  # Useless for 3.5% fraud rate

# ✅ CORRECT
pr_auc = average_precision_score(y_true, y_pred_proba)
recall_at_1pct = recall_at_k(y_true, y_pred_proba, k=int(len(y)*0.01))
```

### 5. SCHEMA-AGNOSTIC FEATURES
```python
# ❌ WRONG - Hardcoded column name
df['amount_feature'] = df['TransactionAmt'] / df['card1']  # Breaks if renamed

# ✅ CORRECT - Pattern-based
amount_cols = [col for col in df.columns if 'amt' in col.lower()]
if amount_cols:
    df['amount_feature'] = df[amount_cols[0]] / df['card1']
else:
    df['amount_feature'] = default_value  # Graceful fallback
```

---

## 🎯 Success Checklist

### Before You Start
- [ ] Read EXECUTIVE_SUMMARY.md
- [ ] Understand temporal validation (no random splits!)
- [ ] Know the 3 critical risks: leakage, temporal leakage, schema drift
- [ ] Downloaded IEEE-CIS dataset

### During Development
- [ ] Run leakage detection after every feature addition
- [ ] Use temporal splits with gap period
- [ ] Test schema drift handling (missing columns, unknown categories)
- [ ] Evaluate using PR-AUC, Recall@K, not accuracy
- [ ] Document all decisions

### Before Submission
- [ ] No feature with AUC > 0.90
- [ ] Walk-forward validation shows stable performance
- [ ] API handles 50+ schema variation test cases
- [ ] Final holdout performance within 5% of validation
- [ ] All documentation complete

---

## 📊 Metric Targets

| Metric | Minimum (Pass) | Good | Excellent |
|--------|---------------|------|-----------|
| PR-AUC | 0.30 | 0.40 | 0.50 |
| Recall@1% | 30% | 35% | 40% |
| Recall@5% | 60% | 70% | 80% |
| Precision@1000 | 30% | 40% | 50% |
| MCC | 0.50 | 0.55 | 0.60 |
| Brier Score | < 0.030 | < 0.025 | < 0.020 |

---

## 🚨 Red Flags (Automatic Failure)

1. ❌ Random train-test split
2. ❌ Perfect/near-perfect validation score (AUC > 0.99)
3. ❌ No leakage detection
4. ❌ No temporal validation
5. ❌ API crashes on schema changes
6. ❌ Using accuracy as primary metric
7. ❌ No gap period in temporal split
8. ❌ Hardcoded feature names everywhere

---

## 💡 Interview One-Liners

**Q: "How did you prevent leakage?"**  
A: "Multi-layer detection: statistical tests (AUC, correlation), temporal availability audit, and point-in-time feature engineering."

**Q: "Why temporal split?"**  
A: "Random splits leak future information. Temporal split with gap period simulates real production deployment."

**Q: "How do you handle schema changes?"**  
A: "Pattern-based feature detection, graceful fallbacks for missing columns, unknown category encoding."

**Q: "Why this metric?"**  
A: "PR-AUC focuses on the rare positive class. Accuracy is useless at 3.5% fraud rate."

**Q: "Why this model?"**  
A: "LightGBM: best PR-AUC (0.42), fastest training (45s), best calibration (Brier 0.028), production-ready."

---

## 🔧 Key Code Snippets

### Temporal Split
```python
# Time-based split with gap
df_sorted = df.sort_values('TransactionDT')

train_end = df['TransactionDT'].quantile(0.60)
gap_end = df['TransactionDT'].quantile(0.70)
val_end = df['TransactionDT'].quantile(0.90)

train = df[df['TransactionDT'] < train_end]
val = df[(df['TransactionDT'] >= gap_end) & (df['TransactionDT'] < val_end)]
test = df[df['TransactionDT'] >= val_end]
```

### Leakage Detection
```python
from sklearn.metrics import roc_auc_score

for col in X.columns:
    if X[col].dtype in [np.number]:
        auc = roc_auc_score(y, X[col])
        if auc > 0.95 or auc < 0.05:
            print(f"🚨 LEAKAGE: {col} has AUC = {auc:.3f}")
```

### Schema Handling
```python
def safe_feature_extraction(df, expected_columns):
    features = {}
    
    # Handle missing columns
    for col in expected_columns:
        if col in df.columns:
            features[col] = df[col]
        else:
            features[col] = -999  # Default value
            print(f"⚠️  Column {col} missing, using default")
    
    return pd.DataFrame(features)
```

### Class Imbalance
```python
import lightgbm as lgb

# Calculate scale_pos_weight
neg_count = (y_train == 0).sum()
pos_count = (y_train == 1).sum()
scale_pos_weight = neg_count / pos_count  # ~27 for 3.5% fraud

model = lgb.LGBMClassifier(
    scale_pos_weight=scale_pos_weight,
    random_state=42
)
```

### Evaluation
```python
from sklearn.metrics import average_precision_score, matthews_corrcoef

# PR-AUC (primary metric)
pr_auc = average_precision_score(y_val, y_val_proba)

# Recall@K
k = int(len(y_val) * 0.01)  # Top 1%
sorted_idx = np.argsort(y_val_proba)[::-1][:k]
recall_at_1pct = y_val.iloc[sorted_idx].sum() / y_val.sum()

# MCC
y_val_pred = (y_val_proba >= threshold).astype(int)
mcc = matthews_corrcoef(y_val, y_val_pred)

print(f"PR-AUC: {pr_auc:.3f}")
print(f"Recall@1%: {recall_at_1pct:.2%}")
print(f"MCC: {mcc:.3f}")
```

---

## 📁 File Priority

### Must Create (P0)
1. `src/data/quality.py` - DataQualityAuditor
2. `src/validation/leakage_detector.py` - LeakageDetector
3. `src/data/splitter.py` - Temporal split logic
4. `src/features/schema_agnostic.py` - Schema-agnostic features
5. `src/inference/api.py` - FastAPI endpoint
6. `scripts/train_model.py` - Training pipeline

### Should Create (P1)
7. `src/monitoring/drift.py` - PSI, KS test
8. `src/models/calibration.py` - Probability calibration
9. `streamlit_app/app.py` - Dashboard
10. `tests/test_inference/test_schema_drift.py` - Schema tests

### Nice to Have (P2)
11. `.github/workflows/ci.yml` - CI/CD
12. `src/models/ensemble.py` - Model ensembling
13. `notebooks/06_production_simulation.ipynb` - Production tests

---

## ⏱️ Time Management

**48-Hour Breakdown:**

- **0-8h:** Foundation (data, quality, leakage detection)
- **8-24h:** Features & validation (temporal split, features, testing)
- **24-32h:** Modeling (train, compare, select)
- **32-44h:** Production (API, monitoring, MLOps)
- **44-48h:** Documentation & submission

**Critical Path:**
Data → Leakage Detection → Temporal Validation → Features → Model → Inference → Monitoring

**If Running Out of Time:**
1. Ensure P0 complete (no leakage, temporal validation, working API)
2. Skip P2 (advanced features, complex ensembles)
3. Use simple but robust approach
4. Document what you would improve

---

## 🎓 Final Words

**Remember:**
- Methodology > Metrics
- Production-ready > Leaderboard-winning
- Simple & robust > Complex & fragile
- Documentation > Experimentation

**You're building a system that:**
- Will be reviewed by senior engineers
- Must handle real-world messiness
- Needs to work tomorrow, not just today
- Must never crash

**Good luck!** 🚀

