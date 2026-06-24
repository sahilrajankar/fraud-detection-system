# Risk Register - Production Risk Scoring System

**Last Updated:** June 24, 2026  
**Owner:** ML Engineering Team  
**Review Cycle:** Weekly during development

---

## Critical Risks (Showstoppers)

### R-CRIT-001: Data Leakage
**Impact:** CRITICAL | **Probability:** HIGH | **Status:** 🔴 Active Monitoring

**Description:**  
Target variable information leaking into features through:
- Post-event variables
- Aggregations computed on full dataset including test
- Label proxies in disguised form

**Detection Strategy:**
1. Statistical correlation analysis (> 0.95 threshold)
2. Single-feature AUC testing (> 0.95 = suspicious)
3. Perfect predictor detection
4. Temporal availability audit for each feature
5. Cross-validation with deliberate label shuffling (should drop performance)

**Mitigation:**
- Implement automated LeakageDetector class
- Manual review of all aggregated features
- Point-in-time feature engineering only
- Feature availability timestamp documentation
- Pre-commit hooks to run leakage tests

**Validation:**
- [ ] All features pass correlation test (< 0.90)
- [ ] No single feature achieves AUC > 0.90
- [ ] Temporal audit shows all features available at prediction time
- [ ] Label-shuffled validation shows expected performance drop

---

### R-CRIT-002: Temporal Leakage (Lookahead Bias)
**Impact:** CRITICAL | **Probability:** HIGH | **Status:** 🔴 Active Monitoring

**Description:**  
Model trained on future information not available at prediction time:
- Features using data from after transaction timestamp
- Aggregations including future rows
- Incorrect train/test split allowing data bleeding

**Detection Strategy:**
1. Walk-forward validation performance check
2. Time-sorted splits only
3. Feature availability timeline documentation
4. Rolling window validation
5. Performance degradation from validation to test (should be minimal if no leakage)

**Mitigation:**
- NEVER use random train/test split
- Implement strict temporal cutoffs
- Use only expanding/rolling windows for aggregations
- Feature engineering pipeline enforces time-awareness
- Gap period between train and test (minimum 2 weeks)

**Validation:**
- [ ] All splits are strictly temporal
- [ ] Gap period implemented (min 14 days)
- [ ] Walk-forward validation implemented
- [ ] No future data in feature engineering verified
- [ ] Performance stable across time periods

---

### R-CRIT-003: Schema Drift Crashes
**Impact:** CRITICAL | **Probability:** MEDIUM | **Status:** 🟡 Mitigation Active

**Description:**  
Production inference fails when:
- Expected columns are missing
- New categorical values appear
- Data types change
- Column names are renamed

**Detection Strategy:**
1. Schema validation at inference entry point
2. Column existence checks before feature engineering
3. Unknown category detection
4. Type mismatch detection
5. Integration tests with schema variations

**Mitigation:**
- Schema-agnostic feature engineering (pattern-based column detection)
- Graceful fallback for missing columns (use defaults)
- Unknown category handling in all encoders
- Try-except blocks with logging
- Feature importance-based degradation (drop low-importance features first)

**Validation:**
- [ ] API handles missing columns without crash
- [ ] Unknown categories encoded correctly
- [ ] Type mismatches handled gracefully
- [ ] 50 test cases with schema variations pass
- [ ] Logging captures all schema issues

---

### R-CRIT-004: Validation Set Overfitting
**Impact:** HIGH | **Probability:** MEDIUM | **Status:** 🟡 Mitigation Active

**Description:**  
Excessive hyperparameter tuning on validation set causes:
- Model memorizes validation patterns
- Poor generalization to truly unseen test data
- Optimistic performance estimates

**Detection Strategy:**
1. Track validation score changes across tuning iterations
2. Multiple independent validation sets
3. Walk-forward validation
4. Final blind holdout set (never touched until end)
5. Validation-test performance gap monitoring

**Mitigation:**
- Limit hyperparameter search iterations (max 50)
- Use early stopping
- Prefer simpler models
- Multiple validation periods (not just one)
- Final holdout set never used for tuning
- Bayesian optimization instead of grid search (more efficient)

**Validation:**
- [ ] Max 50 hyperparameter configurations tested
- [ ] Walk-forward validation shows consistent performance
- [ ] Holdout performance within 5% of validation
- [ ] No suspicious perfect scores

---

## High Risks

### R-HIGH-001: Extreme Class Imbalance
**Impact:** HIGH | **Probability:** CERTAIN | **Status:** 🟢 Mitigated

**Description:**  
3.5% fraud rate leads to:
- Models predicting all negative
- Poor minority class recall
- Misleading accuracy metrics

**Mitigation:**
- Class-weighted loss functions
- Stratified sampling in all splits
- Threshold optimization for business metrics
- PR-AUC instead of ROC-AUC
- Focal loss for hard examples

**Validation:**
- [ ] Stratified splits implemented
- [ ] Class weights applied
- [ ] Recall@K > 60%
- [ ] PR-AUC > 0.30

---

### R-HIGH-002: Temporal/Concept Drift
**Impact:** HIGH | **Probability:** HIGH | **Status:** 🟡 Monitoring Required

**Description:**  
Fraud patterns evolve:
- New fraud tactics emerge
- Seasonal patterns change
- Economic conditions shift
- Feature distributions drift

**Detection:**
- PSI monitoring on all features
- KS test on predictions
- Performance degradation alerts
- Rolling window evaluation

**Mitigation:**
- Drift detection dashboard
- Retraining triggers (PSI > 0.2)
- Model versioning
- Ensemble of models from different time periods
- Regularization to prevent overfitting to specific patterns

**Validation:**
- [ ] PSI calculated for all features
- [ ] Retraining threshold defined
- [ ] Model versioning system in place
- [ ] Alert system configured

---

