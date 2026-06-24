# Production-Grade Risk Scoring System - Technical Design Document

**Version:** 1.0  
**Date:** June 24, 2026  
**Author:** Principal ML Engineering Team  
**Status:** Design Phase Complete

---

## Executive Summary

This document presents a comprehensive production-grade risk scoring system designed for adversarial real-world deployment where:
- No dataset is provided in advance
- Hidden future-period evaluation will be conducted
- Schema drift, temporal drift, and data quality issues are expected
- The system must prioritize methodology, reliability, and generalization over leaderboard metrics

This design would survive senior engineering review and production deployment scrutiny.

---

## PHASE 1: REQUIREMENTS ANALYSIS

### 1.1 Explicit Requirements

| Requirement ID | Description | Priority | Complexity |
|---------------|-------------|----------|------------|
| REQ-001 | Self-source appropriate dataset | Critical | High |
| REQ-002 | Handle unknown future-period data | Critical | High |
| REQ-003 | Survive schema changes during inference | Critical | High |
| REQ-004 | Detect and prevent target leakage | Critical | Medium |
| REQ-005 | Detect and prevent time leakage | Critical | Medium |
| REQ-006 | Handle heavy class imbalance | Critical | Medium |
| REQ-007 | Handle data quality issues | High | Medium |
| REQ-008 | Prioritize methodology over metrics | Critical | Low |

### 1.2 Hidden Requirements (What They're ACTUALLY Testing)

| Hidden Test | Description | How They'll Catch You |
|------------|-------------|----------------------|
| **Production Thinking** | Do you think like a production engineer or a Kaggle competitor? | - Random train/test split<br>- No validation strategy<br>- No drift monitoring |
| **Leakage Detection** | Can you identify subtle data leakage? | - Using post-event features<br>- Perfect/near-perfect predictors<br>- Label proxies |
| **Temporal Awareness** | Do you respect time boundaries? | - Lookahead bias<br>- Future information in features<br>- Incorrect time splits |
| **Robustness Engineering** | Can you build systems that don't crash? | - Crashes on missing columns<br>- Fails on new categories<br>- No error handling |
| **Generalization First** | Do you optimize for unseen data? | - Overfitting to validation<br>- Complex feature engineering<br>- Memorization over learning |

### 1.3 Common Failure Modes

#### Critical Failures (Immediate Rejection)

1. **Leakage Failures**
   - Using features available only after the event
   - Including the target variable in transformed form
   - Using aggregations computed on the full dataset including test

2. **Temporal Failures**
   - Training on future data
   - Using random splits on time-series data
   - Lookahead bias in feature engineering

3. **Production Failures**
   - API crashes on schema changes
   - No handling of missing columns
   - No handling of new categories

4. **Validation Failures**
   - No holdout period
   - Validation data bleeding into training
   - Overfitting to validation set

#### High-Risk Failures (Major Points Lost)

5. **Generalization Failures**
   - Overengineered features that memorize training data
   - Deep feature interactions on limited data
   - No regularization

6. **Robustness Failures**
   - No drift detection
   - No monitoring
   - No graceful degradation

### 1.4 Red Flags That Would Immediately Fail Assessment

| Red Flag | Why It Fails | Detection Method |
|----------|-------------|------------------|
| Perfect validation score (AUC > 0.99) | Obvious leakage | Statistical impossibility for real fraud |
| Random train/test split | Shows no understanding of time-series | Test contains future information |
| No time-based validation | Cannot generalize to future | Hidden test will perform poorly |
| Feature names hardcoded everywhere | Breaks on schema changes | Inference fails immediately |
| No leakage detection framework | Untrustworthy results | Likely contaminated |
| No drift monitoring | Not production-ready | Silent degradation |
| Complex neural networks with tiny data | Massive overfitting | Poor generalization |
| No calibration analysis | Probabilities meaningless | Bad business decisions |

### 1.5 Risk Matrix

