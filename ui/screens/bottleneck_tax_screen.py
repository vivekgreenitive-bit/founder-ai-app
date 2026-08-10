"""
ui/screens/bottleneck_tax_screen.py
Interactive Founder Micromanagement Tax Calculator Screen.
Calculates exact $ revenue leak/month and enables 1-click delegation AI diagnosis.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QSlider, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from agents.bottleneck_agent import BottleneckAgent


class BottleneckTaxScreen(QWidget):
    """
    Interactive Bottleneck Tax Calculator UI Screen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.agent = BottleneckAgent()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QLabel("💰 Founder Bottleneck Tax Calculator")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        root.addWidget(header)

        sub = QLabel(
            "Calculate the exact dollar revenue lost per month due to the Founder Micromanagement Tax. "
            "Discover how much leverage you unlock by delegating low-impact operational tasks."
        )
        sub.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Main Input & Output Layout
        body = QHBoxLayout()
        body.setSpacing(20)

        # Left Column: Inputs Card
        input_card = QFrame()
        input_card.setStyleSheet("background: #ffffff; border: 1px solid #ccebd7; border-radius: 12px; padding: 20px;")
        ic_layout = QVBoxLayout(input_card)
        ic_layout.setSpacing(14)

        ic_title = QLabel("Input Operational Numbers")
        ic_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        ic_title.setStyleSheet("color: #1a7a3c;")
        ic_layout.addWidget(ic_title)

        # 1. Target Hourly Rate ($/hr)
        ic_layout.addWidget(QLabel("Target Founder Hourly Value ($/hr):"))
        self.rate_input = QLineEdit("150")
        self.rate_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: bold;")
        self.rate_input.textChanged.connect(self._recalculate)
        ic_layout.addWidget(self.rate_input)

        # 2. Hours spent on low leverage tasks / week
        ic_layout.addWidget(QLabel("Hours Spent on Low-Leverage Tasks / Week:"))
        self.hours_input = QLineEdit("15")
        self.hours_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: bold;")
        self.hours_input.textChanged.connect(self._recalculate)
        ic_layout.addWidget(self.hours_input)

        # 3. Monthly Revenue ($)
        ic_layout.addWidget(QLabel("Current Monthly Revenue ($):"))
        self.rev_input = QLineEdit("30000")
        self.rev_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-weight: bold;")
        self.rev_input.textChanged.connect(self._recalculate)
        ic_layout.addWidget(self.rev_input)

        ic_layout.addStretch()
        body.addWidget(input_card, stretch=1)

        # Right Column: Output Results Card
        self.result_card = QFrame()
        self.result_card.setStyleSheet("background: #fef2f2; border: 2px solid #fca5a5; border-radius: 12px; padding: 24px;")
        rc_layout = QVBoxLayout(self.result_card)
        rc_layout.setSpacing(12)

        rc_title = QLabel("ESTIMATED FINANCIAL LEAK")
        rc_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        rc_title.setStyleSheet("color: #991b1b; letter-spacing: 1px;")
        rc_layout.addWidget(rc_title)

        self.monthly_tax_lbl = QLabel("$9,742.50 / month")
        self.monthly_tax_lbl.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.monthly_tax_lbl.setStyleSheet("color: #b91c1c;")
        rc_layout.addWidget(self.monthly_tax_lbl)

        self.annual_tax_lbl = QLabel("Equivalent to $116,910 / year in lost capacity")
        self.annual_tax_lbl.setStyleSheet("color: #991b1b; font-size: 11pt; font-weight: bold;")
        rc_layout.addWidget(self.annual_tax_lbl)

        self.leak_ratio_lbl = QLabel("Tax Severity: HIGH (32.5% of Monthly Revenue)")
        self.leak_ratio_lbl.setStyleSheet("color: #7f1d1d; font-size: 10pt; font-weight: 500;")
        rc_layout.addWidget(self.leak_ratio_lbl)

        rc_layout.addStretch()

        # Action CTA Button
        self.action_btn = QPushButton("⚡ Generate AI Delegation Plan ($9.7k recovery)")
        self.action_btn.setFixedHeight(44)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10.5pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        self.action_btn.clicked.connect(self._run_delegation_plan)
        rc_layout.addWidget(self.action_btn)

        body.addWidget(self.result_card, stretch=1)
        root.addLayout(body)

        self._recalculate()

    def _recalculate(self):
        try:
            rate = float(self.rate_input.text().strip() or "0")
            hours = float(self.hours_input.text().strip() or "0")
            rev = float(self.rev_input.text().strip() or "0")

            res = self.agent.calculate_tax(rate, hours, rev)

            m_tax = res["monthly_tax"]
            a_tax = res["annual_tax"]
            ratio = res["leak_ratio_pct"]
            sev = res["severity"]

            self.monthly_tax_lbl.setText(f"${m_tax:,.2f} / month")
            self.annual_tax_lbl.setText(f"Equivalent to ${a_tax:,.2f} / year in lost capacity")
            self.leak_ratio_lbl.setText(f"Tax Severity: {sev} ({ratio}% of Revenue)")

            self.action_btn.setText(f"⚡ Generate AI Delegation Plan (${m_tax:,.0f} recovery)")
        except Exception:
            pass

    def _run_delegation_plan(self):
        if self.main_app and hasattr(self.main_app, "switch_to_diagnose"):
            hours = self.hours_input.text().strip()
            rate = self.rate_input.text().strip()
            prompt = f"I am spending {hours} hours per week on low-leverage operational tasks (Target Rate: ${rate}/hr). Generate a 3-step AI & team delegation plan to recover this time using the ADMINS ER framework."
            if hasattr(self.main_app, "query_input"):
                self.main_app.query_input.setPlainText(prompt)
            self.main_app.switch_to_diagnose()
