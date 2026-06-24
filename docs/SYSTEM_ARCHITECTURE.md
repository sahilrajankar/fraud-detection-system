# System Architecture - Production Risk Scoring System

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION ENVIRONMENT                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐         ┌──────────────┐        ┌─────────────┐  │
│  │   Upstream   │────────▶│   Inference  │───────▶│  Downstream │  │
│  │   Systems    │ Request │      API     │Response│   Systems   │  │
│  │(Transaction) │         │   (FastAPI)  │        │  (Alerts)   │  │
│  └──────────────┘         └──────┬───────┘        └─────────────┘  │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │  Preprocessing  │                        │
│                          │    Pipeline     │                        │
│                          └────────┬────────┘                        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │    Feature      │                        │
│                          │   Engineering   │                        │
│                          └────────┬────────┘                        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │   ML Model      │                        │
│                          │  (Prediction)   │                        │
│                          └────────┬────────┘                        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │  Calibration    │                        │
│                          │    & Scoring    │                        │
│                          └────────┬────────┘                        │
│                                   │                                  │
│                          ┌────────▼────────┐                        │
│                          │   Monitoring    │                        │
│                          │  (Drift/Perf)   │                        │
│                          └─────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          TRAINING PIPELINE                           │
└─────────────────────────────────────────────────────────────────────┘

Raw Data (IEEE-CIS)
        │
        ▼
┌───────────────────┐
│  Data Validation  │──────▶ Schema Check
│   & Quality Audit │──────▶ Missing Values Analysis
└─────────┬─────────┘──────▶ Outlier Detection
          │                ▶ Data Quality Score
          │
          ▼
┌───────────────────┐
│ Leakage Detection │──────▶ Perfect Predictor Test
│                   │──────▶ Temporal Availability Audit
└─────────┬─────────┘──────▶ Correlation Analysis
          │                ▶ Label Proxy Detection
          │
          ▼
┌───────────────────┐
│  Temporal Split   │──────▶ Train (60%)
│                   │──────▶ Validation (20%)
└─────────┬─────────┘──────▶ Holdout (10%)
          │                ▶ Hidden Test (10%)
          │                ▶ Gap Period (14 days)
          │
          ▼
┌───────────────────┐
│Feature Engineering│──────▶ Entity Features
│ (Schema-Agnostic) │──────▶ Transaction Features
└─────────┬─────────┘──────▶ Temporal Aggregations
          │                ▶ Risk History
          │                ▶ Behavioral Deviations
          │
          ▼
┌───────────────────┐
│  Model Training   │──────▶ Class Imbalance Handling
│                   │──────▶ Cross-Validation
└─────────┬─────────┘──────▶ Hyperparameter Tuning
          │                ▶ Early Stopping
          │
          ▼
┌───────────────────┐
│    Calibration    │──────▶ Platt Scaling
│                   │──────▶ Isotonic Regression
└─────────┬─────────┘──────▶ Reliability Curves
          │
          ▼
┌───────────────────┐
│    Evaluation     │──────▶ PR-AUC
│                   │──────▶ Recall@K
└─────────┬─────────┘──────▶ Precision@K
          │                ▶ Brier Score
          │                ▶ MCC
          │
          ▼
┌───────────────────┐
│  Model Registry   │──────▶ Version Control
│                   │──────▶ Metadata Storage
└─────────┬─────────┘──────▶ Artifact Management
          │
          ▼
    PRODUCTION


┌─────────────────────────────────────────────────────────────────────┐
│                         INFERENCE PIPELINE                           │
└─────────────────────────────────────────────────────────────────────┘

Incoming Request (JSON)
        │
        ▼
┌───────────────────┐
│ Schema Validation │──────▶ Column Existence Check
│                   │──────▶ Type Validation
└─────────┬─────────┘──────▶ Range Validation
          │
          ├─── FAIL ───▶ Error Response (400)
          │
          ▼ PASS
┌───────────────────┐
│  Schema Handler   │──────▶ Missing Column Detection
│                   │──────▶ Unknown Category Handling
└─────────┬─────────┘──────▶ Type Coercion
          │                ▶ Default Value Insertion
          │
          ▼
┌───────────────────┐
│Feature Engineering│──────▶ Auto-Detect Column Types
│ (Runtime)         │──────▶ Compute Features
└─────────┬─────────┘──────▶ Handle Missing Features
          │                ▶ Fallback Logic
          │
          ▼
┌───────────────────┐
│  Model Inference  │──────▶ Load Model
│                   │──────▶ Predict Probability
└─────────┬─────────┘──────▶ Confidence Score
          │
          ▼
┌───────────────────┐
│   Calibration     │──────▶ Apply Calibrator
│                   │──────▶ Adjust Probabilities
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Risk Scoring     │──────▶ Threshold Application
│                   │──────▶ Risk Band Assignment
└─────────┬─────────┘──────▶ Explainability (SHAP)
          │
          ▼
┌───────────────────┐
│    Monitoring     │──────▶ Log Prediction
│                   │──────▶ Track Drift Metrics
└─────────┬─────────┘──────▶ Performance Metrics
          │
          ▼