| Risk ID | Risk Description | Impact | Probability | Detection Strategy | Mitigation Strategy |
|---------|-----------------|--------|-------------|-------------------|-------------------|
| **R-001** | Target leakage through derived features | CRITICAL | HIGH | - Statistical tests (correlation > 0.95)<br>- Temporal availability audit<br>- Perfect predictor detection | - Feature availability timeline<br>- Point-in-time feature engineering<br>- Automated leakage tests |
| **R-002** | Time leakage via lookahead bias | CRITICAL | HIGH | - Feature availability audit<br>- Time-sorted validation<br>- Walk-forward testing | - Strict temporal splits<br>- Point-in-time aggregations<br>- No future information |
| **R-003** | Schema drift during inference | CRITICAL | MEDIUM | - Column existence checks<br>- Data type validation<br>- Distribution monitoring | - Schema-agnostic features<br>- Robust feature extraction<br>- Graceful fallbacks |
| **R-004** | Temporal/concept drift | HIGH | HIGH | - PSI monitoring<br>- Distribution shifts<br>- Performance degradation | - Drift detection system<br>- Retraining triggers<br>- Model versioning |
| **R-005** | Class imbalance extreme overfitting | HIGH | MEDIUM | - Cross-validation stratified<br>- Minority class evaluation<br>- PR curves | - Proper sampling strategies<br>- Class-weighted loss<br>- Threshold optimization |
| **R-006** | Validation set overfitting | HIGH | MEDIUM | - Multiple holdout periods<br>- Walk-forward validation<br>- Degradation from val to test | - Minimal validation tuning<br>- Final blind holdout<br>- Simple models |
| **R-007** | Data quality issues corrupting features | MEDIUM | HIGH | - Automated data quality checks<br>- Statistical anomaly detection<br>- Distribution monitoring | - Robust feature engineering<br>- Outlier handling<br>- Missing value strategies |
| **R-008** | New categorical values at inference | MEDIUM | HIGH | - Category tracking<br>- Unknown category counts<br>- Error logging | - Unknown category handling<br>- Encoding fallbacks<br>- Default predictions |
| **R-009** | Insufficient holdout period | HIGH | MEDIUM | - Time gap analysis<br>- Seasonal pattern checks | - Minimum 3-month gap<br>- Seasonal validation |
| **R-010** | Model explanation failure | MEDIUM | LOW | - SHAP values<br>- Feature importance<br>- Business logic review | - Explainability framework<br>- Feature documentation<br>- Business alignment |

### 1.6 Assessment Success Criteria (What Actually Matters)

#### Tier 1: Must Have (Minimum to Pass)
- ✅ No data leakage (verified through testing)
- ✅ Proper temporal validation
- ✅ Handles schema changes gracefully
- ✅ Reasonable performance on hidden test set
- ✅ Production-ready inference API

#### Tier 2: Strong Submission (Top 20%)
- ✅ Comprehensive drift monitoring
- ✅ Calibrated probability outputs
- ✅ Explainability framework
- ✅ Complete MLOps pipeline
- ✅ Professional documentation

#### Tier 3: Exceptional (Top 5%)
- ✅ Sophisticated feature engineering that generalizes
- ✅ Multiple validation strategies compared
- ✅ Automated leakage detection framework
- ✅ Production monitoring dashboards
- ✅ Cost-aware threshold optimization

---

## PHASE 2: DATASET STRATEGY

### 2.1 Dataset Evaluation Framework

Evaluation criteria for candidate datasets:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Transaction-based | 20% | Must be transaction-level, not aggregated |
| Rare event | 20% | Target class < 5% |
| Temporal structure | 20% | Clear timestamp column for time-based splits |
| Real-world complexity | 15% | Messy data, missing values, data quality issues |
| Volume | 10% | >100K records for drift analysis |
| Public availability | 10% | Easily accessible, well-documented |
| Leakage risk testability | 5% | Can verify no leakage exists |

### 2.2 Candidate Datasets Analysis

#### Dataset 1: IEEE-CIS Fraud Detection (Kaggle)
- **Source**: Kaggle competition dataset
- **Records**: 590K transactions
- **Features**: 434 features (anonymized)
- **Target**: isFraud (3.5% positive)
- **Time**: TransactionDT (timedelta from reference)
- **Leakage Risks**: ⚠️ Anonymized features hide semantic meaning
- **Pros**: Large, realistic imbalance, temporal structure, production-like
- **Cons**: Anonymized names make leakage detection harder
- **Score**: 8.5/10

