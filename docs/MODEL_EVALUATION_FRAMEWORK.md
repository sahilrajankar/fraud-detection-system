# Model Evaluation Framework

## DO NOT Use Accuracy!

**Why accuracy is misleading for rare events:**
- 3.5% fraud rate means predicting all "not fraud" gives 96.5% accuracy
- Completely useless model looks great on accuracy
- Hides complete failure on minority class

---

## Primary Metrics (The Metrics That Actually Matter)

### 1. PR-AUC (Precision-Recall Area Under Curve)

**Why PR-AUC:**
- Focuses on the positive (fraud) class
- Not biased by class imbalance
- Shows trade-off between precision and recall across all thresholds

**Interpretation:**
- Random baseline: ~0.035 (equal to fraud rate)
- Good model: > 0.30
- Excellent model: > 0.50
- Suspicious model: > 0.80 (check for leakage!)

**Implementation:**
```python
from sklearn.metrics import average_precision_score, precision_recall_curve

pr_auc = average_precision_score(y_true, y_pred_proba)

# Plot PR curve
precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
plt.plot(recall, precision)
plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title(f'PR Curve (AUC={pr_auc:.3f})')
```

---

### 2. Recall@K (Top-K Precision)

**Business Context:**
- Fraud team can investigate N cases per day
- Want to maximize fraud catch rate in top N scored transactions

**Metric:**
```
Recall@K = (True Frauds in Top K) / (Total Frauds)
```

**Example:**
- If team can review 1000 cases/day
- Total frauds = 3500
- True frauds in top 1000 = 700
- Recall@1000 = 700/3500 = 20%

**Target:**
- Recall@1% (top 1% of scored transactions) > 30%
- Recall@5% > 60%
- Recall@10% > 80%

**Implementation:**
```python
def recall_at_k(y_true, y_pred_proba, k):
    """
    Calculate recall in top-k highest-scored predictions
    """
    # Sort by prediction probability
    sorted_idx = np.argsort(y_pred_proba)[::-1]
    
    # Get top k
    top_k_idx = sorted_idx[:k]
    
    # Count frauds in top k
    frauds_caught = y_true.iloc[top_k_idx].sum()
    total_frauds = y_true.sum()
    
    return frauds_caught / total_frauds

# Calculate for multiple k values
k_values = [100, 500, 1000, 5000]
for k in k_values:
    recall_k = recall_at_k(y_val, y_val_proba, k)
    print(f"Recall@{k}: {recall_k:.2%}")
```

---

### 3. Precision@K

**Metric:**
```
Precision@K = (True Frauds in Top K) / K
```

**Interpretation:**
- If investigating top 1000 cases, what % are actually fraud?
- High precision = fewer wasted investigations
- Trade-off with recall

**Target:**
- Precision@1000 > 30% (compared to 3.5% base rate)
- 10x lift over baseline is strong

**Implementation:**
```python
def precision_at_k(y_true, y_pred_proba, k):
    sorted_idx = np.argsort(y_pred_proba)[::-1]
    top_k_idx = sorted_idx[:k]
    return y_true.iloc[top_k_idx].sum() / k
```

---

### 4. F1 Score

**What it measures:**
- Harmonic mean of precision and recall
- Balances false positives and false negatives

**When to use:**
- When you care equally about precision and recall
- Threshold-dependent metric

**Threshold optimization:**
```python
from sklearn.metrics import f1_score

# Find optimal threshold for F1
best_f1 = 0
best_threshold = 0

for threshold in np.linspace(0.01, 0.99, 100):
    y_pred = (y_pred_proba >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred)
    
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = threshold

print(f"Best F1: {best_f1:.3f} at threshold {best_threshold:.3f}")
```

**Target:**
- F1 > 0.40 is good for 3.5% fraud rate
- F1 > 0.50 is excellent

---

### 5. Matthews Correlation Coefficient (MCC)

**Why MCC:**
- Best metric for imbalanced datasets
- Accounts for all four confusion matrix quadrants
- Range: -1 (worst) to +1 (perfect)
- 0 = random guessing

**Interpretation:**
- MCC > 0.3: Moderate
- MCC > 0.5: Good
- MCC > 0.7: Excellent
- MCC > 0.9: Suspicious (check for leakage)

**Implementation:**
```python
from sklearn.metrics import matthews_corrcoef

mcc = matthews_corrcoef(y_true, y_pred)
```

---

## Probability Calibration Metrics