┌───────────────────┐
│  Response         │──────▶ risk_score: 0.85
│                   │──────▶ risk_band: "HIGH"
└───────────────────┘──────▶ confidence: 0.92
                           ▶ explanation: {...}
```

---

## Model Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MODEL LIFECYCLE                              │
└─────────────────────────────────────────────────────────────────────┘

1. DEVELOPMENT
   │
   ├─▶ Experimentation (Notebooks)
   │   └─▶ Feature ideas, model selection
   │
   ├─▶ Local Training
   │   └─▶ Validation, hyperparameter tuning
   │
   └─▶ Leakage Testing
       └─▶ Automated checks

2. STAGING
   │
   ├─▶ CI/CD Pipeline Triggered
   │   └─▶ GitHub Actions
   │
   ├─▶ Automated Tests
   │   ├─▶ Unit tests
   │   ├─▶ Integration tests
   │   ├─▶ Leakage tests
   │   └─▶ Schema drift tests
   │
   ├─▶ Training on Full Data
   │   └─▶ Walk-forward validation
   │
   ├─▶ Model Evaluation
   │   ├─▶ Holdout performance
   │   ├─▶ Calibration analysis
   │   └─▶ Fairness checks
   │
   └─▶ Model Registry
       └─▶ Version, metadata, artifacts

3. PRODUCTION
   │
   ├─▶ Deployment
   │   ├─▶ A/B testing (10% traffic)
   │   └─▶ Gradual rollout
   │
   ├─▶ Monitoring
   │   ├─▶ Performance tracking
   │   ├─▶ Drift detection
   │   ├─▶ Alert system
   │   └─▶ Dashboard
   │
   └─▶ Retraining Triggers
       ├─▶ Performance degradation
       ├─▶ Drift threshold exceeded
       └─▶ Scheduled (monthly)

4. RETIREMENT
   │
   ├─▶ Model Replacement
   │   └─▶ New version deployed
   │
   └─▶ Archival
       └─▶ Historical record
```

---

## Drift Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MONITORING DASHBOARD                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Feature Drift Monitoring                                  │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • PSI per feature (Population Stability Index)            │    │
│  │  • KS statistic (Kolmogorov-Smirnov test)                  │    │
│  │  • Distribution comparisons (train vs production)          │    │
│  │  • Alerts: PSI > 0.2 (retraining trigger)                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Prediction Drift Monitoring                               │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • Fraud rate over time                                    │    │
│  │  • Prediction distribution shifts                          │    │
│  │  • Confidence score trends                                 │    │
│  │  • High-risk case volume                                   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Performance Monitoring                                    │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • Precision/Recall (if labels available)                  │    │
│  │  • False positive rate                                     │    │
│  │  • Investigation yield                                     │    │
│  │  • Fraud capture rate                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  System Health                                             │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │  • API latency (p50, p95, p99)                             │    │
│  │  • Error rates                                             │    │
│  │  • Schema handling events                                  │    │
│  │  • Fallback invocations                                    │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Alert System
│
├─▶ Level 1: INFO
│   └─▶ Minor drift detected (PSI 0.1-0.2)
│
├─▶ Level 2: WARNING
│   └─▶ Moderate drift (PSI 0.2-0.3)
│   └─▶ Performance degradation > 5%
│
├─▶ Level 3: CRITICAL
│   └─▶ Severe drift (PSI > 0.3)
│   └─▶ Performance degradation > 10%
│   └─▶ API error rate > 1%
│
└─▶ Actions
    ├─▶ Email notifications
    ├─▶ Slack alerts
    ├─▶ PagerDuty (critical only)
    └─▶ Dashboard flags
```

---

## Technology Stack

### Training & Development
- **Languages**: Python 3.9+
- **Data Processing**: pandas, numpy, polars (for large datasets)
- **ML Frameworks**: scikit-learn, XGBoost, LightGBM, CatBoost
- **Validation**: sklearn.model_selection, TimeSeriesSplit
- **Explainability**: SHAP, LIME
- **Experiment Tracking**: MLflow, Weights & Biases
- **Notebooks**: Jupyter

### Production Inference
- **API Framework**: FastAPI
- **Model Serving**: Pickle (simple), ONNX (performance), MLflow (management)
- **Container**: Docker
- **Orchestration**: Kubernetes (optional), Docker Compose (dev)
- **Load Balancer**: Nginx
- **Caching**: Redis (for feature store)

### Monitoring & Observability
- **Metrics**: Prometheus
- **Visualization**: Grafana, Streamlit
- **Logging**: Python logging, ELK stack (optional)
- **Drift Detection**: Custom Python (PSI, KS), Evidently AI
- **Alerting**: Alertmanager, PagerDuty

### CI/CD & MLOps
- **Version Control**: Git, GitHub
- **CI/CD**: GitHub Actions
- **Model Registry**: MLflow Model Registry
- **Artifact Storage**: S3, Azure Blob, GCS
- **IaC**: Terraform (optional)

### Data Storage
- **Training Data**: Parquet files (versioned)
- **Feature Store**: Redis, DynamoDB (for production lookups)
- **Model Artifacts**: S3/Azure Blob
- **Logs**: S3, CloudWatch, ELK