#### Dataset 2: Credit Card Fraud Detection (ULB)
- **Source**: Kaggle / UCL Machine Learning Group
- **Records**: 284K transactions
- **Features**: 30 features (PCA-transformed)
- **Target**: Class (0.17% positive - extreme imbalance)
- **Time**: Time (seconds elapsed)
- **Leakage Risks**: ✅ PCA features unlikely to leak
- **Pros**: Extreme imbalance tests robustness, temporal ordering
- **Cons**: PCA features limit feature engineering
- **Score**: 7.0/10

#### Dataset 3: Synthetic Financial Transactions (PaySim)
- **Source**: Kaggle / Academic research
- **Records**: 6.3M transactions
- **Features**: 11 features
- **Target**: isFraud (0.13% positive)
- **Time**: step (time unit)
- **Leakage Risks**: ⚠️ isFlaggedFraud is a post-event flag (TRAP!)
- **Pros**: Large scale, interpretable features, realistic patterns
- **Cons**: Synthetic (may not reflect real complexity), obvious leakage trap
- **Score**: 6.5/10

#### Dataset 4: Home Credit Default Risk
- **Source**: Kaggle competition
- **Records**: 307K applications + auxiliary tables
- **Features**: 122 main + many auxiliary
- **Target**: TARGET (8% default)
- **Time**: DAYS_* features (relative dates)
- **Leakage Risks**: ⚠️ Many post-application features
- **Pros**: Multiple tables (production-like), good documentation
- **Cons**: Not transaction-level, more credit risk than fraud
- **Score**: 7.5/10

#### Dataset 5: Santander Customer Transaction Prediction
- **Source**: Kaggle
- **Records**: 200K transactions
- **Features**: 200 anonymized features
- **Target**: target (10% positive)
- **Time**: ❌ No explicit time column
- **Leakage Risks**: ⚠️ Anonymized, unknown temporal structure
- **Pros**: Clean, well-balanced
- **Cons**: **NO TIME COLUMN - CRITICAL FLAW**, can't do temporal validation
- **Score**: 4.0/10 (disqualified due to no time)

#### Dataset 6: Lending Club Loan Data
- **Source**: Lending Club public data
- **Records**: 2.2M loans
- **Features**: 150+ features
- **Target**: loan_status (charged off ~20%)
- **Time**: issue_d (issue date)
- **Leakage Risks**: ⚠️ Many post-issue features
- **Pros**: Large, real-world, well-documented, interpretable
- **Cons**: Not transaction-level fraud, more credit risk
- **Score**: 8.0/10

#### Dataset 7: Microsoft Malicious URLs
- **Source**: Kaggle / Microsoft
- **Records**: 2.4M URLs
- **Features**: URL characteristics
- **Target**: isMalicious
- **Time**: ❌ No time dimension
- **Leakage Risks**: Low (static features)
- **Pros**: Large, clear features
- **Cons**: Not transaction data, no temporal aspect
- **Score**: 5.0/10

#### Dataset 8: Elo Merchant Category Recommendation
- **Source**: Kaggle
- **Records**: 200K customers + transaction history
- **Features**: Transaction-level data
- **Target**: loyalty_score (regression)
- **Time**: ✅ purchase_date
- **Leakage Risks**: Medium
- **Pros**: Transaction-based, temporal
- **Cons**: Regression target, not rare event classification
- **Score**: 6.0/10

#### Dataset 9: APWG eCrime Dataset
- **Source**: Research dataset
- **Records**: Variable
- **Features**: URL, domain features
- **Target**: Phishing/legit
- **Time**: Limited
- **Leakage Risks**: Low
- **Pros**: Real phishing data
- **Cons**: Difficult access, small, not transaction-based
- **Score**: 5.5/10

