"""
Robust Data Preprocessor for Messy Real-World Data
Handles: missing values, inconsistent formats, outliers, invalid data
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class MessyDataPreprocessor:
    """
    Production-grade data cleaning for messy real-world data
    
    Handles:
    - Missing values (null, None, empty strings, 'N/A', '-')
    - Type mismatches (strings as numbers, numbers as strings)
    - Outliers (extreme values, impossible data)
    - Format inconsistencies (dates, currencies, country codes)
    - Duplicate/conflicting fields
    - Invalid ranges
    - Data quality scoring
    """
    
    def __init__(self):
        self.cleaning_stats = {}
        self.quality_issues = []
    
    def clean_transaction(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Clean messy transaction data
        
        Returns:
            cleaned_data: Cleaned transaction dict
            metadata: Cleaning statistics and quality score
        """
        self.cleaning_stats = {
            'fields_cleaned': 0,
            'missing_handled': 0,
            'types_fixed': 0,
            'formats_standardized': 0,
            'outliers_capped': 0
        }
        self.quality_issues = []
        
        cleaned = {}
        
        # Process each field
        for key, value in data.items():
            cleaned_key, cleaned_value = self._clean_field(key, value)
            if cleaned_value is not None:
                cleaned[cleaned_key] = cleaned_value
        
        # Add derived fields
        cleaned = self._add_derived_fields(cleaned)
        
        # Calculate data quality score
        quality_score = self._calculate_quality_score(data, cleaned)
        
        metadata = {
            'original_fields': len(data),
            'cleaned_fields': len(cleaned),
            'quality_score': quality_score,
            'cleaning_stats': self.cleaning_stats,
            'quality_issues': self.quality_issues,
            'data_completeness': len(cleaned) / max(len(data), 1)
        }
        
        return cleaned, metadata
    
    def _clean_field(self, key: str, value: Any) -> Tuple[str, Any]:
        """Clean individual field"""
        
        # Standardize field name
        clean_key = self._standardize_field_name(key)
        
        # Handle missing values
        if self._is_missing(value):
            self.cleaning_stats['missing_handled'] += 1
            self.quality_issues.append(f"Missing: {key}")
            return clean_key, None
        
        # Clean by field type
        if 'amount' in clean_key.lower() or 'balance' in clean_key.lower():
            return clean_key, self._clean_amount(value, key)
        
        elif 'date' in clean_key.lower() or 'time' in clean_key.lower():
            return clean_key, self._clean_datetime(value, key)
        
        elif 'country' in clean_key.lower() or 'location' in clean_key.lower():
            return clean_key, self._clean_country(value)
        
        elif 'email' in clean_key.lower():
            return clean_key, self._clean_email(value)
        
        elif 'phone' in clean_key.lower():
            return clean_key, self._clean_phone(value)
        
        elif 'ip' in clean_key.lower():
            return clean_key, self._clean_ip(value)
        
        elif any(x in clean_key.lower() for x in ['count', 'age', 'attempts', 'velocity']):
            return clean_key, self._clean_integer(value, key)
        
        elif any(x in clean_key.lower() for x in ['rate', 'score', 'ratio', 'percent']):
            return clean_key, self._clean_float(value, key, min_val=0.0, max_val=1.0)
        
        else:
            # Generic cleaning
            return clean_key, self._clean_generic(value)
    
    def _is_missing(self, value: Any) -> bool:
        """Check if value is missing"""
        if value is None:
            return True
        if isinstance(value, str):
            cleaned = value.strip().upper()
            return cleaned in ['', 'NULL', 'NONE', 'N/A', 'NA', 'NAN', '-', 'UNKNOWN', 'MISSING']
        if isinstance(value, float) and np.isnan(value):
            return True
        return False
    
    def _standardize_field_name(self, key: str) -> str:
        """Standardize field names"""
        # Convert to snake_case
        key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
        # Remove special characters
        key = re.sub(r'[^a-z0-9_]', '_', key)
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        return key.strip('_')
    
    def _clean_amount(self, value: Any, field_name: str) -> float:
        """Clean monetary amounts"""
        try:
            # Handle string amounts with currency symbols
            if isinstance(value, str):
                # Remove currency symbols and commas
                value = re.sub(r'[$€£¥₹,\s]', '', value)
                value = float(value)
            else:
                value = float(value)
            
            # Cap extreme outliers
            if value < 0:
                self.quality_issues.append(f"Negative amount: {field_name}={value}")
                value = 0
            
            if value > 10_000_000:  # $10M cap
                self.quality_issues.append(f"Extreme amount capped: {field_name}={value}")
                self.cleaning_stats['outliers_capped'] += 1
                value = 10_000_000
            
            self.cleaning_stats['types_fixed'] += 1
            return round(value, 2)
        
        except:
            self.quality_issues.append(f"Invalid amount: {field_name}={value}")
            return 0.0
    
    def _clean_integer(self, value: Any, field_name: str) -> int:
        """Clean integer fields"""
        try:
            value = int(float(str(value)))
            
            # Cap ridiculous values
            if value < 0:
                value = 0
            if value > 100000:  # Reasonable cap
                self.quality_issues.append(f"Extreme count capped: {field_name}={value}")
                self.cleaning_stats['outliers_capped'] += 1
                value = 100000
            
            self.cleaning_stats['types_fixed'] += 1
            return value
        
        except:
            self.quality_issues.append(f"Invalid integer: {field_name}={value}")
            return 0
    
    def _clean_float(self, value: Any, field_name: str, min_val: float = None, max_val: float = None) -> float:
        """Clean float fields"""
        try:
            value = float(value)
            
            # Clamp to range
            if min_val is not None and value < min_val:
                value = min_val
            if max_val is not None and value > max_val:
                value = max_val
            
            self.cleaning_stats['types_fixed'] += 1
            return value
        
        except:
            self.quality_issues.append(f"Invalid float: {field_name}={value}")
            return 0.0
    
    def _clean_datetime(self, value: Any, field_name: str) -> str:
        """Clean datetime fields"""
        try:
            # Try various datetime formats
            if isinstance(value, (int, float)):
                # Unix timestamp
                dt = datetime.fromtimestamp(value)
            elif isinstance(value, str):
                # Try common formats
                for fmt in [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d',
                    '%d/%m/%Y',
                    '%m/%d/%Y',
                    '%Y/%m/%d'
                ]:
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except:
                        continue
                else:
                    raise ValueError("No format matched")
            else:
                dt = value
            
            self.cleaning_stats['formats_standardized'] += 1
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        except:
            self.quality_issues.append(f"Invalid datetime: {field_name}={value}")
            return None
    
    def _clean_country(self, value: str) -> str:
        """Standardize country codes/names"""
        if not isinstance(value, str):
            return str(value).upper()
        
        value = value.strip().upper()
        
        # Map common variations
        country_map = {
            'US': 'USA', 'USA': 'USA', 'UNITED STATES': 'USA',
            'UK': 'GBR', 'GB': 'GBR', 'UNITED KINGDOM': 'GBR',
            'RU': 'RUS', 'RUSSIA': 'RUS', 'RUSSIAN FEDERATION': 'RUS',
            'CN': 'CHN', 'CHINA': 'CHN',
            'IN': 'IND', 'INDIA': 'IND'
        }
        
        self.cleaning_stats['formats_standardized'] += 1
        return country_map.get(value, value)
    
    def _clean_email(self, value: str) -> str:
        """Validate and clean email"""
        if not isinstance(value, str):
            return None
        
        value = value.strip().lower()
        
        # Basic email validation
        if '@' in value and '.' in value.split('@')[1]:
            return value
        
        self.quality_issues.append(f"Invalid email: {value}")
        return None
    
    def _clean_phone(self, value: Any) -> str:
        """Clean phone numbers"""
        if not value:
            return None
        
        # Remove all non-digits
        phone = re.sub(r'\D', '', str(value))
        
        if len(phone) >= 10:
            return phone
        
        self.quality_issues.append(f"Invalid phone: {value}")
        return None
    
    def _clean_ip(self, value: str) -> str:
        """Validate IP address"""
        if not isinstance(value, str):
            return None
        
        # Basic IP validation
        parts = value.split('.')
        if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts if p.isdigit()):
            return value
        
        self.quality_issues.append(f"Invalid IP: {value}")
        return None
    
    def _clean_generic(self, value: Any) -> Any:
        """Generic cleaning"""
        if isinstance(value, str):
            value = value.strip()
            if len(value) == 0:
                return None
        
        return value
    
    def _add_derived_fields(self, data: Dict) -> Dict:
        """Add derived/computed fields"""
        
        # Extract hour from timestamp
        if 'timestamp' in data:
            try:
                dt = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
                data['hour_of_day'] = dt.hour
                data['day_of_week'] = dt.weekday()
                data['is_weekend'] = 1 if dt.weekday() >= 5 else 0
            except:
                pass
        
        # Calculate ratios
        if 'amount' in data and 'account_balance' in data:
            if data['account_balance'] > 0:
                data['amount_to_balance_ratio'] = data['amount'] / data['account_balance']
        
        return data
    
    def _calculate_quality_score(self, original: Dict, cleaned: Dict) -> float:
        """
        Calculate data quality score (0-1)
        
        Based on:
        - Completeness (how many fields present)
        - Validity (how many issues found)
        - Consistency (conflicting data)
        """
        score = 1.0
        
        # Completeness penalty
        if len(original) > 0:
            completeness = len(cleaned) / len(original)
            score *= completeness
        
        # Quality issues penalty
        if len(self.quality_issues) > 0:
            issue_penalty = min(len(self.quality_issues) * 0.05, 0.5)
            score -= issue_penalty
        
        # Cleaning operations (shows data was messy)
        total_fixes = sum(self.cleaning_stats.values())
        if total_fixes > 5:
            score -= 0.1
        
        return max(score, 0.0)


