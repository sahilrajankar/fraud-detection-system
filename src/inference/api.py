"""
Production Inference API
FastAPI endpoint for real-time fraud scoring
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
from typing import Dict, Any, Optional
from pathlib import Path

from src.inference.confidence_scorer import ConfidenceScorer
from src.inference.enterprise_fraud_system import EnterpriseAntiFraudSystem
from src.data.preprocessor import MessyDataPreprocessor
from src.data.intelligent_parser import IntelligentJSONParser

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Fraud Detection API",
    description="Production-grade fraud detection: ML + 20+ Enterprise Rules + Explainable AI + ANY JSON Structure",
    version="3.2.0"
)

# Global variables for loaded models
MODEL = None
PIPELINE = None
CONFIDENCE_SCORER = None
RULE_ENGINE = EnterpriseAntiFraudSystem()  # Enterprise anti-fraud system
PREPROCESSOR = MessyDataPreprocessor()  # Data cleaning
JSON_PARSER = IntelligentJSONParser()  # Intelligent JSON parsing


class TransactionRequest(BaseModel):
    """Transaction data for scoring"""
    transaction_data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_data": {
                    "TransactionAmt": 150.0,
                    "ProductCD": "W",
                    "card1": 12345,
                    "card2": 111,
                    "card3": 150,
                    "TransactionDT": 86400
                }
            }
        }


class PredictionResponse(BaseModel):
    """Fraud prediction response"""
    fraud_probability: float
    risk_level: str
    confidence_score: float
    recommendation: str
    details: Optional[Dict[str, Any]] = None


def load_models():
    """Load trained model and pipeline"""
    global MODEL, PIPELINE, CONFIDENCE_SCORER
    
    model_path = Path('models/fraud_model.pkl')
    pipeline_path = Path('models/feature_pipeline.pkl')
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Train model first!")
    
    if not pipeline_path.exists():
        raise FileNotFoundError(f"Pipeline not found at {pipeline_path}. Train model first!")
    
    MODEL = joblib.load(model_path)
    PIPELINE = joblib.load(pipeline_path)
    CONFIDENCE_SCORER = ConfidenceScorer()
    
    print("✅ Models loaded successfully!")


@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    try:
        load_models()
    except Exception as e:
        print(f"⚠️  Warning: Could not load models: {e}")
        print("Train a model first using: python scripts/train_model.py")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Fraud Detection API",
        "version": "1.0.0",
        "model_loaded": MODEL is not None
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy" if MODEL is not None else "no_model",
        "model_loaded": MODEL is not None,
        "pipeline_loaded": PIPELINE is not None,
        "confidence_scorer_loaded": CONFIDENCE_SCORER is not None
    }


@app.post("/predict_unstructured")
def predict_fraud_unstructured(request: Dict[str, Any]):
    """
    Predict fraud for COMPLETELY UNSTRUCTURED JSON
    
    Handles:
    - Deeply nested JSON (unlimited depth)
    - Varying schemas
    - Different field names
    - Arrays/lists
    - Mixed formats
    - Missing values
    
    Returns fraud prediction + extraction confidence
    """
    if MODEL is None or PIPELINE is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train a model first."
        )
    
    try:
        # Step 1: Parse unstructured JSON → flat structure
        parsed_data = JSON_PARSER.parse(request)
        extraction_confidence = parsed_data.get('_parser_metadata', {}).get('confidence', 0.5)
        
        # Remove metadata from prediction
        if '_parser_metadata' in parsed_data:
            parser_metadata = parsed_data.pop('_parser_metadata')
        else:
            parser_metadata = {}
        
        # Step 2: Clean the parsed data
        cleaned_data, cleaning_metadata = PREPROCESSOR.clean_transaction(parsed_data)
        data_quality = cleaning_metadata['quality_score']
        
        # Step 3: Combined confidence
        combined_confidence = extraction_confidence * data_quality
        
        # If confidence too low, manual review needed
        if combined_confidence < 0.2:
            return {
                "fraud_probability": 0.5,
                "risk_level": "UNKNOWN",
                "confidence_score": combined_confidence,
                "recommendation": "MANUAL REVIEW - Data structure too unstructured or quality too poor",
                "details": {
                    "extraction_confidence": extraction_confidence,
                    "data_quality": data_quality,
                    "extraction_log": parser_metadata.get('extraction_log', []),
                    "quality_issues": cleaning_metadata['quality_issues'][:10],
                    "warning": "Low confidence - manual review required"
                }
            }
        
        # Step 4: Run through prediction pipeline
        rule_result = RULE_ENGINE.evaluate(cleaned_data)
        rule_score = rule_result['rule_score']
        
        # ML prediction
        df = pd.DataFrame([cleaned_data])
        
        try:
            features = PIPELINE.transform(df)
            
            # Adjust feature count
            expected_features = 52
            if features.shape[1] != expected_features:
                if features.shape[1] < expected_features:
                    padding = pd.DataFrame(
                        np.zeros((features.shape[0], expected_features - features.shape[1])),
                        columns=[f'pad_{i}' for i in range(expected_features - features.shape[1])],
                        index=features.index
                    )
                    features = pd.concat([features, padding], axis=1)
                else:
                    features = features.iloc[:, :expected_features]
        
        except Exception as e:
            print(f"⚠️ Feature extraction error: {e}")
            features = pd.DataFrame([[0] * 52], columns=[f'feature_{i}' for i in range(52)])
            combined_confidence *= 0.5
        
        ml_prob = float(MODEL.predict_proba(features)[0, 1])
        
        # Combine scores
        if rule_score > 0.5:
            final_prob = max(ml_prob, rule_score) * combined_confidence
        else:
            final_prob = ml_prob * combined_confidence
        
        # Determine risk level
        if final_prob >= 0.80 or rule_result['severity'] == 'CRITICAL':
            risk_level = "CRITICAL"
            recommendation = "BLOCK transaction immediately"
        elif final_prob >= 0.50 or rule_result['severity'] == 'HIGH':
            risk_level = "HIGH"
            recommendation = "HOLD for manual review"
        elif final_prob >= 0.20 or rule_result['severity'] == 'MEDIUM':
            risk_level = "MEDIUM"
            recommendation = "FLAG for monitoring"
        else:
            risk_level = "LOW"
            recommendation = "APPROVE - low risk"
        
        return {
            "fraud_probability": round(final_prob, 4),
            "risk_level": risk_level,
            "confidence_score": round(combined_confidence, 4),
            "recommendation": recommendation,
            "details": {
                "ml_probability": round(ml_prob, 4),
                "rule_score": round(rule_score, 4),
                "rule_severity": rule_result['severity'],
                "rules_triggered": rule_result['rule_count'],
                "rule_explanation": rule_result['explanation'],
                "extraction_confidence": round(extraction_confidence, 4),
                "data_quality": round(data_quality, 4),
                "extraction_log": parser_metadata.get('extraction_log', [])[:5],
                "fields_extracted": parser_metadata.get('fields_extracted', 0),
                "quality_issues": cleaning_metadata['quality_issues'][:3],
                "features_extracted": int(features.shape[1]),
                "scoring_method": "HYBRID (Rules + ML) with Intelligent Parsing + Cleaning"
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict_messy", response_model=PredictionResponse)
def predict_fraud_messy(request: TransactionRequest):
    """
    Predict fraud probability for MESSY real-world data
    
    Handles:
    - Missing values
    - Type mismatches
    - Format inconsistencies
    - Outliers
    - Invalid data
    
    Returns fraud prediction + data quality score
    """
    if MODEL is None or PIPELINE is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train a model first."
        )
    
    try:
        # Step 1: Clean messy data
        cleaned_data, metadata = PREPROCESSOR.clean_transaction(request.transaction_data)
        
        data_quality = metadata['quality_score']
        
        # If data quality is too poor, warn user
        if data_quality < 0.3:
            return PredictionResponse(
                fraud_probability=0.5,
                risk_level="UNKNOWN",
                confidence_score=data_quality,
                recommendation="MANUAL REVIEW - Data quality too poor for reliable prediction",
                details={
                    "data_quality": data_quality,
                    "quality_issues": metadata['quality_issues'][:10],
                    "cleaning_stats": metadata['cleaning_stats'],
                    "warning": "Low data quality - results may be unreliable"
                }
            )
        
        # Step 2: Run through normal prediction pipeline
        # (Rules first, then ML)
        rule_result = RULE_ENGINE.evaluate(cleaned_data)
        rule_score = rule_result['rule_score']
        
        # Convert to DataFrame for ML
        df = pd.DataFrame([cleaned_data])
        
        # Schema compatibility
        confidence = data_quality  # Use data quality as base confidence
        
        # Extract features
        try:
            features = PIPELINE.transform(df)
            
            # Feature count adjustment
            expected_features = 52
            if features.shape[1] != expected_features:
                if features.shape[1] < expected_features:
                    padding = pd.DataFrame(
                        np.zeros((features.shape[0], expected_features - features.shape[1])),
                        columns=[f'pad_{i}' for i in range(expected_features - features.shape[1])],
                        index=features.index
                    )
                    features = pd.concat([features, padding], axis=1)
                else:
                    features = features.iloc[:, :expected_features]
                
                confidence *= 0.8  # Reduce confidence
        
        except Exception as e:
            print(f"⚠️ Feature extraction error: {e}")
            confidence *= 0.5
            features = pd.DataFrame([[0] * 52], columns=[f'feature_{i}' for i in range(52)])
        
        # ML prediction
        ml_prob = float(MODEL.predict_proba(features)[0, 1])
        
        # Combine scores
        if rule_score > 0.5:
            combined_prob = max(ml_prob, rule_score)
            final_prob = combined_prob * confidence
        else:
            final_prob = ml_prob * confidence
        
        # Determine risk level
        if final_prob >= 0.80 or rule_result['severity'] == 'CRITICAL':
            risk_level = "CRITICAL"
            recommendation = "BLOCK transaction immediately and investigate"
        elif final_prob >= 0.50 or rule_result['severity'] == 'HIGH':
            risk_level = "HIGH"
            recommendation = "HOLD for manual review"
        elif final_prob >= 0.20 or rule_result['severity'] == 'MEDIUM':
            risk_level = "MEDIUM"
            recommendation = "FLAG for monitoring"
        else:
            risk_level = "LOW"
            recommendation = "APPROVE - low risk"
        
        return PredictionResponse(
            fraud_probability=round(final_prob, 4),
            risk_level=risk_level,
            confidence_score=round(confidence, 4),
            recommendation=recommendation,
            details={
                "ml_probability": round(ml_prob, 4),
                "rule_score": round(rule_score, 4),
                "rule_severity": rule_result['severity'],
                "rules_triggered": rule_result['rule_count'],
                "rule_explanation": rule_result['explanation'],
                "data_quality": round(data_quality, 4),
                "data_cleaned": metadata['cleaning_stats'],
                "quality_issues": metadata['quality_issues'][:5],
                "original_fields": metadata['original_fields'],
                "cleaned_fields": metadata['cleaned_fields'],
                "features_extracted": int(features.shape[1]),
                "scoring_method": "HYBRID (Rules + ML) with Data Cleaning"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict", response_model=PredictionResponse)
def predict_fraud(request: TransactionRequest):
    """
    Predict fraud probability for a transaction
    
    Returns:
        - fraud_probability: 0.0 to 1.0
        - risk_level: LOW, MEDIUM, HIGH, CRITICAL
        - confidence_score: How confident are we? (0.0 to 1.0)
        - recommendation: What action to take
    """
    if MODEL is None or PIPELINE is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train a model first."
        )
    
    try:
        # 1. RULE-BASED CHECK FIRST (catches obvious fraud)
        rule_result = RULE_ENGINE.evaluate(request.transaction_data)
        rule_score = rule_result['rule_score']
        
        # Convert to DataFrame
        df = pd.DataFrame([request.transaction_data])
        
        # Schema compatibility check
        if CONFIDENCE_SCORER:
            try:
                confidence, details = CONFIDENCE_SCORER.score_confidence(df)
            except:
                confidence = 0.80  # Default if scorer not fitted
        else:
            confidence = 0.80  # Default confidence
        
        # 2. ML MODEL PREDICTION
        # Extract features (handles schema changes gracefully!)
        try:
            features = PIPELINE.transform(df)
            
            # Ensure feature count matches (pad with zeros if needed)
            expected_features = 52  # From training (updated)
            if features.shape[1] != expected_features:
                print(f"⚠️ Feature mismatch: {features.shape[1]} vs {expected_features}")
                # Pad or truncate
                if features.shape[1] < expected_features:
                    # Pad with zeros
                    padding = pd.DataFrame(
                        np.zeros((features.shape[0], expected_features - features.shape[1])),
                        columns=[f'pad_{i}' for i in range(expected_features - features.shape[1])],
                        index=features.index
                    )
                    features = pd.concat([features, padding], axis=1)
                else:
                    # Truncate
                    features = features.iloc[:, :expected_features]
                
                confidence *= 0.7  # Reduce confidence due to feature mismatch
                
        except Exception as e:
            # Degraded mode - use minimal features
            print(f"⚠️  Feature extraction warning: {e}")
            confidence *= 0.5  # Reduce confidence
            # Create minimal feature set
            features = pd.DataFrame([[0] * 52], columns=[f'feature_{i}' for i in range(52)])
        
        # Predict
        ml_prob = float(MODEL.predict_proba(features)[0, 1])
        
        # 3. COMBINE RULE + ML SCORES
        # If rules triggered, boost the score
        if rule_score > 0.5:
            # Rules say HIGH RISK - trust them more than ML
            combined_prob = max(ml_prob, rule_score)
            final_prob = combined_prob * confidence
        else:
            # Rules say OK - use ML prediction
            final_prob = ml_prob * confidence
        
        # Adjust by confidence
        adjusted_prob = final_prob
        
        # Determine risk level
        if adjusted_prob >= 0.80 or rule_result['severity'] == 'CRITICAL':
            risk_level = "CRITICAL"
            recommendation = "BLOCK transaction immediately and investigate"
        elif adjusted_prob >= 0.50 or rule_result['severity'] == 'HIGH':
            risk_level = "HIGH"
            recommendation = "HOLD for manual review"
        elif adjusted_prob >= 0.20 or rule_result['severity'] == 'MEDIUM':
            risk_level = "MEDIUM"
            recommendation = "FLAG for monitoring"
        else:
            risk_level = "LOW"
            recommendation = "APPROVE - low risk"
        
        # Build response
        return PredictionResponse(
            fraud_probability=round(adjusted_prob, 4),
            risk_level=risk_level,
            confidence_score=round(confidence, 4),
            recommendation=recommendation,
            details={
                "ml_probability": round(ml_prob, 4),
                "rule_score": round(rule_score, 4),
                "rule_severity": rule_result['severity'],
                "rules_triggered": rule_result['rule_count'],
                "rule_explanation": rule_result['explanation'],
                "schema_compatibility": round(confidence, 4),
                "features_extracted": int(features.shape[1]),
                "scoring_method": "HYBRID (Rules + ML)"
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/batch_predict")
def batch_predict(transactions: list[Dict[str, Any]]):
    """
    Predict fraud for multiple transactions
    
    Returns list of predictions
    """
    if MODEL is None or PIPELINE is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Train a model first."
        )
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Extract features
        features = PIPELINE.transform(df)
        
        # Predict
        fraud_probs = MODEL.predict_proba(features)[:, 1]
        
        # Build responses
        results = []
        for i, prob in enumerate(fraud_probs):
            prob = float(prob)
            
            if prob >= 0.80:
                risk_level = "CRITICAL"
            elif prob >= 0.50:
                risk_level = "HIGH"
            elif prob >= 0.20:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            results.append({
                "transaction_index": i,
                "fraud_probability": round(prob, 4),
                "risk_level": risk_level
            })
        
        return {
            "total_transactions": len(transactions),
            "predictions": results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("Starting Fraud Detection API")
    print("=" * 80)
    print("\n📍 API will be available at:")
    print("   - http://localhost:8000")
    print("   - http://localhost:8000/docs (Swagger UI)")
    print("   - http://localhost:8000/redoc (ReDoc)")
    print("\n💡 Test the API:")
    print("   curl -X POST http://localhost:8000/predict \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"transaction_data": {"TransactionAmt": 150.0}}\'')
    print("\n" + "=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