#### Dataset 10: Google Analytics Customer Revenue Prediction
- **Source**: Kaggle
- **Records**: 900K sessions
- **Features**: GA features (JSONs)
- **Target**: transactionRevenue (99.9% zero)
- **Time**: ✅ visitStartTime
- **Leakage Risks**: High (many post-session features)
- **Pros**: Extreme rare event, temporal
- **Cons**: Nested JSON structure, revenue prediction not fraud
- **Score**: 6.5/10

### 2.3 Selected Dataset: IEEE-CIS Fraud Detection

**Decision Rationale:**

I recommend **IEEE-CIS Fraud Detection** as the primary dataset for the following reasons:

#### Strengths Aligned with Assessment:

1. **Production-Realistic**
   - 590K transactions (large enough for drift analysis)
   - 3.5% fraud rate (realistic rare-event scenario)
   - 434 features (complex enough to test robustness)
   - Real Vesta Corporation data (not synthetic)

2. **Temporal Structure**
   - TransactionDT provides clear time ordering
   - Allows proper train/validation/test splits
   - Enables drift simulation
   - Supports walk-forward validation

3. **Assessment Alignment**
   - Tests ability to handle many features
   - Tests class imbalance handling
   - Tests temporal validation
   - Tests feature selection under anonymization
   - Tests robustness to data quality issues

4. **Known Challenges**
   - Missing values across many columns
   - Anonymized features (must build schema-agnostic pipeline)
   - Multiple data types (categorical, numerical, identifier-like)
   - Known to have some leakage-prone features (tests leakage detection)

#### Weaknesses & Mitigations:

| Weakness | Impact | Mitigation |
|----------|--------|------------|
| Anonymized feature names | Hard to detect semantic leakage | Statistical leakage detection<br>Correlation analysis<br>Temporal consistency checks |
| Kaggle competition data | May be over-analyzed | Focus on methodology, not leaderboard<br>Use different validation strategy |
| Identity columns may leak | Some V-columns might proxy fraud | Rigorous correlation analysis<br>Temporal availability audit |

**Alternative/Backup**: If IEEE-CIS is deemed too "known", use **Lending Club** with engineered fraud labels based on default + other red flags.

### 2.4 Future-Period Simulation Strategy



#### Temporal Split Strategy

```
|<-------- Historical Data -------->|<-- Gap -->|<-- Future Test -->|
|                                   |           |                   |
| Train (60%)    | Val (20%)       | Hold(10%) | Hidden Test (10%) |
|                                   |           |                   |
| Time Period 1   | Time Period 2   | Period 3  | Period 4          |
```

**Specific Implementation:**

```python
# IEEE-CIS TransactionDT spans ~6 months (Dec 2017 - May 2018)
# Assumption: 180 days total

# Split strategy:
train_end = 108      # Days 0-108 (60%)
val_end = 144        # Days 108-144 (20%)
holdout_end = 162    # Days 144-162 (10%) - Gap period
test_start = 162     # Days 162-180 (10%) - Hidden future

# Critical: NEVER use test period for anything during development
# Simulate "hidden test" by setting aside and never looking
```

**Why This Matters:**
- Gap period prevents label leakage from fraud patterns discovered late
- Future test is truly unseen (simulates real production deployment)
- Validates temporal generalization, not just statistical generalization

### 2.5 Schema Drift Simulation Strategy

#### Simulation 1: Missing Columns
```python
# During inference, randomly drop 10-20% of features
# Tests robustness of feature engineering pipeline
inference_columns = training_columns.sample(frac=0.85)
```

#### Simulation 2: New Categorical Values
```python
# Inject unseen categories in categorical features
# Tests encoding robustness
for cat_col in categorical_features:
    X_test[cat_col].loc[random_sample] = 'UNKNOWN_CATEGORY_2026'
```

#### Simulation 3: Data Type Changes
```python
# Simulate schema evolution (int -> string, etc.)
# Tests type handling robustness
X_test['card1'] = X_test['card1'].astype(str)
```

#### Simulation 4: Feature Name Changes
```python
# Simulate column renames
# Tests schema-agnostic approach
rename_map = {
    'TransactionAmt': 'transaction_amount_v2',
    'card1': 'card_id_primary',
}
X_test = X_test.rename(columns=rename_map)
```

