"""
Prediction Confidence Scoring
Returns a confidence score based on schema match quality
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class ConfidenceScorer:
    """
    Scores prediction confidence based on:
    1. Schema similarity to training data
    2. Feature availability
    3. Data quality of input
    """
    
    def __init__(self):
        self.training_schema = None
        self.feature_importance = None
        self.detected_columns_train = None
    
    def fit(self, training_df: pd.DataFrame, feature_importance: Dict = None):
        """Learn training schema"""
        self.training_schema = {
            'columns': set(training_df.columns),
            'dtypes': training_df.dtypes.to_dict()
        }
        self.feature_importance = feature_importance or {}
        
        # Store which patterns we found in training
        self.detected_columns_train = self._detect_patterns(training_df)
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict:
        """Detect column patterns"""
        patterns = {
            'amount': [],
            'card': [],
            'time': [],
            'identity': []
        }
        
        for col in df.columns:
            col_lower = col.lower()
            if any(p in col_lower for p in ['amt', 'amount', 'price', 'value']):
                patterns['amount'].append(col)
            elif any(p in col_lower for p in ['card', 'payment']):
                patterns['card'].append(col)
            elif any(p in col_lower for p in ['time', 'date', 'dt']):
                patterns['time'].append(col)
            elif any(p in col_lower for p in ['id_', 'identity']):
                patterns['identity'].append(col)
        
        return patterns
    
    def score_confidence(self, test_df: pd.DataFrame) -> Tuple[float, Dict]:
        """
        Calculate prediction confidence score (0-1)
        
        Returns:
            confidence: float 0-1 (1 = high confidence)
            details: dict with breakdown
        """
        if self.training_schema is None:
            return 0.5, {'warning': 'Not fitted'}
        
        details = {}
        score = 1.0  # Start at 100% confidence
        
        # 1. Schema similarity (30% weight)
        test_cols = set(test_df.columns)
        train_cols = self.training_schema['columns']
        
        overlap = len(test_cols & train_cols)
        missing = len(train_cols - test_cols)
        extra = len(test_cols - train_cols)
        
        schema_score = overlap / len(train_cols) if train_cols else 0
        details['schema_overlap'] = schema_score
        details['missing_columns'] = missing
        details['extra_columns'] = extra
        
        # Penalize missing columns
        score -= (missing / len(train_cols)) * 0.3
        
        # 2. Pattern similarity (40% weight)
        detected_test = self._detect_patterns(test_df)
        
        pattern_matches = 0
        pattern_total = 0
        
        for pattern_type in ['amount', 'card', 'time', 'identity']:
            train_found = len(self.detected_columns_train.get(pattern_type, []))
            test_found = len(detected_test.get(pattern_type, []))
            
            if train_found > 0:
                pattern_total += 1
                if test_found > 0:
                    pattern_matches += 1
                else:
                    details[f'missing_{pattern_type}_pattern'] = True
        
        pattern_score = pattern_matches / pattern_total if pattern_total > 0 else 0
        details['pattern_match_rate'] = pattern_score
        
        # Critical patterns missing? Heavy penalty
        if pattern_score < 0.5:
            score -= 0.4  # Major confidence hit
        elif pattern_score < 0.75:
            score -= 0.2
        
        # 3. Data quality (30% weight)
        missing_pct = (test_df.isnull().sum().sum() / test_df.size) * 100
        details['missing_data_pct'] = missing_pct
        
        if missing_pct > 50:
            score -= 0.3
        elif missing_pct > 30:
            score -= 0.15
        elif missing_pct > 10:
            score -= 0.05
        
        # 4. Final score (0-1 range)
        final_confidence = max(min(score, 1.0), 0.0)
        
        # Classify confidence level
        if final_confidence > 0.8:
            details['confidence_level'] = 'HIGH'
        elif final_confidence > 0.5:
            details['confidence_level'] = 'MEDIUM'
        else:
            details['confidence_level'] = 'LOW'
        
        # Warnings
        warnings = []
        if final_confidence < 0.3:
            warnings.append('CRITICAL: Very low confidence - schema highly incompatible')
        elif final_confidence < 0.5:
            warnings.append('WARNING: Low confidence - significant schema differences')
        
        if missing > len(train_cols) * 0.5:
            warnings.append('WARNING: >50% of training columns missing')
        
        if pattern_score < 0.5:
            warnings.append('WARNING: Critical feature patterns missing')
        
        details['warnings'] = warnings
        details['final_confidence'] = final_confidence
        
        return final_confidence, details


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("Confidence Scoring System - DEMO")
    print("=" * 80)
    print()
    
    # Training data
    train_df = pd.DataFrame({
        'TransactionAmt': [150, 200, 50],
        'card1': ['A', 'B', 'C'],
        'card2': [100, 200, 300],
        'TransactionDT': [1, 2, 3],
        'ProductCD': ['W', 'H', 'C']
    })
    
    scorer = ConfidenceScorer()
    scorer.fit(train_df)
    print("✓ Trained on 5 columns")
    print()
    
    # TEST 1: Perfect match
    print("TEST 1: Perfect Schema Match")
    test_perfect = train_df.copy()
    conf, details = scorer.score_confidence(test_perfect)
    print(f"Confidence: {conf:.2f} ({details['confidence_level']})")
    print(f"Schema overlap: {details['schema_overlap']:.2%}")
    print()
    
    # TEST 2: Missing columns
    print("TEST 2: 40% Columns Missing")
    test_missing = train_df[['TransactionAmt', 'card1', 'TransactionDT']].copy()
    conf, details = scorer.score_confidence(test_missing)
    print(f"Confidence: {conf:.2f} ({details['confidence_level']})")
    print(f"Missing columns: {details['missing_columns']}")
    print(f"Warnings: {details['warnings']}")
    print()
    
    # TEST 3: Renamed but patterns match
    print("TEST 3: Renamed Columns (patterns preserved)")
    test_renamed = pd.DataFrame({
        'transaction_amount_usd': [160, 210],
        'payment_card': ['D', 'E'],
        'timestamp': [4, 5]
    })
    conf, details = scorer.score_confidence(test_renamed)
    print(f"Confidence: {conf:.2f} ({details['confidence_level']})")
    print(f"Pattern match: {details['pattern_match_rate']:.2%}")
    print()
    
    # TEST 4: Completely different schema
    print("TEST 4: Completely Different Schema")
    test_different = pd.DataFrame({
        'user_id': [1, 2],
        'session_length': [100, 200],
        'browser': ['chrome', 'firefox']
    })
    conf, details = scorer.score_confidence(test_different)
    print(f"Confidence: {conf:.2f} ({details['confidence_level']})")
    print(f"Pattern match: {details['pattern_match_rate']:.2%}")
    print(f"Warnings: {details['warnings']}")
    print()
    
    print("=" * 80)
    print("Summary: Confidence scoring helps detect when schema is incompatible")
    print("=" * 80)
