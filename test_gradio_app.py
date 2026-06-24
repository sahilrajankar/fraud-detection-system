"""
Quick test script to verify Gradio app works
"""

import json

# Test if all imports work
print("Testing imports...")

try:
    import gradio as gr
    print("✅ gradio")
except ImportError as e:
    print(f"❌ gradio: {e}")
    print("   Install: pip install gradio")

try:
    import pandas as pd
    print("✅ pandas")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    import numpy as np
    print("✅ numpy")
except ImportError as e:
    print(f"❌ numpy: {e}")

try:
    import joblib
    print("✅ joblib")
except ImportError as e:
    print(f"❌ joblib: {e}")

try:
    from pathlib import Path
    print("✅ pathlib")
except ImportError as e:
    print(f"❌ pathlib: {e}")

# Test if our modules can be imported
try:
    from src.inference.confidence_scorer import ConfidenceScorer
    print("✅ ConfidenceScorer")
except ImportError as e:
    print(f"❌ ConfidenceScorer: {e}")

try:
    from src.inference.enterprise_fraud_system import EnterpriseAntiFraudSystem
    print("✅ EnterpriseAntiFraudSystem")
except ImportError as e:
    print(f"❌ EnterpriseAntiFraudSystem: {e}")

try:
    from src.data.preprocessor import MessyDataPreprocessor
    print("✅ MessyDataPreprocessor")
except ImportError as e:
    print(f"❌ MessyDataPreprocessor: {e}")

try:
    from src.data.intelligent_parser import IntelligentJSONParser
    print("✅ IntelligentJSONParser")
except ImportError as e:
    print(f"❌ IntelligentJSONParser: {e}")

# Test if models exist
print("\nChecking models...")
from pathlib import Path

model_path = Path('models/fraud_model.pkl')
pipeline_path = Path('models/feature_pipeline.pkl')

if model_path.exists():
    print(f"✅ Model found: {model_path}")
else:
    print(f"❌ Model NOT found: {model_path}")

if pipeline_path.exists():
    print(f"✅ Pipeline found: {pipeline_path}")
else:
    print(f"❌ Pipeline NOT found: {pipeline_path}")

print("\n" + "="*80)
print("If all imports are ✅, you can run:")
print("  python app.py")
print("="*80)