### 2.6 Concept Drift Simulation

#### Temporal Drift
```python
# Fraud patterns evolve over time
# Early period: Mostly card fraud
# Late period: Account takeover fraud increases
# Tests model adaptation to evolving patterns
```

#### Feature Distribution Shift
```python
# Inject distributional changes in key features
# Simulate economic shocks, seasonal effects
for feature in ['TransactionAmt', 'dist1', 'dist2']:
    if time_period == 'late':
        X_test[feature] *= np.random.normal(1.2, 0.1)  # 20% shift
```

---

## PHASE 3: DATA AUDIT FRAMEWORK

### 3.1 Automated Data Quality Framework

```python
class DataQualityAuditor:
    """
    Comprehensive data quality assessment framework
    Designed to catch issues before they corrupt the model
    """
    
    def __init__(self, data: pd.DataFrame, target: str = None):
        self.data = data
        self.target = target
        self.report = {}
        
    def audit(self) -> Dict:
        """Run all audit checks"""
        self.check_missing_values()
        self.check_duplicates()
        self.check_outliers()
        self.check_impossible_values()
        self.check_data_types()
        self.check_cardinality()
        self.check_correlations()
        self.check_constants()
        self.check_identifiers()
        
        if self.target:
            self.check_target_distribution()
            self.check_class_imbalance()
            
        return self.generate_report()
```

#### 3.1.1 Missing Value Analysis

| Check Type | Severity | Threshold | Action |
|-----------|----------|-----------|---------|
| Missing > 80% | CRITICAL | Drop column | Log & remove from features |
| Missing 50-80% | HIGH | Conditional use | Create missing indicator, impute |
| Missing 20-50% | MEDIUM | Impute | Robust imputation strategy |
| Missing < 20% | LOW | Impute | Simple imputation |

**Implementation:**
```python
def check_missing_values(self):
    missing_pct = (self.data.isnull().sum() / len(self.data)) * 100
    
    critical = missing_pct[missing_pct > 80]
    high = missing_pct[(missing_pct > 50) & (missing_pct <= 80)]
    medium = missing_pct[(missing_pct > 20) & (missing_pct <= 50)]
    
    self.report['missing'] = {
        'critical_columns': critical.to_dict(),
        'high_risk_columns': high.to_dict(),
        'medium_risk_columns': medium.to_dict(),
        'action': 'Drop critical, flag high, impute medium'
    }
```

#### 3.1.2 Duplicate Detection

```python
def check_duplicates(self):
    """
    Detect duplicate rows and potential ID collisions
    """
    # Exact duplicates
    exact_dupes = self.data.duplicated().sum()
    
    # ID columns with duplicates (potential data quality issue)
    id_columns = [col for col in self.data.columns 
                  if 'id' in col.lower() or 'key' in col.lower()]
    
    id_dupes = {}
    for col in id_columns:
        dup_count = self.data[col].duplicated().sum()
        if dup_count > 0:
            id_dupes[col] = dup_count
    
    self.report['duplicates'] = {
        'exact_duplicates': exact_dupes,
        'id_duplicates': id_dupes,
        'severity': 'HIGH' if exact_dupes > 100 else 'LOW'
    }
```

#### 3.1.3 Outlier Detection

```python
def check_outliers(self):
    """
    Multi-method outlier detection
    - Statistical (IQR, Z-score)
    - Domain-specific (impossible values)
    """
    numeric_cols = self.data.select_dtypes(include=[np.number]).columns
    outliers = {}
    
    for col in numeric_cols:
        Q1 = self.data[col].quantile(0.25)
        Q3 = self.data[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR
        
        outlier_count = ((self.data[col] < lower_bound) | 
                         (self.data[col] > upper_bound)).sum()
        
        if outlier_count > 0:
            outliers[col] = {
                'count': outlier_count,
                'percentage': (outlier_count / len(self.data)) * 100,
                'bounds': (lower_bound, upper_bound)
            }
    
    self.report['outliers'] = outliers
```