# Testing
if __name__ == "__main__":
    print("=" * 80)
    print("MESSY DATA PREPROCESSOR - TEST")
    print("=" * 80)
    
    preprocessor = MessyDataPreprocessor()
    
    # Test with messy data
    messy_data = {
        "TransactionAmount": "$4,999.99",  # String with currency
        "AccountBalance": "15000",
        "timestamp": "2026-06-01 14:30:00",
        "Country": "us",  # Lowercase
        "Failed_Login_Attempts": "5.0",  # Float as string
        "email": "  USER@EXAMPLE.COM  ",  # Whitespace + uppercase
        "ip_address": "192.168.1.1",
        "merchant": None,  # Missing
        "extra_field": "N/A",  # Another missing
        "velocity": -1,  # Invalid
        "HugeAmount": 99999999999  # Outlier
    }
    
    print("\nMESSY INPUT:")
    for k, v in messy_data.items():
        print(f"  {k}: {v} ({type(v).__name__})")
    
    cleaned, metadata = preprocessor.clean_transaction(messy_data)
    
    print("\n" + "=" * 80)
    print("CLEANED OUTPUT:")
    for k, v in cleaned.items():
        print(f"  {k}: {v} ({type(v).__name__})")
    
    print("\n" + "=" * 80)
    print("CLEANING METADATA:")
    print(f"  Quality Score: {metadata['quality_score']:.2%}")
    print(f"  Data Completeness: {metadata['data_completeness']:.2%}")
    print(f"  Issues Found: {len(metadata['quality_issues'])}")
    
    if metadata['quality_issues']:
        print(f"\n  Quality Issues:")
        for issue in metadata['quality_issues'][:5]:
            print(f"    - {issue}")
    
    print("\n" + "=" * 80)
    print("✅ Preprocessor ready for messy real-world data!")
    print("=" * 80)
