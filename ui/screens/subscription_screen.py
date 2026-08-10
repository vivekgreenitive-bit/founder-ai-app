"""
ui/screens/subscription_screen.py
Dedicated Subscription & Billing Dialog.
Displays 3 subscription plans clearly with radio button selection:
1. Free Starter ($0/mo)
2. Founder Pro ($49/mo)
3. Enterprise Growth ($199/mo)
Allows immediate plan switching / activation via Razorpay or direct selection.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QRadioButton, QButtonGroup, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from services.entitlement_service import EntitlementService
from providers.razorpay_provider import RazorpayPaymentProvider


class SubscriptionBillingDialog(QDialog):
    """
    Subscription & Billing Dialog with Radio Button Selection for all 3 plans.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Subscription & Billing")
        self.setFixedSize(620, 680)

        self.entitlement_service = EntitlementService()
        self.razorpay = RazorpayPaymentProvider()

        current_plan = self.entitlement_service.get_user_plan() if hasattr(self.entitlement_service, "get_user_plan") else ("PRO" if self.entitlement_service.is_pro() else "FREE")
        self.selected_plan = current_plan
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # Header
        head_title = QLabel("💳 Choose Subscription Plan")
        head_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        head_title.setStyleSheet("color: #0f2318;")
        root.addWidget(head_title)

        sub_title = QLabel("Select your plan below. You can change your plan at any time.")
        sub_title.setStyleSheet("color: #4b6b5a; font-size: 10pt;")
        root.addWidget(sub_title)

        # Scroll Area for Plans
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(12)

        self.button_group = QButtonGroup(self)

        # ── PLAN 1: FREE STARTER ─────────────────────────────────────────────
        self.free_card = QFrame()
        self.free_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_card(self.free_card, selected=(self.selected_plan == "FREE"))

        fc_layout = QVBoxLayout(self.free_card)
        fc_layout.setSpacing(6)

        fc_top = QHBoxLayout()
        self.free_radio = QRadioButton("Free Starter Plan")
        self.free_radio.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.free_radio.setChecked(self.selected_plan == "FREE")
        self.free_radio.setStyleSheet("QRadioButton { color: #0f2318; font-weight: bold; }")

        free_price = QLabel("$0 / month")
        free_price.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        free_price.setStyleSheet("color: #1a7a3c;")

        fc_top.addWidget(self.free_radio)
        fc_top.addStretch()
        fc_top.addWidget(free_price)
        fc_layout.addLayout(fc_top)

        free_desc = QLabel("• 2 Core Founder Frameworks (ECG KISS, SLR CAMERAS)\n• Local Offline AI Reasoning (Llama-3.2-3B)\n• Community Support & Basic Actions")
        free_desc.setStyleSheet("color: #4b6b5a; font-size: 9.5pt; padding-left: 20px;")
        fc_layout.addWidget(free_desc)

        self.button_group.addButton(self.free_radio, 1)
        c_layout.addWidget(self.free_card)

        # ── PLAN 2: FOUNDER PRO ──────────────────────────────────────────────
        self.pro_card = QFrame()
        self.pro_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_card(self.pro_card, selected=(self.selected_plan == "PRO"), is_pro=True)

        pc_layout = QVBoxLayout(self.pro_card)
        pc_layout.setSpacing(6)

        pc_top = QHBoxLayout()
        self.pro_radio = QRadioButton("Founder Pro Plan ⭐")
        self.pro_radio.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.pro_radio.setChecked(self.selected_plan == "PRO")
        self.pro_radio.setStyleSheet("QRadioButton { color: #6b21a8; font-weight: bold; }")

        pro_badge = QLabel("RECOMMENDED")
        pro_badge.setStyleSheet("background: #7c3aed; color: white; font-weight: bold; font-size: 7.5pt; padding: 2px 6px; border-radius: 6px;")

        pro_price = QLabel("$49 / month (₹3,999/mo)")
        pro_price.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        pro_price.setStyleSheet("color: #6b21a8;")

        pc_top.addWidget(self.pro_radio)
        pc_top.addWidget(pro_badge)
        pc_top.addStretch()
        pc_top.addWidget(pro_price)
        pc_layout.addLayout(pc_top)

        pro_desc = QLabel("• All 13 Founder Frameworks (Unlimited)\n• Google Gemini 1.5 Pro Cloud Reasoning\n• Customer Intelligence & Competitor Gap Analysis\n• 1:1 GCP Advisory Chat Workspace\n• PDF Report Exports & Bottleneck Tax Calculator")
        pro_desc.setStyleSheet("color: #581c87; font-size: 9.5pt; padding-left: 20px; font-weight: 500;")
        pc_layout.addWidget(pro_desc)

        self.button_group.addButton(self.pro_radio, 2)
        c_layout.addWidget(self.pro_card)

        # ── PLAN 3: ENTERPRISE GROWTH ─────────────────────────────────────────
        self.ent_card = QFrame()
        self.ent_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self._style_card(self.ent_card, selected=(self.selected_plan == "ENTERPRISE"), is_ent=True)

        ec_layout = QVBoxLayout(self.ent_card)
        ec_layout.setSpacing(6)

        ec_top = QHBoxLayout()
        self.ent_radio = QRadioButton("Enterprise Growth Plan 👑")
        self.ent_radio.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.ent_radio.setChecked(self.selected_plan == "ENTERPRISE")
        self.ent_radio.setStyleSheet("QRadioButton { color: #1e3a8a; font-weight: bold; }")

        ent_badge = QLabel("SCALE-UP")
        ent_badge.setStyleSheet("background: #1d4ed8; color: white; font-weight: bold; font-size: 7.5pt; padding: 2px 6px; border-radius: 6px;")

        ent_price = QLabel("$199 / month (₹15,999/mo)")
        ent_price.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        ent_price.setStyleSheet("color: #1e3a8a;")

        ec_top.addWidget(self.ent_radio)
        ec_top.addWidget(ent_badge)
        ec_top.addStretch()
        ec_top.addWidget(ent_price)
        ec_layout.addLayout(ec_top)

        ent_desc = QLabel("• Everything in Pro Plan included\n• Multi-user Team & Co-founder Workspace\n• Custom SOP Generator & Process Automation\n• Governed Agentic Payments & Wallet Controls\n• Dedicated Human Startup Advisor Channel")
        ent_desc.setStyleSheet("color: #1e40af; font-size: 9.5pt; padding-left: 20px; font-weight: 500;")
        ec_layout.addWidget(ent_desc)

        self.button_group.addButton(self.ent_radio, 3)
        c_layout.addWidget(self.ent_card)

        # Connect radio selections
        self.free_radio.toggled.connect(self._on_plan_changed)
        self.pro_radio.toggled.connect(self._on_plan_changed)
        self.ent_radio.toggled.connect(self._on_plan_changed)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # Action Buttons
        self.confirm_btn = QPushButton("Save & Activate Selected Plan")
        self.confirm_btn.setFixedHeight(44)
        self._update_button_style()
        self.confirm_btn.clicked.connect(self.handle_confirm)

        root.addWidget(self.confirm_btn)

    def _style_card(self, card: QFrame, selected: bool, is_pro: bool = False, is_ent: bool = False):
        if selected:
            if is_pro:
                card.setStyleSheet("QFrame { background-color: #f3e8ff; border: 2px solid #7c3aed; border-radius: 12px; padding: 12px; }")
            elif is_ent:
                card.setStyleSheet("QFrame { background-color: #eff6ff; border: 2px solid #1d4ed8; border-radius: 12px; padding: 12px; }")
            else:
                card.setStyleSheet("QFrame { background-color: #f0fbf4; border: 2px solid #1a7a3c; border-radius: 12px; padding: 12px; }")
        else:
            card.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; }")

    def _on_plan_changed(self):
        if self.free_radio.isChecked():
            self.selected_plan = "FREE"
        elif self.pro_radio.isChecked():
            self.selected_plan = "PRO"
        elif self.ent_radio.isChecked():
            self.selected_plan = "ENTERPRISE"

        active_plan = self.entitlement_service.get_user_plan() if hasattr(self.entitlement_service, "get_user_plan") else ("PRO" if self.entitlement_service.is_pro() else "FREE")

        self._style_card(self.free_card, selected=(self.selected_plan == "FREE"))
        self._style_card(self.pro_card, selected=(self.selected_plan == "PRO"), is_pro=True)
        self._style_card(self.ent_card, selected=(self.selected_plan == "ENTERPRISE"), is_ent=True)

        self._update_button_style(active_plan)

    def _update_button_style(self, active_plan: str = None):
        if active_plan is None:
            active_plan = self.entitlement_service.get_user_plan() if hasattr(self.entitlement_service, "get_user_plan") else ("PRO" if self.entitlement_service.is_pro() else "FREE")

        if self.selected_plan == active_plan:
            self.confirm_btn.setText(f"Current Plan ({active_plan}) Active")
            self.confirm_btn.setEnabled(False)
            self.confirm_btn.setStyleSheet("background-color: #94a3b8; color: #ffffff; border-radius: 8px; font-weight: bold; font-size: 11pt;")
        elif self.selected_plan == "PRO":
            self.confirm_btn.setText("Upgrade to Founder Pro ($49/mo) 🚀")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet("background-color: #7c3aed; color: #ffffff; border-radius: 8px; font-weight: bold; font-size: 11pt;")
        elif self.selected_plan == "ENTERPRISE":
            self.confirm_btn.setText("Upgrade to Enterprise Growth ($199/mo) 👑")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet("background-color: #1d4ed8; color: #ffffff; border-radius: 8px; font-weight: bold; font-size: 11pt;")
        else:
            self.confirm_btn.setText("Downgrade to Free Starter")
            self.confirm_btn.setEnabled(True)
            self.confirm_btn.setStyleSheet("background-color: #64748b; color: #ffffff; border-radius: 8px; font-weight: bold; font-size: 11pt;")

    def handle_confirm(self):
        if self.selected_plan == "PRO":
            res = self.razorpay.create_subscription("plan_pro_monthly", "founder@greenitive.com")
            short_url = res.get("short_url", "https://rzp.io/i/pro")
            self.entitlement_service.upgrade_to_pro()
            QMessageBox.information(
                self,
                "Upgrade to Founder Pro",
                f"Your upgrade to Founder Pro ($49/mo) is ready.\n\nCheckout URL:\n{short_url}\n\nPlan features have been activated!"
            )
        elif self.selected_plan == "ENTERPRISE":
            res = self.razorpay.create_subscription("plan_enterprise_monthly", "founder@greenitive.com")
            short_url = res.get("short_url", "https://rzp.io/i/enterprise")
            if hasattr(self.entitlement_service, "upgrade_to_enterprise"):
                self.entitlement_service.upgrade_to_enterprise()
            else:
                self.entitlement_service.upgrade_to_pro()
            QMessageBox.information(
                self,
                "Upgrade to Enterprise Growth",
                f"Your upgrade to Enterprise Growth ($199/mo) is ready.\n\nCheckout URL:\n{short_url}\n\nAll Enterprise features have been activated!"
            )
        else:
            self.entitlement_service.downgrade_to_free()
            QMessageBox.information(self, "Plan Downgraded", "Your plan has been changed to Free Starter.")

        self.accept()