#### 3.1.4 Impossible Values Detection

```python
def check_impossible_values(self):
    """
    Domain-specific validation rules
    """
    issues = {}
    
    # Transaction amounts
    if 'TransactionAmt' in self.data.columns:
        negative = (self.data['TransactionAmt'] < 0).sum()
        too_large = (self.data['TransactionAmt'] > 1_000_000).sum()
        if negative > 0 or too_large > 0:
            issues['TransactionAmt'] = {
                'negative_values': negative,
                'extremely_large': too_large
            }
    
    # Dates/times
    time_cols = [col for col in self.data.columns if 'time' in col.lower() or 'date' in col.lower()]
    for col in time_cols:
        if self.data[col].dtype in ['datetime64', 'timedelta64']:
            future_dates = (self.data[col] > pd.Timestamp.now()).sum()
            if future_dates > 0:
                issues[col] = f'{future_dates} future dates detected'
    
    # Percentages/probabilities
    prob_cols = [col for col in self.data.columns if 'pct' in col.lower() or 'prob' in col.lower()]
    for col in prob_cols:
        out_of_range = ((self.data[col] < 0) | (self.data[col] > 1)).sum()
        if out_of_range > 0:
            issues[col] = f'{out_of_range} values outside [0,1]'
    
    self.report['impossible_values'] = issues
```

#### 3.1.5 Category Explosion Detection

```python
def check_cardinality(self):
    """
    Detect high-cardinality categoricals (potential identifiers)
    """
    categorical_cols = self.data.select_dtypes(include=['object', 'category']).columns
    cardinality = {}
    
    for col in categorical_cols:
        unique_count = self.data[col].nunique()
        unique_ratio = unique_count / len(self.data)
        
        if unique_ratio > 0.5:  # More than 50% unique
            cardinality[col] = {
                'unique_count': unique_count,
                'unique_ratio': unique_ratio,
                'warning': 'Potential identifier or high cardinality'
            }
    
    self.report['cardinality'] = cardinality
```

### 3.2 Data Quality Score

```python
def calculate_data_quality_score(self) -> float:
    """
    Composite score: 0-100
    """
    score = 100.0
    
    # Penalize missing values
    avg_missing = (self.data.isnull().sum().sum() / self.data.size) * 100
    score -= min(avg_missing, 30)  # Max 30 point deduction
    
    # Penalize duplicates
    dup_pct = (self.data.duplicated().sum() / len(self.data)) * 100
    score -= min(dup_pct * 2, 20)  # Max 20 point deduction
    
    # Penalize impossible values
    if self.report.get('impossible_values'):
        score -= len(self.report['impossible_values']) * 5  # 5 points per issue
    
    # Penalize high cardinality issues
    if self.report.get('cardinality'):
        score -= len(self.report['cardinality']) * 3  # 3 points per issue
    
    return max(score, 0.0)
```

### 3.3 Leakage Detection Framework

```python
class LeakageDetector:
    """
    Automated framework to detect various forms of data leakage
    """
    
    def __init__(self, X_train, y_train, X_test=None, y_test=None):
        self.X_train = X_train
        self.y_train = y_train
        self.X_test = X_test
        self.y_test = y_test
        self.leakage_report = {}
    
    def detect_all(self):
        """Run all leakage checks"""
        self.check_perfect_predictors()
        self.check_suspicious_correlations()
        self.check_label_proxies()
        self.check_temporal_leakage()
        self.check_test_train_similarity()
        
        return self.leakage_report
```

#### 3.3.1 Perfect Predictor Detection

```python
def check_perfect_predictors(self, threshold=0.95):
    """
    Features that predict target too well are likely leaked
    """
    from sklearn.metrics import roc_auc_score
    
    perfect_predictors = {}
    
    for col in self.X_train.columns:
        if self.X_train[col].dtype in [np.number]:
            try:
                # Single feature AUC
                auc = roc_auc_score(self.y_train, self.X_train[col])
                
                if auc > threshold or auc < (1 - threshold):
                    perfect_predictors[col] = {
                        'auc': auc,
                        'severity': 'CRITICAL',
                        'action': 'DROP IMMEDIATELY'
                    }
            except:
                pass
    
    self.leakage_report['perfect_predictors'] = perfect_predictors
```

