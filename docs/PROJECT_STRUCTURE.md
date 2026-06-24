# Production Risk Scoring System - Project Structure

## Complete Directory Structure

```
risk-scoring-system/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── model-training.yml
│       └── deployment.yml
│
├── config/
│   ├── config.yaml                 # Master configuration
│   ├── feature_config.yaml         # Feature engineering settings
│   ├── model_config.yaml           # Model hyperparameters
│   └── monitoring_config.yaml      # Drift thresholds, alerts
│
├── data/
│   ├── raw/                        # Original downloaded data (gitignored)
│   ├── processed/                  # Cleaned, feature-engineered data
│   ├── splits/                     # Train/val/test splits
│   └── metadata/
│       ├── schema.json             # Expected data schema
│       └── feature_catalog.json    # Feature documentation
│
├── notebooks/
│   ├── 01_eda.ipynb                        # Exploratory data analysis
│   ├── 02_leakage_analysis.ipynb           # Leakage detection
│   ├── 03_feature_engineering.ipynb        # Feature development
│   ├── 04_model_experiments.ipynb          # Model selection
│   ├── 05_validation_strategy.ipynb        # Temporal validation
│   └── 06_production_simulation.ipynb      # Schema drift testing
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py               # Data loading utilities
│   │   ├── validator.py            # Schema validation
│   │   ├── quality.py              # DataQualityAuditor class
│   │   └── splitter.py             # Temporal split logic
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base feature engineering class
│   │   ├── entity_features.py      # User/card level features
│   │   ├── transaction_features.py # Transaction-level features
│   │   ├── temporal_features.py    # Time-based aggregations
│   │   ├── risk_features.py        # Historical risk features
│   │   └── schema_agnostic.py      # Pattern-based feature detection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py           # Abstract model interface
│   │   ├── logistic.py             # Logistic Regression
│   │   ├── random_forest.py        # Random Forest
│   │   ├── xgboost_model.py        # XGBoost
│   │   ├── lightgbm_model.py       # LightGBM
│   │   ├── catboost_model.py       # CatBoost
│   │   ├── ensemble.py             # Model ensembling
│   │   └── calibration.py          # Probability calibration
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── temporal_split.py       # TimeSeriesSplit, walk-forward
│   │   ├── metrics.py              # PR-AUC, Recall@K, MCC, Brier
│   │   └── leakage_detector.py     # LeakageDetector class
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── drift.py                # PSI, KS test, distribution monitoring
│   │   ├── performance.py          # Performance tracking over time
│   │   └── alerts.py               # Alert system
│   │
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── api.py                  # FastAPI inference endpoint
│   │   ├── preprocessing.py        # Inference-time preprocessing
│   │   ├── schema_handler.py       # Handle schema changes
│   │   └── fallback.py             # Graceful degradation logic
│   │
│   └── utils/
│       ├── __init__.py
│       ├── io.py                   # File I/O utilities
│       ├── logging.py              # Custom logging
│       └── visualization.py        # Plotting utilities
│
├── tests/
│   ├── __init__.py
│   ├── test_data/
│   │   ├── test_quality.py
│   │   ├── test_leakage.py
│   │   └── test_splitter.py
│   ├── test_features/
│   │   ├── test_entity_features.py
│   │   └── test_schema_agnostic.py
│   ├── test_models/
│   │   └── test_inference.py
│   └── test_inference/
│       ├── test_schema_drift.py
│       └── test_api.py
│
├── models/
│   ├── model_v1.pkl
│   ├── model_v2.pkl
│   ├── scaler.pkl
│   ├── encoder.pkl
│   └── metadata.json               # Model metadata
│
├── experiments/
│   ├── experiment_001/
│   │   ├── config.yaml
│   │   ├── metrics.json
│   │   ├── model.pkl
│   │   └── report.md
│   └── experiment_002/
│
├── reports/
│   ├── data_quality_report.html
│   ├── leakage_analysis_report.html
│   ├── model_evaluation_report.html
│   └── drift_monitoring_report.html
│
├── streamlit_app/
│   ├── app.py                      # Main Streamlit app
│   ├── pages/
│   │   ├── 1_upload_data.py
│   │   ├── 2_risk_scoring.py
│   │   ├── 3_high_risk_cases.py
│   │   ├── 4_model_monitoring.py
│   │   ├── 5_drift_dashboard.py
│   │   ├── 6_explainability.py
│   │   └── 7_validation_results.py
│   ├── utils/
│   │   └── ui_helpers.py
│   └── assets/
│       ├── styles.css
│       └── logo.png
│
├── scripts/
│   ├── download_data.py            # Download IEEE-CIS dataset
│   ├── train_model.py              # Training pipeline
│   ├── evaluate_model.py           # Evaluation pipeline
│   ├── generate_reports.py         # Generate HTML reports
│   └── deploy.py                   # Deployment script
│
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── terraform/
│       └── main.tf
│
└── docs/
    ├── architecture.md
    ├── api_documentation.md
    ├── feature_documentation.md
    ├── model_card.md
    └── production_runbook.md
```

## Key File Responsibilities

### Configuration Files

**config/config.yaml**
- Master settings (paths, thresholds, etc.)
- Environment-specific configs (dev, staging, prod)

**config/feature_config.yaml**
```yaml
entity_features:
  enabled: true
  lookback_days: 90
  min_transactions: 3

temporal_features:
  enabled: true
  windows: [7, 14, 30, 60]
  aggregations: ['mean', 'std', 'max', 'min']

schema_detection:
  enabled: true
  column_patterns:
    transaction_id: ['id', 'transaction', 'key']
    amount: ['amt', 'amount', 'price', 'value']
```

### Core Modules

**src/data/quality.py**
- DataQualityAuditor class
- Missing value analysis
- Outlier detection
- Data quality scoring

**src/validation/leakage_detector.py**
- LeakageDetector class
- Perfect predictor detection
- Temporal leakage checks
- Label proxy identification

**src/features/schema_agnostic.py**
- SchemaAgnosticFeatureEngineer class
- Auto-detect column types by pattern
- Fallback strategies for missing columns
- Robust encoding

**src/monitoring/drift.py**
- DriftMonitor class
- PSI calculation
- KS tests
- Alert generation

**src/inference/api.py**
- FastAPI application
- /predict endpoint
- Schema validation
- Error handling

