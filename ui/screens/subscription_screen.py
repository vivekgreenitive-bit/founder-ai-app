from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QMessageBox, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from services.entitlement_service import EntitlementService
from providers.razorpay_provider import RazorpayPaymentProvider
import os
import sys

class SubscriptionBillingDialog(QDialog):
    """
    Dedicated Production Subscription & Billing Screen.
    Displays Current Plan, Status, Price, Feature Entitlements, and Live Razorpay Checkout Trigger.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Subscription & Billing")
        self.setFixedSize(560, 480)
        self.entitlement_service = EntitlementService()
        self.razorpay = RazorpayPaymentProvider()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header
        head_title = QLabel("💳 Subscription & Billing")
        head_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        head_title.setStyleSheet("color: #0f2318;")
        root.addWidget(head_title)

        # Current Plan Overview Card
        plan_card = QFrame()
        current_plan = self.entitlement_service.get_current_plan()
        is_pro = self.entitlement_service.is_pro()

        plan_card.setStyleSheet(f"""
            QFrame {{
                background-color: {"#f3e8ff" if is_pro else "#ffffff"};
                border: 1px solid {"#d8b4fe" if is_pro else "#ccebd7"};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        pc_layout = QVBoxLayout(plan_card)
        pc_layout.setSpacing(8)

        status_row = QHBoxLayout()
        plan_name = QLabel(f"CURRENT PLAN: Founder AI {current_plan}")
        plan_name.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        plan_name.setStyleSheet(f"color: {'#6b21a8' if is_pro else '#1a7a3c'};")
        status_row.addWidget(plan_name, stretch=1)

        badge_lbl = QLabel("ACTIVE" if is_pro else "FREE STARTER")
        badge_lbl.setStyleSheet(
            "background: #7c3aed; color: white; font-weight: bold; font-size: 8pt; padding: 3px 8px; border-radius: 10px;"
            if is_pro else
            "background: #e2f5ea; color: #1a7a3c; font-weight: bold; font-size: 8pt; padding: 3px 8px; border-radius: 10px;"
        )
        status_row.addWidget(badge_lbl)
        pc_layout.addLayout(status_row)

        price_lbl = QLabel("$49 / month (₹3,999/mo)" if is_pro else "$0 / month")
        price_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        price_lbl.setStyleSheet("color: #2d4536;")
        pc_layout.addWidget(price_lbl)

        root.addWidget(plan_card)

        # Plan Inclusions List
        inc_title = QLabel("YOUR PLAN INCLUDES:")
        inc_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        inc_title.setStyleSheet("color: #4b6b5a; letter-spacing: 1px;")
        root.addWidget(inc_title)

        inc_box = QFrame()
        inc_box.setStyleSheet("background: #ffffff; border: 1px solid #ebf7f0; border-radius: 8px; padding: 14px;")
        ib_layout = QVBoxLayout(inc_box)
        ib_layout.setSpacing(6)

        features = [
            ("✓ 2 Core Founder Frameworks (ECG KISS, SLR CAMERAS)", True),
            ("✓ Local Offline AI Reasoning (Llama-3.2-3B)", True),
            ("✓ Unlimited 13 Founder Frameworks", is_pro),
            ("✓ Google Gemini 1.5 Pro Cloud Reasoning", is_pro),
            ("✓ Customer Intelligence & Competitor Analysis", is_pro),
            ("✓ Decision Verification & Evidence Validation", is_pro),
            ("✓ Governed Agentic Payments Execution", is_pro),
        ]
        for text, active in features:
            f_lbl = QLabel(text if active else f"🔒 {text[2:]} (Pro Only)")
            f_lbl.setStyleSheet("color: #1a7a3c; font-size: 10pt; font-weight: bold;" if active else "color: #94a3b8; font-size: 9.5pt;")
            ib_layout.addWidget(f_lbl)

        root.addWidget(inc_box)

        # Upgrade / Manage Buttons
        btn_layout = QHBoxLayout()
        if not is_pro:
            upgrade_btn = QPushButton("Upgrade to Pro ($49/mo) 🚀")
            upgrade_btn.setFixedHeight(42)
            upgrade_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a7a3c;
                    color: #ffffff;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #145e2e;
                }
            """)
            upgrade_btn.clicked.connect(self.trigger_upgrade)
            btn_layout.addWidget(upgrade_btn)
        else:
            cancel_btn = QPushButton("Cancel Subscription")
            cancel_btn.setFixedHeight(36)
            cancel_btn.setStyleSheet("background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; border-radius: 6px; font-weight: bold;")
            cancel_btn.clicked.connect(self.trigger_cancellation)
            btn_layout.addWidget(cancel_btn)

        root.addLayout(btn_layout)

    def trigger_upgrade(self):
        try:
            res = self.razorpay.create_subscription("plan_founder_pro", customer_email="founder@example.com")
            sub_id = res.get("id")
            pay_url = res.get("short_url")

            if pay_url:
                import webbrowser
                webbrowser.open(pay_url)

            # Verification Modal
            reply = QMessageBox.question(
                self,
                "Verify Pro Upgrade",
                f"Razorpay subscription created (ID: {sub_id}).\n\nDid you complete payment in your browser?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.entitlement_service.activate_pro_subscription(sub_id)
                QMessageBox.information(self, "Success", "Pro subscription activated cleanly!")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Subscription Error", f"Failed to initiate subscription: {str(e)}")

    def trigger_cancellation(self):
        reply = QMessageBox.question(
            self,
            "Cancel Subscription",
            "Are you sure you want to cancel your Pro subscription?\n\nYour account will revert to the Free Starter plan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.entitlement_service.cancel_subscription()
            QMessageBox.information(self, "Cancelled", "Subscription cancelled. Account set to Free.")
            self.accept()