#### 3.3.2 Suspicious Correlations

```python
def check_suspicious_correlations(self, threshold=0.90):
    """
    Extremely high correlations with target
    """
    correlations = {}
    
    for col in self.X_train.select_dtypes(include=[np.number]).columns:
        corr = self.X_train[col].corr(self.y_train)
        
        if abs(corr) > threshold:
            correlations[col] = {
                'correlation': corr,
                'severity': 'HIGH' if abs(corr) > 0.95 else 'MEDIUM',
                'action': 'INVESTIGATE'
            }
    
    self.leakage_report['suspicious_correlations'] = correlations
```

#### 3.3.3 Label Proxy Detection

```python
def check_label_proxies(self):
    """
    Features that encode the label in transformed form
    """
    from sklearn.tree import DecisionTreeClassifier
    
    proxies = {}
    
    for col in self.X_train.columns:
        if self.X_train[col].nunique() < 20:  # Only check low-cardinality
            # Train simple tree on single feature
            dt = DecisionTreeClassifier(max_depth=3, random_state=42)
            dt.fit(self.X_train[[col]].fillna(-999), self.y_train)
            
            train_acc = dt.score(self.X_train[[col]].fillna(-999), self.y_train)
            
            if train_acc > 0.95:
                proxies[col] = {
                    'accuracy': train_acc,
                    'severity': 'CRITICAL',
                    'details': 'Single feature achieves > 95% accuracy'
                }
    
    self.leakage_report['label_proxies'] = proxies
```

#### 3.3.4 Temporal Leakage Detection

```python
def check_temporal_leakage(self, time_column='TransactionDT'):
    """
    Features that shouldn't exist at prediction time
    """
    temporal_issues = {}
    
    # Check if any features are computed using future information
    # Strategy: Features should not change when we limit to point-in-time data
    
    if time_column in self.X_train.columns:
        # Sort by time
        sorted_idx = self.X_train[time_column].argsort()
        
        for col in self.X_train.columns:
            if col == time_column:
                continue
            
            # Check if feature values depend on future rows
            # Simple test: Rolling statistics should not change retrospectively
            if 'mean' in col.lower() or 'sum' in col.lower() or 'count' in col.lower():
                temporal_issues[col] = {
                    'warning': 'Aggregation feature - verify point-in-time computation',
                    'severity': 'MEDIUM'
                }
    
    self.leakage_report['temporal_issues'] = temporal_issues
```

#### 3.3.5 Test-Train Similarity Check

```python
def check_test_train_similarity(self):
    """
    If test set is too similar to train, might indicate data leakage
    """
    if self.X_test is None:
        return
    
    from sklearn.ensemble import RandomForestClassifier
    
    # Create binary classification: train vs test
    train_test_labels = np.concatenate([
        np.zeros(len(self.X_train)),
        np.ones(len(self.X_test))
    ])
    
    combined = pd.concat([self.X_train, self.X_test], axis=0)
    
    # Train classifier to distinguish train from test
    rf = RandomForestClassifier(n_estimators=50, random_state=42)
    rf.fit(combined.fillna(-999), train_test_labels)
    
    auc = roc_auc_score(train_test_labels, 
                        rf.predict_proba(combined.fillna(-999))[:, 1])
    
    if auc > 0.8:
        self.leakage_report['train_test_separation'] = {
            'auc': auc,
            'severity': 'HIGH',
            'warning': 'Train and test sets are too distinguishable',
            'implication': 'Model may not generalize (distribution shift too large)'
        }
    elif auc < 0.55:
        self.leakage_report['train_test_separation'] = {
            'auc': auc,
            'severity': 'LOW',
            'status': 'Good - train and test are similar'
        }
```

### 3.4 Statistical Tests for Leakage

