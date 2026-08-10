from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QStackedWidget, QWidget, QLineEdit,
                             QComboBox, QFrame, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import os

from services.company_profile_service import CompanyProfileService

class OnboardingWizardDialog(QDialog):
    """
    Production 4-Step First-Run Customer Onboarding Wizard.
    Step 1: About Business ➔ Step 2: Focus Areas ➔ Step 3: Attach Context ➔ Step 4: Ready.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Founder AI")
        self.setFixedSize(620, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #0f2318;
            }
        """)
        self.profile_data = {}
        self._profile_svc = CompanyProfileService()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header Title
        header_lbl = QLabel("Welcome to Founder AI")
        header_lbl.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_lbl.setStyleSheet("color: #1a7a3c;")
        root.addWidget(header_lbl)

        sub_lbl = QLabel("Find what's holding your business back, prove it with evidence, take action, and measure whether it worked.")
        sub_lbl.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub_lbl.setWordWrap(True)
        root.addWidget(sub_lbl)

        # Step Progress Indicator
        self.step_label = QLabel("STEP 1 OF 4  •  ABOUT YOUR BUSINESS")
        self.step_label.setStyleSheet("color: #1a7a3c; font-size: 9pt; font-weight: bold; letter-spacing: 1px;")
        root.addWidget(self.step_label)

        # Stacked Widget Container
        self.stacked = QStackedWidget()

        # Step 1: About Your Business
        self.step1_widget = QWidget()
        s1_layout = QVBoxLayout(self.step1_widget)
        s1_layout.setSpacing(12)

        s1_layout.addWidget(QLabel("Company / Product Name:"))
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("e.g. Acme SaaS Inc.")
        self.company_input.setFixedHeight(36)
        self.company_input.setStyleSheet("border: 1px solid #ccebd7; border-radius: 6px; padding: 0 10px;")
        s1_layout.addWidget(self.company_input)

        s1_layout.addWidget(QLabel("Industry Sector:"))
        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g. B2B SaaS / E-Commerce / EdTech")
        self.industry_input.setFixedHeight(36)
        self.industry_input.setStyleSheet("border: 1px solid #ccebd7; border-radius: 6px; padding: 0 10px;")
        s1_layout.addWidget(self.industry_input)

        s1_layout.addWidget(QLabel("Business Stage:"))
        self.stage_combo = QComboBox()
        self.stage_combo.addItems(["Early Stage / Pre-Revenue", "Seed ($1k - $10k MRR)", "Growth ($10k - $100k MRR)", "Scale-up ($100k+ MRR)"])
        self.stage_combo.setFixedHeight(36)
        self.stage_combo.setStyleSheet("border: 1px solid #ccebd7; border-radius: 6px; padding: 0 10px;")
        s1_layout.addWidget(self.stage_combo)

        s1_layout.addWidget(QLabel("Your #1 Quarterly Goal (What matters most right now?):"))
        self.quarterly_goal_input = QLineEdit()
        self.quarterly_goal_input.setPlaceholderText("e.g. Reach $10k MRR by end of Q3")
        self.quarterly_goal_input.setFixedHeight(36)
        self.quarterly_goal_input.setStyleSheet("border: 1px solid #ccebd7; border-radius: 6px; padding: 0 10px;")
        s1_layout.addWidget(self.quarterly_goal_input)

        s1_layout.addStretch()
        self.stacked.addWidget(self.step1_widget)

        # Step 2: What Do You Want to Improve?
        self.step2_widget = QWidget()
        s2_layout = QVBoxLayout(self.step2_widget)
        s2_layout.setSpacing(10)
        s2_layout.addWidget(QLabel("Select your primary operational focus (Select one or multiple):"))

        self.goals = [
            ("Revenue & Monetization", "Fix conversion funnel leaks and increase MRR."),
            ("Customer Growth & Churn", "Reduce churn and improve customer onboarding."),
            ("Product & Operations", "Remove founder bottleneck and streamline systems."),
            ("Execution & Strategy", "Align team sprints and clear execution blockers.")
        ]
        self.goal_btns = []
        for title, desc in self.goals:
            btn = QPushButton(f"🎯  {title}\n    {desc}")
            btn.setCheckable(True)
            btn.setFixedHeight(54)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #0f2318;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 10pt;
                }
                QPushButton:checked {
                    background-color: #f0fbf4;
                    color: #1a7a3c;
                    border: 2px solid #1a7a3c;
                    font-weight: bold;
                }
            """)
            s2_layout.addWidget(btn)
            self.goal_btns.append((title, btn))

        s2_layout.addStretch()
        self.stacked.addWidget(self.step2_widget)

        # Step 3: Add Business Context
        self.step3_widget = QWidget()
        s3_layout = QVBoxLayout(self.step3_widget)
        s3_layout.setSpacing(12)

        info_box = QFrame()
        info_box.setStyleSheet("background: #f0fbf4; border: 1px solid #ccebd7; border-radius: 8px; padding: 16px;")
        ib_layout = QVBoxLayout(info_box)
        ib_title = QLabel("📄 Attach Business Context (Optional)")
        ib_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        ib_title.setStyleSheet("color: #1a7a3c;")
        ib_desc = QLabel("Uploading CSV, PDF, or P&L financial data helps Founder AI provide evidence-backed recommendations with 89%+ confidence.")
        ib_desc.setStyleSheet("color: #4b6b5a; font-size: 10pt;")
        ib_desc.setWordWrap(True)
        ib_layout.addWidget(ib_title)
        ib_layout.addWidget(ib_desc)
        s3_layout.addWidget(info_box)

        self.file_status_lbl = QLabel("No document attached yet.")
        self.file_status_lbl.setStyleSheet("color: #64748b; font-style: italic;")
        s3_layout.addWidget(self.file_status_lbl)

        upload_btn = QPushButton("📁 Select CSV / PDF / P&L Document")
        upload_btn.setFixedHeight(40)
        upload_btn.setStyleSheet("background: #1a7a3c; color: white; border-radius: 6px; font-weight: bold;")
        upload_btn.clicked.connect(self.browse_file)
        s3_layout.addWidget(upload_btn)

        s3_layout.addStretch()
        self.stacked.addWidget(self.step3_widget)

        # Step 4: Ready
        self.step4_widget = QWidget()
        s4_layout = QVBoxLayout(self.step4_widget)
        s4_layout.setSpacing(12)

        ready_card = QFrame()
        ready_card.setStyleSheet("background: #ffffff; border: 1px solid #ebf7f0; border-radius: 10px; padding: 16px;")
        rc_layout = QVBoxLayout(ready_card)
        rc_title = QLabel("🚀 Founder AI Execution Pipeline Ready")
        rc_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        rc_title.setStyleSheet("color: #1a7a3c;")
        
        steps_text = QLabel(
            "1. Observe your business context\n"
            "2. Diagnose the primary constraint\n"
            "3. Verify the evidence & confidence score\n"
            "4. Recommend a decision using 13 Founder Frameworks\n"
            "5. Help execute approved actions\n"
            "6. Measure the result & learn from the outcome"
        )
        steps_text.setStyleSheet("color: #2d4536; font-size: 10.5pt; line-height: 1.6;")
        rc_layout.addWidget(rc_title)
        rc_layout.addWidget(steps_text)
        s4_layout.addWidget(ready_card)

        s4_layout.addStretch()
        self.stacked.addWidget(self.step4_widget)

        root.addWidget(self.stacked, stretch=1)

        # Bottom Button Bar
        btn_bar = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedSize(90, 36)
        self.back_btn.setEnabled(False)
        self.back_btn.clicked.connect(self.prev_step)

        self.next_btn = QPushButton("Continue ➔")
        self.next_btn.setFixedSize(140, 36)
        self.next_btn.setStyleSheet("background: #1a7a3c; color: white; border-radius: 6px; font-weight: bold;")
        self.next_btn.clicked.connect(self.next_step)

        btn_bar.addWidget(self.back_btn)
        btn_bar.addStretch()
        btn_bar.addWidget(self.next_btn)
        root.addLayout(btn_bar)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Business Document", "", "Documents (*.csv *.pdf *.txt *.xlsx)")
        if file_path:
            self.attached_file = file_path
            self.file_status_lbl.setText(f"Attached: {os.path.basename(file_path)}")
            self.file_status_lbl.setStyleSheet("color: #166534; font-weight: bold;")

    def next_step(self):
        idx = self.stacked.currentIndex()
        if idx == 0:
            name = self.company_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Input Required", "Please enter your Company Name to continue.")
                return
            self.profile_data["company_name"] = name
            self.profile_data["industry"] = self.industry_input.text().strip() or "General SaaS"
            self.profile_data["stage"] = self.stage_combo.currentText()
            self.profile_data["quarterly_goal"] = self.quarterly_goal_input.text().strip()
            self.stacked.setCurrentIndex(1)
            self.step_label.setText("STEP 2 OF 4  •  PRIMARY GOALS")
            self.back_btn.setEnabled(True)
        elif idx == 1:
            selected_goals = [title for title, btn in self.goal_btns if btn.isChecked()]
            self.profile_data["goals"] = selected_goals or ["Revenue & Monetization"]
            self.stacked.setCurrentIndex(2)
            self.step_label.setText("STEP 3 OF 4  •  BUSINESS CONTEXT")
        elif idx == 2:
            self.stacked.setCurrentIndex(3)
            self.step_label.setText("STEP 4 OF 4  •  READY TO DIAGNOSE")
            self.next_btn.setText("Run My First Diagnosis 🚀")
        elif idx == 3:
            self.save_and_complete()

    def prev_step(self):
        idx = self.stacked.currentIndex()
        if idx > 0:
            self.stacked.setCurrentIndex(idx - 1)
            labels = ["ABOUT YOUR BUSINESS", "PRIMARY GOALS", "BUSINESS CONTEXT", "READY TO DIAGNOSE"]
            self.step_label.setText(f"STEP {idx} OF 4  •  {labels[idx-1]}")
            self.next_btn.setText("Continue ➔")
            if idx - 1 == 0:
                self.back_btn.setEnabled(False)

    def save_and_complete(self):
        # Use CompanyProfileService as canonical writer — never write JSON directly
        self.profile_data["onboarding_complete"] = True
        try:
            self._profile_svc.save_profile(self.profile_data)
        except Exception as e:
            print(f"[OnboardingWizard] Failed to save profile: {e}")
        self.accept()
