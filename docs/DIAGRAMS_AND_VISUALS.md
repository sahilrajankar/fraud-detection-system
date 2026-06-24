# System Diagrams & Visual Reference

## 1. Temporal Validation Strategy (CRITICAL!)

```
Timeline Visualization:
====================================================================================

                    TRAINING PERIOD              VALIDATION       GAP    TEST
                    ===============              ==========      ====   ====
                    (Historical Data)            (Recent Data)   (Wait) (Future)

Day:    0    20    40    60    80   100   110   120   130  140  150  160  170  180
        |-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
        [========== TRAIN (60%) ==========][== VAL ==][GAP][== TEST ==]
        
        
Details:
--------
TRAIN:      Days 0-108   (60%)
            - Build features from this period only
            - Point-in-time aggregations
            - NO future information

VALIDATION: Days 108-144 (20%)
            - Model tuning and selection
            - Hyperparameter optimization
            - Feature importance analysis

GAP:        Days 144-162 (10%)
            - CRITICAL: Prevents label leakage
            - Fraud discovered late (days/weeks after)
            - Without gap, "future" fraud labels leak into training

TEST:       Days 162-180 (10%)
            - Simulates production deployment
            - NEVER LOOKED AT during development
            - True unseen future evaluation


WHY THIS MATTERS:
=================
❌ Random Split:  Train ← mix of all time periods → Test
                  WRONG! Test contains "past" that model learned from

✅ Temporal Split: Train → Gap → Test
                   CORRECT! Test is truly "future"


COMMON MISTAKE:
===============
Day 100: Transaction happens
Day 105: Fraud discovered and labeled
Day 108: Training period ends

Without gap period:
- Day 105 fraud label is in training data
- But similar late-discovered frauds in validation are "unknown"
- Model learns pattern that doesn't exist at prediction time
- TEMPORAL LEAKAGE!

With gap period:
- Day 105 fraud excluded from training (in gap)
- Model only learns from fraud discovered by Day 100
- More realistic for production
```

---

## 2. Leakage Detection Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEAKAGE DETECTION PIPELINE                    │
└─────────────────────────────────────────────────────────────────┘

INPUT: Dataset with features X and target y

    │
    ▼
┌─────────────────────────────────────────────────┐
│  TEST 1: Perfect Predictor Detection           │
│  ─────────────────────────────────────────────  │
│  For each feature:                              │
│    - Train simple model on single feature       │
│    - Calculate AUC                              │
│    - Flag if AUC > 0.95                         │
│                                                  │
│  ⚠️  High AUC = Feature is too predictive       │
│      (likely contains target information)       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  TEST 2: Suspicious Correlations                │
│  ─────────────────────────────────────────────  │
│  For each feature:                              │
│    - Calculate Pearson correlation with target  │
│    - Flag if |correlation| > 0.90               │
│                                                  │
│  ⚠️  High correlation = Direct target proxy     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  TEST 3: Label Proxy Detection                  │
│  ─────────────────────────────────────────────  │
│  For low-cardinality features:                  │
│    - Train decision tree (max_depth=3)          │
│    - Check if accuracy > 95%                    │
│                                                  │
│  ⚠️  Perfect single-feature accuracy = Proxy    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  TEST 4: Temporal Availability Audit            │
│  ─────────────────────────────────────────────  │
│  For each feature:                              │
│    - Check if exists at prediction time         │
│    - Verify no lookahead bias                   │
│    - Flag aggregations using future data        │
│                                                  │
│  ⚠️  Post-event features = Temporal leakage     │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  TEST 5: Train-Test Distinguishability          │
│  ─────────────────────────────────────────────  │
│  - Train classifier: train vs test              │
│  - If AUC > 0.80: sets too different           │
│  - If AUC < 0.55: good similarity              │
│                                                  │
│  ⚠️  Very different = May not generalize        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
        LEAKAGE REPORT
        
✅ PASS: No leakage detected
⚠️  WARNING: Suspicious features found
❌ FAIL: Critical leakage detected


EXAMPLE OUTPUT:
===============

Leakage Report
--------------
✅ 430 features passed all tests
⚠️  3 features flagged as suspicious:
    - V300: AUC = 0.94 (close to threshold)
    - V127: correlation = 0.88 (high correlation)
    - id_05: 22% accuracy on single feature (moderate)