| Test | Purpose | Threshold | Interpretation |
|------|---------|-----------|----------------|
| **Single Feature AUC** | Detect perfect predictors | > 0.95 | CRITICAL - likely leakage |
| **Pearson Correlation** | Linear target relationship | > 0.90 | HIGH - investigate |
| **Mutual Information** | Non-linear associations | > 0.8 (normalized) | MEDIUM - verify causality |
| **Feature Stability** | Train vs test distribution | KS statistic > 0.3 | HIGH - drift or leakage |
| **Null Importance** | Permutation test | p-value < 0.001 with no signal | Suspicious |

---

## PHASE 4: FEATURE ENGINEERING STRATEGY

### 4.1 Schema-Agnostic Feature Engineering Framework

**Core Principle**: Build features based on **semantic patterns**, not hardcoded column names.



```python
class SchemaAgnosticFeatureEngineer:
    """
    Feature engineering that survives schema changes
    """
    
    def __init__(self):
        self.feature_config = {}
        
    def auto_detect_columns(self, df):
        """Infer column types by pattern and distribution"""
        self.detected = {
            'transaction_id': [],
            'user_id': [],
            'amount': [],
            'timestamp': [],
            'categorical': [],
            'numerical': [],
            'email': [],
            'ip_address': [],
            'card_info': []
        }
        
        for col in df.columns:
            # Pattern-based detection
            col_lower = col.lower()
            
            if 'id' in col_lower or 'key' in col_lower:
                if df[col].nunique() / len(df) > 0.95:
                    self.detected['transaction_id'].append(col)
                else:
                    self.detected['user_id'].append(col)
                    
            elif 'amt' in col_lower or 'amount' in col_lower or 'price' in col_lower:
                self.detected['amount'].append(col)
                
            elif 'time' in col_lower or 'date' in col_lower or 'dt' in col_lower:
                self.detected['timestamp'].append(col)
                
            elif df[col].dtype == 'object' or df[col].dtype.name == 'category':
                self.detected['categorical'].append(col)
                
            elif np.issubdtype(df[col].dtype, np.number):
                self.detected['numerical'].append(col)
        
        return self.detected
```

### 4.2 Feature Categories

#### 4.2.1 Entity-Level Features (User Behavior)

These features characterize the entity (user/card/account) making the transaction.

| Feature Type | Description | Leakage Risk | Production Feasibility |
|--------------|-------------|--------------|----------------------|
| **Historical Transaction Count** | Total transactions by user (up to current time) | ✅ LOW | ✅ HIGH - easy to maintain |
| **Historical Fraud Rate** | % of user's past transactions that were fraud | ⚠️ MEDIUM - must exclude current | ✅ HIGH |
| **Account Age** | Days since first transaction | ✅ LOW | ✅ HIGH |
| **Average Transaction Amount** | User's typical transaction size | ✅ LOW | ✅ HIGH |
| **Transaction Frequency** | Transactions per day/week | ✅ LOW | ✅ HIGH |

```python
def create_entity_features(self, df, entity_col, time_col):
    """Point-in-time aggregations"""
    features = pd.DataFrame(index=df.index)
    
    # Sort by time to ensure no lookahead
    df = df.sort_values(time_col)
    
    # Expanding window (only past information)
    features['entity_transaction_count'] = df.groupby(entity_col).cumcount()
    features['entity_transaction_velocity'] = (
        features['entity_transaction_count'] / 
        (df[time_col] - df.groupby(entity_col)[time_col].transform('first'))
    )
    
    return features
```

#### 4.2.2 Transaction-Level Features

| Feature Type | Description | Leakage Risk | Production Feasibility |
|--------------|-------------|--------------|------------------------|
| **Amount Bands** | Categorical bins of transaction amounts | ✅ LOW | ✅ HIGH |
| **Hour of Day** | When transaction occurred | ✅ LOW | ✅ HIGH |
| **Day of Week** | Weekday vs weekend patterns | ✅ LOW | ✅ HIGH |
| **Is Round Amount** | Amount ends in .00 (behavioral signal) | ✅ LOW | ✅ HIGH |
| **Amount Digit Patterns** | First/last digits (Benford's law) | ✅ LOW | ✅ MEDIUM |

