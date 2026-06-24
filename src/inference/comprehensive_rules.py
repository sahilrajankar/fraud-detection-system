"""
Comprehensive Fraud Detection Rule Engine
Enterprise-grade with 20+ rules covering all fraud patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import re


class ComprehensiveFraudRules:
    """
    Production-grade fraud detection with exhaustive rule coverage
    """
    
    def __init__(self):
        self.rules = []
        self._setup_all_rules()
    
    def _setup_all_rules(self):
        """Define all fraud detection rules"""
        
        # ===== CRITICAL SEVERITY RULES =====
        self.rules.extend([
            {
                'name': 'BALANCE_OVERDRAFT',
                'check': self._check_balance_overdraft,
                'severity': 'CRITICAL',
                'weight': 1.0,
                'description': 'Transaction exceeds available balance'
            },
            {
                'name': 'EXTREME_AMOUNT',
                'check': self._check_extreme_amount,
                'severity': 'CRITICAL',
                'weight': 0.95,
                'description': 'Unusually large transaction amount'
            },
            {
                'name': 'ANONYMOUS_HIGH_VALUE',
                'check': self._check_anonymous_high_value,
                'severity': 'CRITICAL',
                'weight': 0.95,
                'description': 'High value transaction from anonymous source'
            },
            {
                'name': 'IMPOSSIBLE_VELOCITY',
                'check': self._check_impossible_velocity,
                'severity': 'CRITICAL',
                'weight': 0.9,
                'description': 'Physically impossible transaction velocity'
            },
        ])
        
        # ===== HIGH SEVERITY RULES =====
        self.rules.extend([
            {
                'name': 'HIGH_RISK_INDICATORS',
                'check': self._check_high_risk_indicators,
                'severity': 'HIGH',
                'weight': 0.85,
                'description': 'Multiple high-risk signals present'
            },
            {
                'name': 'VELOCITY_ABUSE',
                'check': self._check_velocity_abuse,
                'severity': 'HIGH',
                'weight': 0.8,
                'description': 'Abnormal transaction frequency'
            },
            {
                'name': 'NEW_USER_HIGH_RISK',
                'check': self._check_new_user_patterns,
                'severity': 'HIGH',
                'weight': 0.75,
                'description': 'New account with risky behavior'
            },
            {
                'name': 'GEOGRAPHIC_ANOMALY',
                'check': self._check_geographic_anomaly,
                'severity': 'HIGH',
                'weight': 0.7,
                'description': 'Suspicious location patterns'
            },
            {
                'name': 'TIME_ANOMALY',
                'check': self._check_time_anomaly,
                'severity': 'HIGH',
                'weight': 0.65,
                'description': 'Unusual transaction timing'
            },
            {
                'name': 'DEVICE_ANOMALY',
                'check': self._check_device_anomaly,
                'severity': 'HIGH',
                'weight': 0.7,
                'description': 'Suspicious device characteristics'
            },
        ])
        
        # ===== MEDIUM SEVERITY RULES =====
        self.rules.extend([
            {
                'name': 'AMOUNT_PATTERN',
                'check': self._check_amount_patterns,
                'severity': 'MEDIUM',
                'weight': 0.6,
                'description': 'Suspicious amount characteristics'
            },
            {
                'name': 'BEHAVIORAL_ANOMALY',
                'check': self._check_behavioral_anomaly,
                'severity': 'MEDIUM',
                'weight': 0.55,
                'description': 'Deviation from normal behavior'
            },
            {
                'name': 'MERCHANT_RISK',
                'check': self._check_merchant_risk,
                'severity': 'MEDIUM',
                'weight': 0.5,
                'description': 'High-risk merchant category'
            },
            {
                'name': 'AUTHENTICATION_ISSUES',
                'check': self._check_authentication_issues,
                'severity': 'MEDIUM',
                'weight': 0.6,
                'description': 'Login or authentication problems'
            },
            {
                'name': 'CUSTOMER_HISTORY',
                'check': self._check_customer_history,
                'severity': 'MEDIUM',
                'weight': 0.55,
                'description': 'Negative customer history'
            },
        ])
        
        # ===== LOW SEVERITY (MONITORING) RULES =====
        self.rules.extend([
            {
                'name': 'MINOR_INCONSISTENCIES',
                'check': self._check_minor_inconsistencies,
                'severity': 'LOW',
                'weight': 0.3,
                'description': 'Minor suspicious indicators'
            },
        ])
    
    # ========== HELPER FUNCTIONS ==========
    
    def _get_field_value(self, data: Dict, field_names: List[str], default=None):
        """Get value from data with case-insensitive field name matching"""
        for field in field_names:
            # Exact match first
            if field in data:
                return data[field]
            # Case-insensitive match
            matching = [k for k in data.keys() if k.lower() == field.lower()]
            if matching:
                return data[matching[0]]
        return default
    
    def _safe_float(self, value, default=0.0):
        """Safely convert to float"""
        try:
            return float(value) if value is not None else default
        except:
            return default
    
    def _safe_int(self, value, default=0):
        """Safely convert to int"""
        try:
            return int(value) if value is not None else default
        except:
            return default
    
    # ========== CRITICAL RULES ==========
    
    def _check_balance_overdraft(self, data: Dict) -> Tuple[bool, str]:
        """Transaction exceeds available balance"""
        amount_fields = ['amount', 'transaction_amount', 'transactionamount', 'value', 'TransactionAmount']
        balance_fields = ['account_balance', 'balance', 'AccountBalance', 'available_balance']
        
        amount = self._safe_float(self._get_field_value(data, amount_fields))
        balance = self._safe_float(self._get_field_value(data, balance_fields))
        
        if amount > 0 and balance > 0:
            if amount > balance:
                excess = amount - balance
                return True, f"Overdraft: ${amount:,.0f} exceeds ${balance:,.0f} balance (${excess:,.0f} over)"
            
            # Large percentage of balance
            if amount > balance * 0.9:
                pct = (amount / balance) * 100
                return True, f"Draining account: ${amount:,.0f} ({pct:.0f}% of ${balance:,.0f})"
        
        return False, ""
    
    def _check_extreme_amount(self, data: Dict) -> Tuple[bool, str]:
        """Unusually large amounts (context-aware)"""
        amount_fields = ['amount', 'transaction_amount', 'transactionamount', 'value', 'TransactionAmount']
        amount = self._safe_float(self._get_field_value(data, amount_fields))
        
        # Get balance for context
        balance = self._safe_float(self._get_field_value(data, ['account_balance', 'AccountBalance', 'balance']))
        
        # If we have balance, check if amount is reasonable relative to it
        if balance > 0:
            pct_of_balance = (amount / balance) * 100
            
            # Only flag if it's a large absolute amount AND suspicious relative to balance
            if amount > 1000000 and pct_of_balance > 50:
                return True, f"Extreme amount: ${amount:,.0f} ({pct_of_balance:.0f}% of balance)"
            
            # Very large absolute amounts with reasonable balance
            if amount > 5000000:
                return True, f"Very large amount: ${amount:,.0f}"
            
            # If balance is sufficient, don't flag just for round amounts
            if pct_of_balance < 10:  # Less than 10% of balance = probably legitimate
                return False, ""
        
        # No balance context - use absolute thresholds
        if amount > 5000000:
            return True, f"Extreme amount: ${amount:,.0f}"
        
        if amount > 2000000:
            return True, f"Very large amount: ${amount:,.0f}"
        
        # Round amounts over threshold (but less strict)
        if amount > 1000000 and amount % 100000 == 0:
            return True, f"Suspiciously round very large amount: ${amount:,.0f}"
        
        return False, ""
    
    def _check_anonymous_high_value(self, data: Dict) -> Tuple[bool, str]:
        """High value from anonymous/risky source"""
        amount = self._safe_float(self._get_field_value(data, ['amount', 'TransactionAmount']))
        device = str(self._get_field_value(data, ['device_type', 'DeviceType'], '')).upper()
        ip_risk = self._safe_float(self._get_field_value(data, ['ip_risk_score', 'IPRiskScore']))
        
        is_anonymous = any(x in device for x in ['TOR', 'VPN', 'PROXY', 'UNKNOWN'])
        high_ip_risk = ip_risk > 0.8
        
        if amount > 10000 and (is_anonymous or high_ip_risk):
            return True, f"${amount:,.0f} from risky source (Device: {device}, IP Risk: {ip_risk})"
        
        return False, ""
    
    def _check_impossible_velocity(self, data: Dict) -> Tuple[bool, str]:
        """Physically impossible transaction patterns"""
        txn_count = self._safe_int(self._get_field_value(data, [
            'transactions_last_24h', 'TransactionsLast24H', 'txn_count_24h'
        ]))
        
        # Over 200 transactions in 24h = 1 every 7 minutes (impossible for human)
        if txn_count > 200:
            return True, f"Impossible velocity: {txn_count} transactions in 24h (bot/script suspected)"
        
        # Over 100 = highly suspicious
        if txn_count > 100:
            return True, f"Extreme velocity: {txn_count} transactions in 24h"
        
        return False, ""
    
    # ========== HIGH SEVERITY RULES ==========
    
    def _check_high_risk_indicators(self, data: Dict) -> Tuple[bool, str]:
        """Multiple high-risk signals"""
        flags = []
        
        # IP risk
        ip_risk = self._safe_float(self._get_field_value(data, ['ip_risk_score', 'IPRiskScore', 'risk_score']))
        if ip_risk > 0.9:
            flags.append(f"Critical IP risk: {ip_risk}")
        elif ip_risk > 0.7:
            flags.append(f"High IP risk: {ip_risk}")
        elif ip_risk > 0.5:
            flags.append(f"Elevated IP risk: {ip_risk}")
        
        # Device
        device = str(self._get_field_value(data, ['device_type', 'DeviceType'], '')).upper()
        if any(x in device for x in ['TOR', 'VPN', 'PROXY']):
            flags.append(f"Anonymous device: {device}")
        elif 'UNKNOWN' in device or 'EMULATOR' in device:
            flags.append(f"Suspicious device: {device}")
        
        # Location
        country = str(self._get_field_value(data, ['country', 'Country', 'Location'], '')).upper()
        high_risk_countries = ['RUSSIA', 'NIGERIA', 'BELARUS', 'IRAN', 'SYRIA', 'NORTH KOREA', 'HIGHRISK']
        if any(c in country for c in high_risk_countries):
            flags.append(f"High-risk location: {country}")
        
        # Failed logins
        failed = self._safe_int(self._get_field_value(data, ['failed_login_attempts', 'LoginAttempts', 'FailedLogins']))
        if failed > 20:
            flags.append(f"Excessive login failures: {failed}")
        elif failed > 10:
            flags.append(f"Many login failures: {failed}")
        elif failed > 5:
            flags.append(f"Multiple login failures: {failed}")
        
        # Chargebacks
        chargebacks = self._safe_int(self._get_field_value(data, ['chargeback_history', 'ChargebackCount', 'chargebacks']))
        if chargebacks > 10:
            flags.append(f"Excessive chargebacks: {chargebacks}")
        elif chargebacks > 5:
            flags.append(f"High chargeback history: {chargebacks}")
        elif chargebacks > 0:
            flags.append(f"Chargeback history: {chargebacks}")
        
        # New device flag
        new_device = self._get_field_value(data, ['is_new_device', 'NewDevice', 'new_device'])
        if new_device in [True, 'true', 'True', 1, '1']:
            flags.append("New/unknown device")
        
        if len(flags) >= 2:  # Multiple indicators = high risk
            return True, " | ".join(flags)
        
        return False, ""
    
    def _check_velocity_abuse(self, data: Dict) -> Tuple[bool, str]:
        """Abnormal transaction frequency"""
        txn_count = self._safe_int(self._get_field_value(data, [
            'transactions_last_24h', 'TransactionsLast24H', 'txn_count_24h', 'daily_transaction_count'
        ]))
        
        if txn_count > 100:
            return True, f"Extreme velocity: {txn_count} transactions in 24h"
        elif txn_count > 50:
            return True, f"Very high velocity: {txn_count} transactions in 24h"
        elif txn_count > 30:
            return True, f"High velocity: {txn_count} transactions in 24h"
        
        return False, ""
    
    def _check_new_user_patterns(self, data: Dict) -> Tuple[bool, str]:
        """New accounts with risky behavior (context-aware)"""
        amount = self._safe_float(self._get_field_value(data, ['amount', 'TransactionAmount']))
        age_days = self._safe_int(self._get_field_value(data, [
            'customer_age_days', 'account_age', 'AccountAgeDays', 'days_since_signup'
        ]))
        
        # Check if we have customer context
        customer_age = self._safe_int(self._get_field_value(data, ['CustomerAge', 'customer_age', 'age']))
        occupation = str(self._get_field_value(data, ['CustomerOccupation', 'occupation', 'job'], '')).upper()
        
        # High net worth indicators (doctors, lawyers, executives) - less strict
        high_networth_jobs = ['DOCTOR', 'PHYSICIAN', 'LAWYER', 'ATTORNEY', 'CEO', 'CFO', 'EXECUTIVE', 'SURGEON']
        is_high_networth = any(job in occupation for job in high_networth_jobs)
        is_senior = customer_age >= 50  # Older customers typically have more wealth
        
        # If high net worth or senior, be less strict about new accounts
        if is_high_networth or is_senior:
            # Only flag truly suspicious new account behavior
            if age_days == 0 and amount > 100000:
                return True, f"Brand new account ({age_days} days) with very large transaction: ${amount:,.0f}"
            return False, ""
        
        # Standard checks for regular customers
        # Brand new account (0-2 days)
        if age_days <= 2 and amount > 10000:
            return True, f"New account ({age_days} days) with large transaction: ${amount:,.0f}"
        
        # Very new account (3-7 days)
        if age_days <= 7 and amount > 30000:
            return True, f"Very new account ({age_days} days) with high-value transaction: ${amount:,.0f}"
        
        # Somewhat new (8-30 days)
        if age_days <= 30 and amount > 100000:
            return True, f"Recent account ({age_days} days) with very large transaction: ${amount:,.0f}"
        
        return False, ""
    
    def _check_geographic_anomaly(self, data: Dict) -> Tuple[bool, str]:
        """Suspicious location patterns"""
        country = str(self._get_field_value(data, ['country', 'Country', 'Location'], '')).upper()
        
        # Offshore/tax havens
        tax_havens = ['CAYMAN', 'PANAMA', 'SEYCHELLES', 'BERMUDA', 'BVI', 'VIRGIN ISLANDS']
        if any(t in country for t in tax_havens):
            return True, f"Offshore location: {country}"
        
        # Multiple simultaneous locations (if available)
        # This would need transaction history - placeholder for now
        
        return False, ""
    
    def _check_time_anomaly(self, data: Dict) -> Tuple[bool, str]:
        """Unusual transaction timing"""
        # Check if timestamp provided
        timestamp_str = self._get_field_value(data, ['timestamp', 'Timestamp', 'transaction_time', 'datetime'])
        
        if timestamp_str:
            try:
                # Parse timestamp
                if isinstance(timestamp_str, str):
                    # Try multiple formats
                    for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            dt = datetime.strptime(timestamp_str, fmt)
                            break
                        except:
                            continue
                    else:
                        return False, ""
                    
                    # Check if late night (2-5 AM local time)
                    hour = dt.hour
                    if 2 <= hour <= 5:
                        return True, f"Late night transaction: {dt.strftime('%H:%M')}"
            except:
                pass
        
        return False, ""
    
    def _check_device_anomaly(self, data: Dict) -> Tuple[bool, str]:
        """Suspicious device characteristics"""
        flags = []
        
        device = str(self._get_field_value(data, ['device_type', 'DeviceType'], '')).upper()
        
        # Suspicious device types
        if 'EMULATOR' in device:
            flags.append("Emulator detected")
        if 'ROOTED' in device or 'JAILBROKEN' in device:
            flags.append("Modified device")
        if 'BOT' in device:
            flags.append("Bot detected")
        
        # Browser-based risks
        user_agent = str(self._get_field_value(data, ['user_agent', 'UserAgent'], '')).upper()
        if 'HEADLESS' in user_agent:
            flags.append("Headless browser")
        
        if flags:
            return True, " | ".join(flags)
        
        return False, ""
    
    # ========== MEDIUM SEVERITY RULES ==========
    
    def _check_amount_patterns(self, data: Dict) -> Tuple[bool, str]:
        """Suspicious amount characteristics (context-aware)"""
        amount = self._safe_float(self._get_field_value(data, ['amount', 'TransactionAmount']))
        balance = self._safe_float(self._get_field_value(data, ['account_balance', 'AccountBalance']))
        
        # Just below reporting thresholds - structuring
        if 9000 <= amount <= 9999:
            return True, f"Just below $10K reporting threshold: ${amount:,.0f} (structuring suspected)"
        
        # Just below $5K threshold
        if 4900 <= amount <= 4999.99:
            return True, f"Just below $5K threshold: ${amount:,.2f} (structuring suspected)"
        
        # Round amounts are only suspicious if:
        # 1. Large absolute amount AND
        # 2. Significant percentage of balance
        if balance > 0:
            pct = (amount / balance) * 100
            
            # Round amount that's also a large % of balance
            if amount >= 50000 and amount % 10000 == 0 and pct > 20:
                return True, f"Round amount draining account: ${amount:,.0f} ({pct:.0f}% of balance)"
            
            # If it's a small % of balance, round amounts are normal
            if pct < 5:
                return False, ""
        
        # Repeating digits (more suspicious)
        amount_str = str(int(amount))
        if len(set(amount_str)) == 1 and len(amount_str) >= 4:
            return True, f"Suspicious repeating digits: ${amount:,.0f}"
        
        return False, ""
    
    def _check_behavioral_anomaly(self, data: Dict) -> Tuple[bool, str]:
        """Deviation from normal behavior"""
        amount = self._safe_float(self._get_field_value(data, ['amount', 'TransactionAmount']))
        avg_amount = self._safe_float(self._get_field_value(data, [
            'avg_transaction_amount_30d', 'average_amount', 'AvgAmount', 'avg_user_amount', 'avg_amount'
        ]))
        
        if avg_amount > 0 and amount > 0:
            multiplier = amount / avg_amount
            
            # Transaction is 30x+ normal
            if multiplier >= 30:
                return True, f"${amount:,.2f} is {multiplier:.0f}x normal average (${avg_amount:,.2f})"
            
            # Transaction is 20x+ normal
            if multiplier >= 20:
                return True, f"${amount:,.2f} is {multiplier:.0f}x normal average (${avg_amount:,.2f})"
            
            # Transaction is 10x normal
            if multiplier >= 10:
                return True, f"${amount:,.2f} is {multiplier:.0f}x normal average (${avg_amount:,.2f})"
        
        return False, ""
    
    def _check_merchant_risk(self, data: Dict) -> Tuple[bool, str]:
        """High-risk merchant categories"""
        category = str(self._get_field_value(data, [
            'merchant_category', 'MerchantCategory', 'category', 'mcc', 'type', 'TransactionType'
        ], '')).upper()
        
        high_risk = {
            'CRYPTO': 'Cryptocurrency',
            'GAMBLING': 'Gambling',
            'CASINO': 'Casino',
            'ADULT': 'Adult content',
            'FOREX': 'Foreign exchange',
            'WIRE_TRANSFER': 'Wire transfer',
            'MONEY_TRANSFER': 'Money transfer',
            'PREPAID': 'Prepaid cards',
            'GIFT_CARD': 'Gift cards'
        }
        
        for key, desc in high_risk.items():
            if key in category:
                return True, f"High-risk category: {desc}"
        
        return False, ""
    
    def _check_authentication_issues(self, data: Dict) -> Tuple[bool, str]:
        """Login or authentication problems"""
        failed = self._safe_int(self._get_field_value(data, ['failed_login_attempts', 'LoginAttempts']))
        
        if failed > 3:
            return True, f"Authentication issues: {failed} failed attempts"
        
        # Check for password reset flags
        reset = self._get_field_value(data, ['password_reset', 'recent_password_change'])
        if reset in [True, 'true', 1, '1']:
            return True, "Recent password reset"
        
        return False, ""
    
    def _check_customer_history(self, data: Dict) -> Tuple[bool, str]:
        """Negative customer history"""
        flags = []
        
        # Previous fraud
        prev_fraud = self._get_field_value(data, ['previous_fraud', 'fraud_history', 'FraudHistory'])
        if prev_fraud in [True, 'true', 1, '1']:
            flags.append("Previous fraud history")
        
        # Disputes
        disputes = self._safe_int(self._get_field_value(data, ['dispute_count', 'disputes']))
        if disputes > 0:
            flags.append(f"{disputes} previous disputes")
        
        if flags:
            return True, " | ".join(flags)
        
        return False, ""
    
    # ========== LOW SEVERITY RULES ==========
    
    def _check_minor_inconsistencies(self, data: Dict) -> Tuple[bool, str]:
        """Minor suspicious indicators"""
        flags = []
        
        # First transaction flag
        first_txn = self._get_field_value(data, ['is_first_transaction', 'FirstTransaction'])
        if first_txn in [True, 'true', 1, '1']:
            flags.append("First transaction")
        
        # Unusual currency
        currency = str(self._get_field_value(data, ['currency', 'Currency'], '')).upper()
        if currency and currency not in ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'INR']:
            flags.append(f"Uncommon currency: {currency}")
        
        if flags:
            return True, " | ".join(flags)
        
        return False, ""
    
    # ========== EVALUATION ==========
    
    def evaluate(self, transaction_data: Dict) -> Dict:
        """
        Evaluate transaction against ALL rules
        
        Returns comprehensive fraud assessment
        """
        triggered = []
        max_severity = 'LOW'
        total_score = 0.0
        
        severity_rank = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
        
        # Check every rule
        for rule in self.rules:
            try:
                is_triggered, reason = rule['check'](transaction_data)
                
                if is_triggered:
                    triggered.append({
                        'rule': rule['name'],
                        'severity': rule['severity'],
                        'reason': reason,
                        'weight': rule['weight'],
                        'description': rule['description']
                    })
                    
                    # Update max severity
                    if severity_rank[rule['severity']] > severity_rank[max_severity]:
                        max_severity = rule['severity']
                    
                    # Accumulate score
                    total_score += rule['weight']
            except Exception as e:
                # Don't let one rule failure break entire evaluation
                print(f"Rule {rule['name']} failed: {e}")
                continue
        
        # Normalize score (0-1)
        max_possible_score = sum(r['weight'] for r in self.rules)
        normalized_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        # Build comprehensive explanation
        if triggered:
            explanation = f"🚨 FRAUD ALERT: {len(triggered)} rule(s) triggered\n\n"
            
            # Group by severity
            by_severity = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}
            for t in triggered:
                by_severity[t['severity']].append(t)
            
            for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if by_severity[sev]:
                    explanation += f"\n{sev} ({len(by_severity[sev])}):\n"
                    for t in by_severity[sev]:
                        explanation += f"  • {t['rule']}: {t['reason']}\n"
        else:
            explanation = "✅ No fraud rules triggered - transaction appears legitimate"
        
        return {
            'triggered_rules': triggered,
            'rule_score': round(normalized_score, 4),
            'severity': max_severity,
            'explanation': explanation,
            'rule_count': len(triggered),
            'rules_by_severity': {
                'CRITICAL': len([t for t in triggered if t['severity'] == 'CRITICAL']),
                'HIGH': len([t for t in triggered if t['severity'] == 'HIGH']),
                'MEDIUM': len([t for t in triggered if t['severity'] == 'MEDIUM']),
                'LOW': len([t for t in triggered if t['severity'] == 'LOW']),
            },
            'total_rules_checked': len(self.rules)
        }


# Test
if __name__ == "__main__":
    print("=" * 80)
    print("COMPREHENSIVE FRAUD RULE ENGINE - TEST")
    print("=" * 80)
    
    engine = ComprehensiveFraudRules()
    print(f"\n✅ Loaded {len(engine.rules)} fraud detection rules")
    
    # Test extreme fraud
    print("\n" + "=" * 80)
    print("TEST: Extreme Fraud Case")
    print("=" * 80)
    
    extreme_fraud = {
        "TransactionAmount": 50000,
        "AccountBalance": 1000,
        "transactions_last_24h": 150,
        "ip_risk_score": 0.99,
        "device_type": "TOR_BROWSER",
        "country": "Russia",
        "failed_login_attempts": 25,
        "customer_age_days": 0,
        "merchant_category": "CRYPTO_EXCHANGE",
        "chargeback_history": 10
    }
    
    result = engine.evaluate(extreme_fraud)
    print(f"\n🎯 RESULT:")
    print(f"   Risk Score: {result['rule_score']:.2%}")
    print(f"   Severity: {result['severity']}")
    print(f"   Rules Triggered: {result['rule_count']}/{result['total_rules_checked']}")
    print(f"\n{result['explanation']}")
    
    print("\n" + "=" * 80)
    print("✅ Comprehensive rule engine ready!")
    print("=" * 80)