❌ 1 feature CRITICAL:
    - V999: AUC = 0.999, correlation = 0.97
    → ACTION: DROP IMMEDIATELY
```

---

## 3. Feature Engineering Pipeline (Schema-Agnostic)

```
┌─────────────────────────────────────────────────────────────────┐
│                 SCHEMA-AGNOSTIC FEATURE ENGINEERING              │
└─────────────────────────────────────────────────────────────────┘

INPUT: DataFrame (unknown columns)

    │
    ▼
┌──────────────────────────────────────────┐
│  STEP 1: Auto-Detect Column Types       │
│  ───────────────────────────────────────  │
│  Pattern matching:                       │
│  - 'id', 'key' → identifier columns      │
│  - 'amt', 'amount', 'price' → money      │
│  - 'time', 'date', 'dt' → temporal       │
│  - dtype object → categorical            │
│  - dtype numeric → numerical             │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  STEP 2: Entity Features                 │
│  ───────────────────────────────────────  │
│  For each identifier column:             │
│  - Historical transaction count          │
│  - Historical fraud rate                 │
│  - Account age                           │
│  - Average transaction amount            │
│  - Transaction velocity                  │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  STEP 3: Transaction Features            │
│  ───────────────────────────────────────  │
│  For amount columns:                     │
│  - Amount bands (bins)                   │
│  - Is round amount? (.00)                │
│  - First/last digits (Benford's law)     │
│                                           │
│  For time columns:                       │
│  - Hour of day                           │
│  - Day of week                           │
│  - Is weekend?                           │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  STEP 4: Temporal Aggregations           │
│  ───────────────────────────────────────  │
│  Rolling windows (7, 14, 30, 60 days):   │
│  - Mean transaction amount               │
│  - Std dev of amounts                    │
│  - Transaction count                     │
│  - Max/min amounts                       │
│                                           │
│  ⚠️  CRITICAL: Only past data!           │
│      (expanding or rolling, not full)    │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  STEP 5: Risk History Features           │
│  ───────────────────────────────────────  │
│  - Past fraud count                      │
│  - Days since last fraud                 │
│  - Fraud rate in last 30 days            │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  STEP 6: Behavioral Deviation            │
│  ───────────────────────────────────────  │
│  - Current amount vs user average        │
│  - Current velocity vs user average      │
│  - Population percentile                 │
└──────────────┬───────────────────────────┘
               │
               ▼
        FEATURE MATRIX
        (87 features)


ADVANTAGE:
==========
✅ Works even if columns renamed
✅ Handles missing columns gracefully
✅ No hardcoded column names
✅ Adapts to different datasets


EXAMPLE:
========
Original column: "TransactionAmt"
Renamed to:      "transaction_amount_v2"

Schema-Agnostic Approach:
- Detects 'amount' pattern in name
- Extracts as money column
- Builds same features
- ✅ STILL WORKS!

Hardcoded Approach:
- Looks for "TransactionAmt" exactly
- Column not found
- ❌ CRASHES!
```

---

## 4. Drift Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION MONITORING DASHBOARD               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  FEATURE DRIFT (PSI - Population Stability Index)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Feature: TransactionAmt                                          │
│  ┌────────────────────────────────────────────────────┐          │
│  │ PSI = 0.15  🟡 WARNING                             │          │
│  │                                                     │          │
│  │ Train Distribution    Production Distribution      │          │
│  │ ─────────────────     ──────────────────────       │          │
│  │     ████                     ████████              │          │
│  │   ████████                 ████████████            │          │
│  │ ██████████████         ████████████████████        │          │
│  │ ──────────────────────────────────────────────     │          │
│  │ 0    50   100  150   0    50   100  150  200       │          │
│  │                                                     │          │
│  │ Shift detected: Mean increased from $80 → $95      │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                   │
│  Alert Thresholds:                                                │
│  ✅ PSI < 0.1  : No action needed                                │
│  🟡 PSI 0.1-0.2: Monitor closely                                 │
│  🟠 PSI 0.2-0.3: Investigate + prepare retraining                │
│  🔴 PSI > 0.3  : CRITICAL - Retrain immediately                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  PREDICTION DISTRIBUTION                                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Fraud Rate Over Time                                             │
│  ┌────────────────────────────────────────────────────┐          │
│  │ 5%│                                    ╱            │          │
│  │   │                              ╱╲   ╱             │          │
│  │ 4%│                         ╱╲  ╱  ╲ ╱              │          │
│  │   │                    ╱╲  ╱  ╲╱    ╲               │          │
│  │ 3%│──────────────────╱──╲╱────────────╲──────       │          │
│  │   │  Baseline 3.5%                     ╲             │          │
│  │ 2%│                                      ╲            │          │
│  │   │                                       ╲           │          │
│  │ 1%│                                        ╲          │          │
│  │   └────────────────────────────────────────╲────     │          │
│  │     Week1  Week2  Week3  Week4  Week5  Week6         │          │
│  │                                                       │          │
│  │ 🔴 Anomaly detected in Week 5: 4.8% (37% above base) │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  PERFORMANCE METRICS (when labels available)                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Metric           Current   Target   Status                       │
│  ──────────────   ───────   ──────   ──────                       │
│  PR-AUC           0.38      > 0.30   ✅ PASS                      │
│  Recall@1%        31%       > 30%    ✅ PASS                      │
│  Precision@1000   33%       > 30%    ✅ PASS                      │
│  MCC              0.48      > 0.50   🟡 BORDERLINE                │
│  Brier Score      0.032     < 0.030  🟡 BORDERLINE                │
│                                                                   │
│  Trend (vs last week): ↓ -3%  🟠 DEGRADING                        │
│                                                                   │
│  Action: Schedule retraining within 7 days                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  SYSTEM HEALTH                                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  API Latency                                                      │
│  ─────────────                                                    │
│  p50:  8ms  ✅                                                    │
│  p95: 24ms  ✅                                                    │
│  p99: 45ms  ✅                                                    │
│                                                                   │
│  Error Rate: 0.03%  ✅                                            │
│                                                                   │
│  Schema Issues Today: 12                                          │
│  - Missing columns: 8  (handled gracefully)                       │
│  - Unknown categories: 4  (encoded as 'UNKNOWN')                  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Inference Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      INFERENCE REQUEST FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. REQUEST ARRIVES
   ───────────────
   POST /predict
   {
     "TransactionAmt": 150.00,
     "card1": "12345",
     "TransactionDT": 1234567,
     ...
   }
   
   │
   ▼

2. SCHEMA VALIDATION
   ─────────────────
   ✅ Check required fields exist
   ✅ Validate data types
   ✅ Check value ranges
   
   ❌ If fails → Return 400 Error
   
   │
   ▼

3. SCHEMA HANDLING
   ───────────────
   ⚠️  Missing column "card2"?
       → Use default value: -999
   
   ⚠️  Unknown category "US_Territory"?
       → Map to "UNKNOWN"
   
   ⚠️  Type mismatch (string instead of int)?
       → Try coercion → Fallback to string encoding
   
   │
   ▼

4. FEATURE ENGINEERING
   ───────────────────
   - Auto-detect column types (pattern matching)
   - Extract entity features (from database/cache)
   - Compute transaction features
   - Calculate temporal aggregations
   - Add risk history features
   
   ✅ 87 features generated
   
   │
   ▼

5. MODEL PREDICTION
   ────────────────
   - Load model from artifact store
   - Predict fraud probability
   - Calculate confidence score
   
   Raw Probability: 0.8234
   
   │
   ▼

6. CALIBRATION
   ───────────
   - Apply calibration layer
   - Adjust probability for real-world accuracy
   
   Calibrated Probability: 0.7891
   
   │
   ▼

7. RISK SCORING
   ────────────
   - Apply business rules
   - Assign risk band
   - Threshold: 0.75
   
   Risk Score: 78.91%
   Risk Band: HIGH
   
   │
   ▼

8. EXPLAINABILITY
   ──────────────
   - Generate SHAP values
   - Top contributing features
   
   Top Factors:
   - TransactionAmt: +0.15 (unusual amount)
   - Hour: +0.08 (late night)
   - card_velocity_7d: +0.12 (rapid usage)
   
   │
   ▼

9. MONITORING
   ──────────
   - Log prediction
   - Update drift metrics
   - Track performance
   
   │
   ▼

10. RESPONSE
    ────────
    {
      "risk_score": 0.7891,
      "risk_band": "HIGH",
      "confidence": 0.92,
      "explanation": {
        "top_factors": [
          {"feature": "TransactionAmt", "impact": 0.15},
          {"feature": "card_velocity_7d", "impact": 0.12},
          {"feature": "Hour", "impact": 0.08}
        ]
      },
      "metadata": {
        "model_version": "v1.2.0",
        "inference_time_ms": 8
      }
    }
```

---

## 6. Class Imbalance Visualization

```
PROBLEM: Extreme Class Imbalance (3.5% fraud)
==============================================

Dataset Distribution:
────────────────────

    Legitimate (96.5%)           Fraud (3.5%)
    ══════════════════           ════
    
    ████████████████             ██
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    ████████████████
    

WHY ACCURACY IS USELESS:
════════════════════════

Model that predicts EVERYTHING as "not fraud":
- Accuracy: 96.5%  ← Looks great!
- Recall: 0%       ← Catches NO fraud!
- Useless for business


SOLUTION: Use the Right Metrics
════════════════════════════════

PR-AUC (Precision-Recall):
─────────────────────────
Focus on positive class only
Range: 0.035 (random) to 1.0 (perfect)
Target: > 0.30 (good for 3.5% rate)

Recall@K:
────────
Of top K highest-scored, what % of fraud did we catch?
Example: Recall@1% = 35% means we caught 35% of fraud
         in the top 1% of scored transactions

Precision@K:
───────────
Of top K highest-scored, what % are actually fraud?
Example: Precision@1000 = 38% means 380 out of 1000
         flagged cases are real fraud (vs 35 expected by chance)


HANDLING STRATEGIES:
═══════════════════

1. Class Weighting:
   ─────────────
   weight_positive = 27 (ratio of negative to positive)
   Model penalizes false negatives 27x more
   
2. Threshold Optimization:
   ──────────────────────
   Don't use 0.5 default!
   Optimize for business metric (cost, recall target)
   Example: threshold = 0.15 might be optimal
   
3. Cost-Sensitive Learning:
   ───────────────────────
   False Negative Cost: $500 (fraud not caught)
   False Positive Cost: $10 (investigation)
   Optimize for total cost


EVALUATION:
══════════

           Predicted
           NEG   POS
         ┌─────┬─────┐
Actual N │ TN  │ FP  │  ← Customer friction
         ├─────┼─────┤
Actual P │ FN  │ TP  │  ← Money lost
         └─────┴─────┘

Focus on bottom-right quadrant (True Positives)!
```

---

## 7. Model Comparison Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                      MODEL COMPARISON                            │
└─────────────────────────────────────────────────────────────────┘

Model             PR-AUC  Recall@1%  F1    MCC   Brier  Train_Time
─────────────     ──────  ─────────  ────  ────  ─────  ──────────
Logistic Reg      0.32    28%        0.38  0.44  0.029  5s        ✅ Fast
Random Forest     0.38    32%        0.42  0.48  0.031  720s      ❌ Slow
XGBoost           0.41    35%        0.44  0.51  0.033  180s      ⚠️  Medium
LightGBM          0.42    35%        0.45  0.52  0.028  45s       ✅✅ BEST
CatBoost          0.41    34%        0.44  0.51  0.029  240s      ⚠️  Medium


SELECTION CRITERIA:
══════════════════

Performance:       LightGBM (PR-AUC 0.42) ✅
Calibration:       LightGBM (Brier 0.028) ✅
Training Speed:    LightGBM (45s) ✅
Inference Speed:   LightGBM (8ms) ✅
Robustness:        LightGBM (handles missing) ✅
Explainability:    LightGBM (SHAP support) ✅

WINNER: LightGBM 🏆
─────────────────

Pros:
  ✅ Best overall performance
  ✅ Fastest training among tree models
  ✅ Best calibration
  ✅ Native missing value handling
  ✅ Direct categorical encoding
  ✅ Production-ready

Cons:
  ⚠️  Less interpretable than logistic regression
  ⚠️  More complex than simple baselines

Recommendation:
  PRIMARY: LightGBM
  BACKUP: Logistic Regression (for explainability)
  ENSEMBLE: Consider LightGBM + XGBoost + Logistic (if time)
```

---

**These diagrams summarize the critical concepts.**  
**Refer back when implementing or during interviews.**

