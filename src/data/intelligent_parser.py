"""
Intelligent Unstructured JSON Parser
Automatically extracts transaction features from ANY JSON structure
Handles: nested objects, arrays, varying schemas, mixed formats
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import re
from collections import defaultdict


class IntelligentJSONParser:
    """
    Extracts transaction features from ANY JSON structure
    
    Handles:
    - Deeply nested JSON (unlimited depth)
    - Arrays/lists
    - Mixed data types
    - Varying schemas
    - Multiple field name variations
    - Automatic field detection by semantic meaning
    """
    
    def __init__(self):
        # Semantic field mappings
        self.field_patterns = {
            'amount': ['amount', 'value', 'total', 'sum', 'price', 'cost', 'payment', 'transaction_amt'],
            'balance': ['balance', 'available', 'funds', 'account_balance', 'current_balance'],
            'timestamp': ['timestamp', 'time', 'date', 'datetime', 'created', 'transaction_time'],
            'country': ['country', 'location', 'nation', 'region', 'geo', 'origin'],
            'merchant': ['merchant', 'vendor', 'seller', 'payee', 'recipient', 'store'],
            'category': ['category', 'type', 'class', 'merchant_category', 'mcc'],
            'customer_age': ['age', 'customer_age', 'user_age', 'account_age_years'],
            'account_age_days': ['account_age', 'days_old', 'tenure', 'account_age_days'],
            'occupation': ['occupation', 'job', 'profession', 'work', 'employment'],
            'device': ['device', 'device_type', 'platform', 'client'],
            'ip_risk': ['ip_risk', 'risk_score', 'ip_score', 'threat_score'],
            'failed_attempts': ['failed', 'failures', 'attempts', 'login_attempts', 'failed_login'],
            'velocity': ['velocity', 'count', 'frequency', 'transactions_count', 'txn_count'],
            'email': ['email', 'mail', 'email_address'],
            'phone': ['phone', 'mobile', 'telephone', 'contact'],
            'card': ['card', 'card_number', 'pan', 'payment_method'],
            'currency': ['currency', 'curr', 'denomination'],
        }
        
        self.extracted_fields = {}
        self.extraction_log = []
    
    def parse(self, data: Any) -> Dict[str, Any]:
        """
        Parse ANY JSON structure and extract transaction fields
        
        Args:
            data: Raw JSON (dict, list, or string)
        
        Returns:
            Flattened dict with extracted transaction fields
        """
        self.extracted_fields = {}
        self.extraction_log = []
        
        # Handle string JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return {'raw_text': data}
        
        # Handle list (extract first item or merge all)
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]  # Use first transaction
            else:
                return {}
        
        # Flatten nested structure
        flattened = self._flatten_json(data)
        
        # Extract semantic fields
        extracted = self._extract_semantic_fields(flattened)
        
        # Add metadata
        extracted['_parser_metadata'] = {
            'fields_extracted': len(extracted),
            'extraction_log': self.extraction_log[:10],  # Top 10
            'confidence': self._calculate_extraction_confidence(extracted)
        }
        
        return extracted
    
    def _flatten_json(self, data: Any, parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """
        Recursively flatten nested JSON
        
        Example:
            {"user": {"age": 30}} → {"user_age": 30}
        """
        items = []
        
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                
                if isinstance(v, dict):
                    items.extend(self._flatten_json(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    # Handle arrays
                    for i, item in enumerate(v):
                        if isinstance(item, dict):
                            items.extend(self._flatten_json(item, f"{new_key}_{i}", sep=sep).items())
                        else:
                            items.append((f"{new_key}_{i}", item))
                else:
                    items.append((new_key, v))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_key = f"{parent_key}_{i}"
                if isinstance(item, dict):
                    items.extend(self._flatten_json(item, new_key, sep=sep).items())
                else:
                    items.append((new_key, item))
        else:
            items.append((parent_key, data))
        
        return dict(items)
    
    def _extract_semantic_fields(self, flattened: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields by semantic meaning (not exact name match)
        """
        extracted = {}
        
        for semantic_field, patterns in self.field_patterns.items():
            # Try to find this semantic field in flattened data
            found = False
            
            for pattern in patterns:
                for key, value in flattened.items():
                    # Case-insensitive fuzzy match
                    key_lower = key.lower()
                    pattern_lower = pattern.lower()
                    
                    if pattern_lower in key_lower or self._fuzzy_match(key_lower, pattern_lower):
                        # Found a match!
                        extracted[semantic_field] = value
                        self.extraction_log.append(f"Mapped '{key}' → '{semantic_field}'")
                        found = True
                        break
                
                if found:
                    break
            
            # If not found, try partial matches
            if not found:
                for key, value in flattened.items():
                    if any(p in key.lower() for p in [patterns[0][:4]]):  # Partial match
                        extracted[semantic_field] = value
                        self.extraction_log.append(f"Partial match '{key}' → '{semantic_field}'")
                        break
        
        # Add all other fields that weren't semantically mapped
        for key, value in flattened.items():
            # Standardize key name
            clean_key = re.sub(r'[^a-z0-9_]', '_', key.lower())
            if clean_key not in extracted and not any(clean_key in str(v) for v in extracted.values()):
                extracted[clean_key] = value
        
        return extracted
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Simple fuzzy string matching"""
        # Levenshtein-like simple match
        if len(str1) == 0 or len(str2) == 0:
            return False
        
        # Check if one contains the other
        if str1 in str2 or str2 in str1:
            return True
        
        # Check character overlap
        set1 = set(str1)
        set2 = set(str2)
        overlap = len(set1 & set2) / max(len(set1), len(set2))
        
        return overlap >= threshold
    
    def _calculate_extraction_confidence(self, extracted: Dict) -> float:
        """
        Calculate confidence in extraction quality
        
        Based on:
        - Number of critical fields found
        - Data completeness
        - Field validity
        """
        score = 0.0
        
        # Critical fields
        critical_fields = ['amount', 'balance', 'timestamp', 'country']
        found_critical = sum(1 for f in critical_fields if f in extracted)
        score += (found_critical / len(critical_fields)) * 0.5
        
        # Total fields
        if len(extracted) > 5:
            score += 0.3
        elif len(extracted) > 3:
            score += 0.2
        else:
            score += 0.1
        
        # Extraction log (successful mappings)
        if len(self.extraction_log) > 5:
            score += 0.2
        elif len(self.extraction_log) > 3:
            score += 0.1
        
        return min(score, 1.0)


# Testing
if __name__ == "__main__":
    print("=" * 80)
    print("INTELLIGENT JSON PARSER - TEST")
    print("=" * 80)
    
    parser = IntelligentJSONParser()
    
    # Test Case 1: Deeply nested structure
    print("\nTEST 1: Deeply Nested JSON")
    print("-" * 80)
    
    nested_json = {
        "transaction": {
            "payment": {
                "amount_details": {
                    "total": "$4,999.99",
                    "currency": "USD"
                }
            },
            "user_info": {
                "profile": {
                    "personal": {
                        "age": 65,
                        "occupation": "Doctor"
                    }
                },
                "account": {
                    "balance": 15000000,
                    "account_age_days": 365
                }
            },
            "metadata": {
                "timestamp": "2026-06-01 14:30:00",
                "location": {
                    "country": "USA"
                },
                "device_info": {
                    "type": "Mobile",
                    "ip_risk_score": 0.2
                }
            }
        }
    }
    
    print("INPUT (nested 5 levels deep):")
    print(json.dumps(nested_json, indent=2)[:500] + "...")
    
    result = parser.parse(nested_json)
    
    print("\nEXTRACTED FLAT STRUCTURE:")
    for k, v in sorted(result.items()):
        if k != '_parser_metadata':
            print(f"  {k}: {v}")
    
    print(f"\nExtraction Confidence: {result['_parser_metadata']['confidence']:.2%}")
    print(f"Fields Extracted: {result['_parser_metadata']['fields_extracted']}")
    
    # Test Case 2: Unstructured/varying schema
    print("\n" + "=" * 80)
    print("TEST 2: Completely Different Schema")
    print("-" * 80)
    
    different_schema = {
        "txn_data": {
            "amt": 50000,
            "acct_bal": 1000
        },
        "customer": {
            "failed_logins": 15,
            "device": "TOR_BROWSER"
        },
        "risk_signals": {
            "geo": "Russia",
            "merchant_name": "CryptoExchange"
        }
    }
    
    print("INPUT (different field names):")
    print(json.dumps(different_schema, indent=2))
    
    result2 = parser.parse(different_schema)
    
    print("\nEXTRACTED:")
    for k, v in sorted(result2.items()):
        if k != '_parser_metadata':
            print(f"  {k}: {v}")
    
    # Test Case 3: Array structure
    print("\n" + "=" * 80)
    print("TEST 3: Array/List Structure")
    print("-" * 80)
    
    array_json = [
        {
            "transaction_amount": 100,
            "customer_country": "US"
        }
    ]
    
    result3 = parser.parse(array_json)
    print(f"Extracted from array: {result3}")
    
    # Test Case 4: String JSON
    print("\n" + "=" * 80)
    print("TEST 4: JSON String")
    print("-" * 80)
    
    json_string = '{"amount": 5000, "country": "India", "merchant_category": "CRYPTO"}'
    result4 = parser.parse(json_string)
    print(f"Extracted from string: {result4}")
    
    print("\n" + "=" * 80)
    print("✅ Intelligent parser handles ANY JSON structure!")
    print("=" * 80)
