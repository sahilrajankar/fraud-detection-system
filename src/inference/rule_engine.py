"""
Rule-Based Fraud Detection Engine
Complements ML model with business logic
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class FraudRuleEngine:
    """
    Business rules for fraud detection
    Works BEFORE ML model to catch obvious fraud
    """
    
    def __init__(self):
        self.rules = []
        self._setup_rules()
    
    def _setup_rules(self):
        """Define fraud detection rules"""
        
        # Rule 1: Suspicious amount patterns
        self.rules.append({
            'name': 'EXTREME_AMOUNT',
            'check': self._check_extreme_amount,
            'severity': 'CRITICAL',
            'weight': 0.9
        })
        
        # Rule 2: High-risk indicators
        self.rules.append({
            'name': 'HIGH_RISK_INDICATORS',
            'check': self._check_high_risk_indicators,
            'severity': 'HIGH',
            'weight': 0.8
        })
        
        # Rule 3: Velocity checks
        self.rules.append({
            'name': 'VELOCITY_ABUSE',
            'check': self._check_velocity,
            'severity': 'HIGH',
            'weight': 0.7
        })
        
        # Rule 4: New user with large transaction
        self.rules.append({
            'name': 'NEW_USER_HIGH_VALUE',
            'check': self._check_new_user_risk,
            'severity': 'MEDIUM',
            'weight': 0.6
        })
        
        # Rule 6: Balance vs transaction amount
        self.rules.append({
            'name': 'BALANCE_MISMATCH',
            'check': self._check_balance_mismatch,
            'severity': 'CRITICAL',
            'weight': 0.95
        })
    
    def _check_extreme_amount(self, data: Dict) -> Tuple[bool, str]:
        """Check for suspiciously large amounts"""
        # Try multiple possible field names
        amount_fields = ['amount', 'transaction_amount', 'transactionamount', 'value', 'amt', 'TransactionAmount']
        
        for field in amount_fields:
            # Case-insensitive search
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                amount = float(data[matching[0]])
                
                # Extremely large amount
                if amount > 1000000:  # Over $1M
                    return True, f"Extreme amount: ${amount:,.0f}"
                
                # Round suspicious amount
                if amount > 100000 and amount % 1000 == 0:
                    return True, f"Suspiciously round large amount: ${amount:,.0f}"
        
        return False, ""
    
    def _check_high_risk_indicators(self, data: Dict) -> Tuple[bool, str]:
        """Check for high-risk indicators"""
        flags = []
        
        # IP risk score (multiple field names)
        ip_fields = ['ip_risk_score', 'iprisk', 'risk_score', 'ip_score']
        for field in ip_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                score = float(data[matching[0]])
                if score > 0.8:
                    flags.append(f"Very high IP risk: {score}")
                elif score > 0.6:
                    flags.append(f"Elevated IP risk: {score}")
                break
        
        # TOR/VPN usage
        device = str(data.get('device_type', data.get('DeviceType', ''))).upper()
        if any(x in device for x in ['TOR', 'VPN', 'PROXY', 'UNKNOWN']):
            flags.append(f"Anonymous device: {device}")
        
        # High-risk country (allow common countries)
        country = str(data.get('country', data.get('Country', data.get('Location', '')))).upper()
        high_risk_countries = ['RUSSIA', 'NIGERIA', 'HIGHRISK', 'UNKNOWN', 'BELARUS', 'IRAN', 'SYRIA']
        if any(c in country for c in high_risk_countries):
            flags.append(f"High-risk country: {country}")
        
        # Failed login attempts (multiple field names)
        login_fields = ['failed_login_attempts', 'loginattempts', 'login_attempts', 'LoginAttempts', 'FailedLogins']
        for field in login_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                attempts = int(data[matching[0]])
                if attempts > 20:
                    flags.append(f"Excessive failed logins: {attempts}")
                elif attempts > 5:
                    flags.append(f"Multiple failed logins: {attempts}")
                break
        
        # Chargeback history
        chargeback_fields = ['chargeback_history', 'chargebacks', 'ChargebackCount']
        for field in chargeback_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                chargebacks = int(data[matching[0]])
                if chargebacks > 5:
                    flags.append(f"High chargeback history: {chargebacks}")
                elif chargebacks > 0:
                    flags.append(f"Chargeback history: {chargebacks}")
                break
        
        if flags:
            return True, " | ".join(flags)
        
        return False, ""
    
    def _check_velocity(self, data: Dict) -> Tuple[bool, str]:
        """Check for velocity abuse"""
        
        # Transactions per day (multiple field names)
        velocity_fields = ['transactions_last_24h', 'transactionslast24h', 'TransactionsLast24H', 'txn_count_24h', 'daily_transaction_count']
        
        for field in velocity_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                txn_count = int(data[matching[0]])
                if txn_count > 100:
                    return True, f"Extreme velocity: {txn_count} transactions in 24h"
                elif txn_count > 50:
                    return True, f"High velocity: {txn_count} transactions in 24h"
                elif txn_count > 30:
                    return True, f"Elevated velocity: {txn_count} transactions in 24h"
                break
        
        return False, ""
    
    def _check_new_user_risk(self, data: Dict) -> Tuple[bool, str]:
        """New users with large transactions"""
        
        # Get amount
        amount = None
        for field in ['amount', 'transaction_amount', 'value']:
            if field in data:
                amount = float(data[field])
                break
        
        # Get customer age
        customer_age = None
        for field in ['customer_age_days', 'account_age', 'days_since_signup']:
            if field in data:
                customer_age = int(data[field])
                break
        
        if amount and customer_age is not None:
            # New user (< 7 days) with large transaction
            if customer_age < 7 and amount > 10000:
                return True, f"New user ({customer_age} days) with large amount: ${amount:,.0f}"
        
        return False, ""
    
    def _check_risky_category(self, data: Dict) -> Tuple[bool, str]:
        """Check for high-risk merchant categories"""
        
        category_fields = ['merchant_category', 'category', 'mcc', 'type']
        high_risk = ['CRYPTO', 'GAMBLING', 'ADULT', 'FOREX', 'WIRE_TRANSFER']
        
        for field in category_fields:
            if field in data:
                value = str(data[field]).upper()
                for risk in high_risk:
                    if risk in value:
                        return True, f"High-risk category: {data[field]}"
        
        return False, ""
    
    def _check_balance_mismatch(self, data: Dict) -> Tuple[bool, str]:
        """Check if transaction amount exceeds account balance"""
        
        # Get transaction amount
        amount = None
        amount_fields = ['amount', 'transaction_amount', 'transactionamount', 'TransactionAmount', 'value']
        for field in amount_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                amount = float(data[matching[0]])
                break
        
        # Get account balance
        balance = None
        balance_fields = ['account_balance', 'balance', 'AccountBalance', 'available_balance', 'current_balance']
        for field in balance_fields:
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                balance = float(data[matching[0]])
                break
        
        if amount is not None and balance is not None:
            # Transaction exceeds balance (overdraft/fraud)
            if amount > balance:
                excess = amount - balance
                return True, f"Transaction ${amount:,.0f} exceeds balance ${balance:,.0f} (overdraft: ${excess:,.0f})"
            
            # Transaction is >80% of balance (suspicious for withdrawal)
            if amount > balance * 0.8:
                pct = (amount / balance) * 100
                return True, f"Large withdrawal: ${amount:,.0f} ({pct:.0f}% of ${balance:,.0f} balance)"
        
        return False, ""
    
    def evaluate(self, transaction_data: Dict) -> Dict:
        """
        Evaluate transaction against all rules
        
        Returns:
            {
                'triggered_rules': [...],
                'rule_score': 0.0-1.0,
                'severity': 'LOW'|'MEDIUM'|'HIGH'|'CRITICAL',
                'explanation': '...'
            }
        """
        triggered = []
        max_severity = 'LOW'
        total_score = 0.0
        
        severity_rank = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
        
        # Check each rule
        for rule in self.rules:
            is_triggered, reason = rule['check'](transaction_data)
            
            if is_triggered:
                triggered.append({
                    'rule': rule['name'],
                    'severity': rule['severity'],
                    'reason': reason,
                    'weight': rule['weight']
                })
                
                # Update max severity
                if severity_rank[rule['severity']] > severity_rank[max_severity]:
                    max_severity = rule['severity']
                
                # Accumulate score
                total_score += rule['weight']
        
        # Normalize score (0-1)
        max_possible_score = sum(r['weight'] for r in self.rules)
        normalized_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Build explanation
        if triggered:
            explanation = f"Triggered {len(triggered)} fraud rule(s): " + \
                         "; ".join([f"{t['rule']} ({t['reason']})" for t in triggered])
        else:
            explanation = "No fraud rules triggered"
        
        return {
            'triggered_rules': triggered,
            'rule_score': round(normalized_score, 4),
            'severity': max_severity,
            'explanation': explanation,
            'rule_count': len(triggered)
        }


# Test
if __name__ == "__main__":
    print("=" * 80)
    print("Rule-Based Fraud Detection Engine - TEST")
    print("=" * 80)
    
    engine = FraudRuleEngine()
    
    # Test 1: Obvious fraud
    print("\nTEST 1: Obvious Fraud")
    fraud_txn = {
        "amount": 9999999,
        "currency": "USD",
        "transaction_type": "WIRE_TRANSFER",
        "customer_age_days": 0,
        "merchant_category": "CRYPTO_EXCHANGE",
        "country": "Russia",
        "device_type": "TOR_BROWSER",
        "ip_risk_score": 1.0,
        "failed_login_attempts": 35,
        "transactions_last_24h": 250,
        "chargeback_history": 15
    }
    
    result = engine.evaluate(fraud_txn)
    print(f"Rule Score: {result['rule_score']:.2f}")
    print(f"Severity: {result['severity']}")
    print(f"Triggered: {result['rule_count']} rules")
    print(f"Explanation: {result['explanation']}")
    
    # Test 2: Clean transaction
    print("\n" + "=" * 80)
    print("TEST 2: Clean Transaction")
    clean_txn = {
        "amount": 49.99,
        "customer_age_days": 365,
        "merchant_category": "RETAIL",
        "country": "US",
        "device_type": "Mobile",
        "ip_risk_score": 0.1,
        "failed_login_attempts": 0,
        "transactions_last_24h": 2
    }
    
    result = engine.evaluate(clean_txn)
    print(f"Rule Score: {result['rule_score']:.2f}")
    print(f"Severity: {result['severity']}")
    print(f"Triggered: {result['rule_count']} rules")
    print(f"Explanation: {result['explanation']}")
    
    print("\n" + "=" * 80)
    print("✅ Rule engine works!")
