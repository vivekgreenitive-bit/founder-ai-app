"""
ui/screens/bottleneck_diagnostic_screen.py
60-Second Business Bottleneck Diagnostic Screen.
Runs a 5-domain questionnaire to pinpoint primary business bottleneck and auto-select framework.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QRadioButton, QButtonGroup, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from agents.bottleneck_agent import BottleneckAgent


class BottleneckDiagnosticScreen(QWidget):
    """
    60-Second Business Bottleneck Diagnostic UI Screen.
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
        header = QLabel("🔍 60-Second Business Bottleneck Diagnostic")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        root.addWidget(header)

        sub = QLabel(
            "Answer 5 quick operational questions to isolate your #1 growth bottleneck "
            "and identify the exact Founder Framework needed to fix it."
        )
        sub.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Scroll Area for Questions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(14)

        questions = [
            ("q1", "1. Delegation", "Do you spend >15 hours/week on low-leverage operational or admin tasks?"),
            ("q2", "2. Operations", "Does core business work stop or stall if you take 3 days off?"),
            ("q3", "3. Sales & Pipeline", "Are qualified leads stalling or taking >30 days to close in your sales pipeline?"),
            ("q4", "4. Product & Retention", "Do >20% of new customers cancel or churn within their first 90 days?"),
            ("q5", "5. Cashflow & Runway", "Is your available cash runway less than 6 months of current burn rate?"),
        ]

        self.groups = {}

        for q_id, domain, q_text in questions:
            q_card = QFrame()
            q_card.setStyleSheet("background: #ffffff; border: 1px solid #ccebd7; border-radius: 10px; padding: 14px;")
            qc_layout = QVBoxLayout(q_card)
            qc_layout.setSpacing(6)

            d_lbl = QLabel(domain.upper())
            d_lbl.setStyleSheet("color: #1a7a3c; font-size: 8.5pt; font-weight: bold;")

            t_lbl = QLabel(q_text)
            t_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            t_lbl.setStyleSheet("color: #0f2318;")

            btn_row = QHBoxLayout()
            bg = QButtonGroup(q_card)

            r_yes = QRadioButton("Yes (Bottleneck Present)")
            r_no = QRadioButton("No (Healthy)")
            r_no.setChecked(True)

            bg.addButton(r_yes, 1)
            bg.addButton(r_no, 0)
            self.groups[q_id] = bg

            btn_row.addWidget(r_yes)
            btn_row.addWidget(r_no)
            btn_row.addStretch()

            qc_layout.addWidget(d_lbl)
            qc_layout.addWidget(t_lbl)
            qc_layout.addLayout(btn_row)

            c_layout.addWidget(q_card)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # Run Diagnostic CTA
        self.diag_btn = QPushButton("🔍 Identify My #1 Bottleneck 🚀")
        self.diag_btn.setFixedHeight(44)
        self.diag_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        self.diag_btn.clicked.connect(self._run_diagnostic)
        root.addWidget(self.diag_btn)

    def _run_diagnostic(self):
        answers = {}
        for q_id, bg in self.groups.items():
            answers[q_id] = "yes" if bg.checkedId() == 1 else "no"

        res = self.agent.analyze_domain_bottlenecks(answers)
        primary = res["primary_bottleneck"]
        rec_fw = res["recommended_framework"]

        msg = (
            f"🎯 Primary Bottleneck Identified:\n\n"
            f"• Domain: {primary}\n"
            f"• Recommended Framework: {rec_fw}\n\n"
            f"Would you like to run an automated AI Diagnosis using {rec_fw} now?"
        )

        reply = QMessageBox.question(
            self,
            "Diagnostic Result",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes and self.main_app:
            if hasattr(self.main_app, "selected_framework_prompt"):
                self.main_app.selected_framework_prompt = f"Apply {rec_fw} framework to resolve {primary}"
            if hasattr(self.main_app, "badge_label"):
                self.main_app.badge_label.setText(f"🎯 Using: {rec_fw}")
                self.main_app.badge_widget.setVisible(True)
            if hasattr(self.main_app, "query_input"):
                self.main_app.query_input.setPlainText(f"Our primary business bottleneck is {primary}. Recommend actionable solutions using {rec_fw}.")
            if hasattr(self.main_app, "switch_to_diagnose"):
                self.main_app.switch_to_diagnose()