### 6. Brier Score

**What it measures:**
- Mean squared error of probability predictions
- Assesses how well probabilities match actual outcomes

**Formula:**
```
Brier Score = mean((predicted_prob - actual_label)^2)
```

**Range:**
- 0 = perfect calibration
- Lower is better
- For 3.5% fraud rate, naive baseline = 0.0337

**Target:**
- Brier Score < 0.030 (better than baseline)

**Implementation:**
```python
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(y_true, y_pred_proba)
print(f"Brier Score: {brier:.4f}")
```

---

### 7. Calibration Error

**Expected Calibration Error (ECE):**
- Divides predictions into bins
- Measures difference between predicted and actual fraud rates per bin

**Example:**
- Bin 0.8-0.9: Model predicts 85% fraud on average
- Actual fraud rate in this bin: 82%
- Error for this bin: |85% - 82%| = 3%

**Perfect calibration:**
- If model says 80% probability → 80% of those cases are actually fraud

**Implementation:**
```python
def calibration_error(y_true, y_pred_proba, n_bins=10):
    """
    Calculate expected calibration error
    """
    bins = np.linspace(0, 1, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    calibration_errors = []
    bin_counts = []
    
    for i in range(n_bins):
        mask = (y_pred_proba >= bins[i]) & (y_pred_proba < bins[i+1])
        if mask.sum() > 0:
            avg_predicted = y_pred_proba[mask].mean()
            avg_actual = y_true[mask].mean()
            calibration_errors.append(abs(avg_predicted - avg_actual))
            bin_counts.append(mask.sum())
    
    # Weighted average
    ece = np.average(calibration_errors, weights=bin_counts)
    return ece

ece = calibration_error(y_val, y_val_proba)
print(f"Expected Calibration Error: {ece:.4f}")
```

---

### 8. Reliability Curve

**Visual calibration assessment:**
- Plot predicted probability vs actual fraud rate
- Perfect calibration = diagonal line

**Implementation:**
```python
from sklearn.calibration import calibration_curve

fraction_of_positives, mean_predicted_value = calibration_curve(
    y_true, y_pred_proba, n_bins=10
)

plt.plot(mean_predicted_value, fraction_of_positives, 's-')
plt.plot([0, 1], [0, 1], '--', color='gray')  # Perfect calibration
plt.xlabel('Mean Predicted Probability')
plt.ylabel('Fraction of Positives (Actual Fraud Rate)')
plt.title('Reliability Curve')
```

---

## Business Metrics

### 9. Cost Saved

**Formula:**
```
Cost Saved = (Frauds Caught * Avg Fraud Amount) - (False Alarms * Investigation Cost)
```

**Example:**
- Average fraud amount: $500
- Investigation cost: $10
- Top 1000 scored: 700 frauds (TP), 300 legit (FP)
- Cost saved = (700 * $500) - (300 * $10) = $350,000 - $3,000 = $347,000

**Implementation:**
```python
def calculate_cost_saved(y_true, y_pred, k, avg_fraud_amount=500, investigation_cost=10):
    sorted_idx = np.argsort(y_pred)[::-1][:k]
    
    tp = y_true.iloc[sorted_idx].sum()
    fp = k - tp
    
    fraud_prevented = tp * avg_fraud_amount
    investigation_cost_total = fp * investigation_cost
    
    return fraud_prevented - investigation_cost_total
```

---

### 10. Investigation Yield

**Metric:**
```
Investigation Yield = True Positives / Total Investigations
```

**Interpretation:**
- What percentage of investigated cases are actually fraud?
- Higher yield = more efficient fraud team

**Baseline:** 3.5% (random selection)
**Target:** > 30% (10x improvement)

---

### 11. Fraud Capture Rate

**Metric:**
```
Fraud Capture Rate = Frauds Caught / Total Frauds
```

**Business constraint:**
- Can only investigate K cases per day
- Want to maximize fraud capture within this constraint

**Target:**
- Capture 80% of fraud value in top 10% of scored transactions

---

## Evaluation Dashboard

### Summary Table

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| PR-AUC | 0.42 | > 0.30 | ✅ Pass |
| Recall@1% | 35% | > 30% | ✅ Pass |
| Recall@5% | 68% | > 60% | ✅ Pass |
| Precision@1000 | 38% | > 30% | ✅ Pass |
| F1 Score | 0.45 | > 0.40 | ✅ Pass |
| MCC | 0.52 | > 0.50 | ✅ Pass |
| Brier Score | 0.028 | < 0.030 | ✅ Pass |
| Calibration Error | 0.03 | < 0.05 | ✅ Pass |

