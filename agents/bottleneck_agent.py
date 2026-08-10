"""
agents/bottleneck_agent.py
Calculates Founder Micromanagement Tax ($ loss/month) and identifies primary leakage domain.
"""
from typing import Dict, Any

class BottleneckAgent:
    """
    Quantifies the financial leak caused by founder micromanagement and low-leverage work.
    """
    def __init__(self, llm: Any = None):
        self.llm = llm

    def calculate_tax(self, hourly_rate: float, hours_per_week: float, monthly_revenue: float) -> Dict[str, Any]:
        """
        Calculates monthly and annual founder tax based on hourly rate and low-leverage hours.
        """
        hours_per_month = hours_per_week * 4.33
        monthly_tax = hours_per_month * hourly_rate
        annual_tax = monthly_tax * 12
        
        leak_ratio = (monthly_tax / monthly_revenue * 100) if monthly_revenue > 0 else 0.0

        if leak_ratio > 30:
            severity = "CRITICAL"
        elif leak_ratio > 15:
            severity = "HIGH"
        elif leak_ratio > 5:
            severity = "MODERATE"
        else:
            severity = "LOW"

        return {
            "hourly_rate": hourly_rate,
            "hours_per_week": hours_per_week,
            "monthly_tax": round(monthly_tax, 2),
            "annual_tax": round(annual_tax, 2),
            "leak_ratio_pct": round(leak_ratio, 1),
            "severity": severity,
            "hours_saved_target": round(hours_per_week * 0.7, 1)  # 70% delegation goal
        }

    def analyze_domain_bottlenecks(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Evaluates 5-domain questionnaire answers to pinpoint the #1 bottleneck.
        Domains: Sales/Revenue, Product/Fit, Operations, Delegation, Cashflow
        """
        scores = {
            "Delegation & Founder Dependency": 0,
            "Sales & Revenue Conversion": 0,
            "Product Retention & Churn": 0,
            "Operations & Process Lock": 0,
            "Cashflow & Runway": 0
        }

        if answers.get("q1") == "yes":  # Spending >15 hrs on ops
            scores["Delegation & Founder Dependency"] += 40
        if answers.get("q2") == "yes":  # Work stops if founder away 3 days
            scores["Delegation & Founder Dependency"] += 40
            scores["Operations & Process Lock"] += 20
        if answers.get("q3") == "yes":  # Leads stall in pipeline
            scores["Sales & Revenue Conversion"] += 50
        if answers.get("q4") == "yes":  # Customer churn within 90 days
            scores["Product Retention & Churn"] += 50
        if answers.get("q5") == "yes":  # Runway < 6 months
            scores["Cashflow & Runway"] += 50

        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_bottleneck, max_score = sorted_domains[0]

        # Recommend framework based on bottleneck
        fw_map = {
            "Delegation & Founder Dependency": "ADMINS ER",
            "Sales & Revenue Conversion": "RUN DCMS ER",
            "Product Retention & Churn": "PFA SAAS SME",
            "Operations & Process Lock": "PS ERP",
            "Cashflow & Runway": "OKS REC SME"
        }

        return {
            "primary_bottleneck": primary_bottleneck,
            "severity_score": max_score,
            "recommended_framework": fw_map.get(primary_bottleneck, "ECG KISS"),
            "domain_scores": scores
        }