### Threshold Analysis

```python
def threshold_analysis(y_true, y_pred_proba):
    """
    Analyze metrics across different thresholds
    """
    thresholds = np.linspace(0.01, 0.99, 50)
    
    results = []
    for thresh in thresholds:
        y_pred = (y_pred_proba >= thresh).astype(int)
        
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results.append({
            'threshold': thresh,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'tn': tn
        })
    
    return pd.DataFrame(results)

# Visualize
df_thresh = threshold_analysis(y_val, y_val_proba)

plt.figure(figsize=(10, 6))
plt.plot(df_thresh['threshold'], df_thresh['precision'], label='Precision')
plt.plot(df_thresh['threshold'], df_thresh['recall'], label='Recall')
plt.plot(df_thresh['threshold'], df_thresh['f1'], label='F1')
plt.xlabel('Threshold')
plt.ylabel('Score')
plt.legend()
plt.title('Metrics vs Threshold')
```

---

## Validation Strategy Comparison

### Strategy 1: Time-Series Split (RECOMMENDED)

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
    X_train_fold = X.iloc[train_idx]
    y_train_fold = y.iloc[train_idx]
    X_val_fold = X.iloc[val_idx]
    y_val_fold = y.iloc[val_idx]
    
    # Train and evaluate
    model.fit(X_train_fold, y_train_fold)
    y_pred_proba = model.predict_proba(X_val_fold)[:, 1]
    
    pr_auc = average_precision_score(y_val_fold, y_pred_proba)
    print(f"Fold {fold+1} PR-AUC: {pr_auc:.3f}")
```

**Pros:**
- Respects temporal ordering
- Simulates future deployment
- No lookahead bias

**Cons:**
- Early folds have less training data
- More computationally expensive

---

### Strategy 2: Walk-Forward Validation

```python
# Define time windows
window_size = 30  # days
step_size = 7      # days

results = []

for start_day in range(0, max_day - window_size, step_size):
    train_end = start_day + window_size
    val_end = train_end + step_size
    
    train_mask = (df['day'] >= start_day) & (df['day'] < train_end)
    val_mask = (df['day'] >= train_end) & (df['day'] < val_end)
    
    X_train = X[train_mask]
    y_train = y[train_mask]
    X_val = X[val_mask]
    y_val = y[val_mask]
    
    model.fit(X_train, y_train)
    y_pred = model.predict_proba(X_val)[:, 1]
    
    pr_auc = average_precision_score(y_val, y_pred)
    results.append({'window_start': start_day, 'pr_auc': pr_auc})
```

**Pros:**
- Most realistic simulation of production
- Detects temporal drift
- Shows performance stability over time

**Cons:**
- Very computationally expensive
- Requires sufficient data

---

## Model Comparison Framework

```python
def compare_models(models_dict, X_train, y_train, X_val, y_val):
    """
    Compare multiple models on all key metrics
    """
    results = []
    
    for model_name, model in models_dict.items():
        print(f"Training {model_name}...")
        
        # Train
        model.fit(X_train, y_train)
        
        # Predict
        y_pred_proba = model.predict_proba(X_val)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Calculate metrics
        pr_auc = average_precision_score(y_val, y_pred_proba)
        recall_1pct = recall_at_k(y_val, y_pred_proba, int(len(y_val) * 0.01))
        f1 = f1_score(y_val, y_pred)
        mcc = matthews_corrcoef(y_val, y_pred)
        brier = brier_score_loss(y_val, y_pred_proba)
        
        results.append({
            'Model': model_name,
            'PR-AUC': pr_auc,
            'Recall@1%': recall_1pct,
            'F1': f1,
            'MCC': mcc,
            'Brier': brier
        })
    
    return pd.DataFrame(results).sort_values('PR-AUC', ascending=False)

# Example usage
models = {
    'Logistic Regression': LogisticRegression(class_weight='balanced'),
    'Random Forest': RandomForestClassifier(n_estimators=100, class_weight='balanced'),
    'XGBoost': XGBClassifier(scale_pos_weight=27),  # ratio of negative to positive
    'LightGBM': LGBMClassifier(is_unbalance=True),
}

comparison_df = compare_models(models, X_train, y_train, X_val, y_val)
print(comparison_df)
```

