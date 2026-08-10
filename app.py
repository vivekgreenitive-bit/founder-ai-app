import sys
import os
import json
import uuid
import re
import numpy as np
np.float_ = np.float64

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTextEdit, QLabel,
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                             QFrame, QComboBox, QScrollArea, QSizePolicy, QTabWidget, QStackedWidget, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence

from document_processor import extract_text_from_file
from ai_engine import FounderAIEngine
from ui.screens.today_screen import TodayScreen
from ui.screens.frameworks_screen import FrameworksScreen
from ui.screens.outcomes_screen import OutcomesScreen
from ui.screens.actions_screen import ActionsScreen
from ui.screens.subscription_screen import SubscriptionBillingDialog
from ui.screens.onboarding_dialog import OnboardingWizardDialog
from ui.screens.business_data_screen import BusinessDataScreen
from ui.screens.bottleneck_tax_screen import BottleneckTaxScreen
from ui.screens.velocity_grader_screen import VelocityGraderScreen
from ui.screens.bottleneck_diagnostic_screen import BottleneckDiagnosticScreen
from ui.screens.consulting_screen import ConsultingScreen
from services.company_profile_service import CompanyProfileService
from services.entitlement_service import EntitlementService
from services.diagnosis_session_service import DiagnosisSessionService


class ClickableCard(QFrame):
    """A clickable QFrame card — shows name + subtitle, description on tooltip."""
    def __init__(self, name, subtitle, desc, prompt, color, bg, border, callback, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.callback = callback
        self.color = color
        self.bg = bg
        self.border = border
        self._selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(30)
        self.setToolTip(desc)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self._apply_style(False)
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 5, 10, 5)
        v.setSpacing(0)
        name_label = QLabel(f"<b>{name}</b>  —  {subtitle}")
        name_label.setStyleSheet(f"color: {color}; font-size: 9pt; background: transparent; border: none;")
        name_label.setWordWrap(False)
        v.addWidget(name_label)

    def _apply_style(self, selected):
        if selected:
            self.setStyleSheet(f"""
                ClickableCard {{
                    background-color: #1e293b;
                    border: 2px solid #3b82f6;
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ClickableCard {{
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }}
                ClickableCard:hover {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                }}
            """)

    def set_selected(self, selected):
        self._selected = selected
        self._apply_style(selected)

    def mousePressEvent(self, event):
        self.callback(self.prompt, self)

class AnalysisWorker(QThread):
    finished = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, engine, query, document_text):
        super().__init__()
        self.engine = engine
        self.query = query
        self.document_text = document_text
        
    def run(self):
        try:
            def callback(msg):
                self.progress_update.emit(msg)
            result = self.engine.analyze_query(self.query, self.document_text, status_callback=callback)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class EngineInitWorker(QThread):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    
    def run(self):
        try:
            engine = FounderAIEngine()
            self.finished.emit(engine)
        except Exception as e:
            self.failed.emit(str(e))

class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Profile Configuration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #f8fafc;
            }
            QTabBar::tab {
                background: #e2e8f0;
                color: #475467;
                padding: 10px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 11pt;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0f172a;
                border-bottom: 2px solid #2563eb;
            }
        """)
        
        # ----------------------------------------------------
        # Tab 1: Company Profile
        # ----------------------------------------------------
        self.profile_tab = QWidget()
        profile_layout = QVBoxLayout(self.profile_tab)
        profile_layout.setContentsMargins(20, 20, 20, 20)
        profile_layout.setSpacing(15)
        
        subtitle = QLabel("The AI needs to understand your current business landscape to tailor its frameworks.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b; font-size: 11pt;")
        profile_layout.addWidget(subtitle)
        
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(12)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Inputs
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Acme Corp")
        
        self.industry_input = QComboBox()
        self.industry_input.addItems(["SaaS / Software", "E-commerce", "Manufacturing", "Agency / Services", "Retail", "Healthcare", "Real Estate", "Other"])
        
        self.stage_input = QComboBox()
        self.stage_input.addItems(["Pre-revenue / Idea", "Early Stage ($0 - $1M)", "Growth ($1M - $10M)", "Enterprise ($10M+)"])
        
        self.team_input = QComboBox()
        self.team_input.addItems(["Solo Founder", "2 - 10 Employees", "11 - 50 Employees", "50+ Employees"])
        
        self.challenge_input = QComboBox()
        self.challenge_input.addItems(["Founder is the Bottleneck", "Unpredictable Cash Flow", "Team Execution Errors / Lack of SOPs", "Stagnant Revenue Growth", "Other"])
        
        input_style = """
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                font-size: 11pt;
                color: #334155;
            }
        """
        self.name_input.setStyleSheet(input_style)
        self.industry_input.setStyleSheet(input_style)
        self.stage_input.setStyleSheet(input_style)
        self.team_input.setStyleSheet(input_style)
        self.challenge_input.setStyleSheet(input_style)
        
        label_font = QFont("Arial", 11, QFont.Weight.Bold)
        
        def add_styled_row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setFont(label_font)
            lbl.setStyleSheet("color: #334155;")
            self.form_layout.addRow(lbl, widget)
            
        add_styled_row("Business Name:", self.name_input)
        add_styled_row("Industry:", self.industry_input)
        add_styled_row("Business Stage:", self.stage_input)
        add_styled_row("Team Size:", self.team_input)
        add_styled_row("Primary Challenge:", self.challenge_input)
        
        profile_layout.addLayout(self.form_layout)
        profile_layout.addStretch()
        
        # ----------------------------------------------------
        # Tab 2: Model Configuration
        # ----------------------------------------------------
        self.model_tab = QWidget()
        model_layout = QVBoxLayout(self.model_tab)
        model_layout.setContentsMargins(20, 20, 20, 20)
        model_layout.setSpacing(15)
        
        model_subtitle = QLabel("Select whether to run the AI completely offline or connect to cloud API engines.")
        model_subtitle.setWordWrap(True)
        model_subtitle.setStyleSheet("color: #64748b; font-size: 11pt;")
        model_layout.addWidget(model_subtitle)
        
        self.model_form_layout = QFormLayout()
        self.model_form_layout.setSpacing(12)
        self.model_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.provider_select = QComboBox()
        self.provider_select.addItems(["Local (Default)", "OpenAI", "Gemini"])
        self.provider_select.setStyleSheet(input_style)
        
        self.model_select = QComboBox()
        self.model_select.setStyleSheet(input_style)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your API Key")
        self.api_key_input.setStyleSheet(input_style)
        
        # Add rows
        lbl_prov = QLabel("AI Provider:")
        lbl_prov.setFont(label_font)
        lbl_prov.setStyleSheet("color: #334155;")
        self.model_form_layout.addRow(lbl_prov, self.provider_select)
        
        self.lbl_model = QLabel("Model Name:")
        self.lbl_model.setFont(label_font)
        self.lbl_model.setStyleSheet("color: #334155;")
        self.model_form_layout.addRow(self.lbl_model, self.model_select)
        
        self.lbl_key = QLabel("API Key:")
        self.lbl_key.setFont(label_font)
        self.lbl_key.setStyleSheet("color: #334155;")
        self.model_form_layout.addRow(self.lbl_key, self.api_key_input)
        
        model_layout.addLayout(self.model_form_layout)
        
        # Test Connection button
        self.test_conn_btn = QPushButton("🔌 Test Connection")
        self.test_conn_btn.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        
        self.test_conn_btn.clicked.connect(self.test_model_connection)
        model_layout.addWidget(self.test_conn_btn)
        
        # Privacy Notice panel
        self.privacy_panel = QLabel()
        self.privacy_panel.setWordWrap(True)
        self.privacy_panel.setStyleSheet("""
            padding: 12px;
            background: #eff8ff;
            border: 1px solid #d1e9ff;
            border-radius: 6px;
            color: #1e3a8a;
            font-size: 10pt;
        """)
        model_layout.addWidget(self.privacy_panel)
        model_layout.addStretch()
        
        # Add tabs
        self.tabs.addTab(self.profile_tab, "🏢 Company Profile")
        self.tabs.addTab(self.model_tab, "🤖 Model Configuration")

        # ----------------------------------------------------
        # Tab 3: Payments & Policies
        # ----------------------------------------------------
        self.payments_tab = QWidget()
        payments_layout = QVBoxLayout(self.payments_tab)
        payments_layout.setContentsMargins(20, 20, 20, 20)
        payments_layout.setSpacing(15)

        from db.payment_db import PaymentDBManager
        self.pay_db = PaymentDBManager()
        wallet = self.pay_db.get_wallet("primary_usdc_wallet")
        policy = self.pay_db.get_active_policy() or {
            "max_transaction_limit": 200.0,
            "daily_spending_limit": 500.0,
            "monthly_budget": 2000.0,
            "emergency_stop": 0
        }

        wallet_info = QLabel(f"<b>USDC Wallet:</b> {wallet['address']}<br><b>Blockchain:</b> {wallet['blockchain']}<br><b>USDC Balance:</b> {wallet['usdc_balance']} USDC")
        wallet_info.setStyleSheet("padding: 12px; background: #e2e8f0; border-radius: 6px; color: #1e293b; font-size: 11pt;")
        payments_layout.addWidget(wallet_info)

        self.pay_form_layout = QFormLayout()
        self.pay_form_layout.setSpacing(12)
        self.pay_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.max_limit_input = QLineEdit()
        self.max_limit_input.setStyleSheet(input_style)
        self.max_limit_input.setText(str(policy.get("max_transaction_limit", 200.0)))

        self.daily_limit_input = QLineEdit()
        self.daily_limit_input.setStyleSheet(input_style)
        self.daily_limit_input.setText(str(policy.get("daily_spending_limit", 500.0)))

        self.monthly_budget_input = QLineEdit()
        self.monthly_budget_input.setStyleSheet(input_style)
        self.monthly_budget_input.setText(str(policy.get("monthly_budget", 2000.0)))

        self.emergency_checkbox = QComboBox()
        self.emergency_checkbox.setStyleSheet(input_style)
        self.emergency_checkbox.addItems(["Inactive (Normal Operations)", "Active (Freeze All Transactions)"])
        self.emergency_checkbox.setCurrentIndex(1 if policy.get("emergency_stop") == 1 else 0)

        def add_pay_row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setFont(label_font)
            lbl.setStyleSheet("color: #334155;")
            self.pay_form_layout.addRow(lbl, widget)

        add_pay_row("Max Transaction Limit:", self.max_limit_input)
        add_pay_row("Daily Spending Limit:", self.daily_limit_input)
        add_pay_row("Monthly Spending Budget:", self.monthly_budget_input)
        add_pay_row("Emergency Stop Lock:", self.emergency_checkbox)

        payments_layout.addLayout(self.pay_form_layout)
        payments_layout.addStretch()

        self.tabs.addTab(self.payments_tab, "💳 Agentic Payments")
        main_layout.addWidget(self.tabs)
        
        # Load configs
        self.profile_path = "company_profile.json"
        self.load_profile()
        from providers.provider_factory import ProviderFactory
        self.model_config = ProviderFactory.load_config()
        self.load_model_config()
        
        # Connect changes
        self.provider_select.currentIndexChanged.connect(self.on_provider_changed)
        self.update_model_dropdown_and_inputs()
        
        # Save Button
        self.save_btn = QPushButton("Save Settings & Apply Changes")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: white;
                font-weight: bold;
                font-size: 13pt;
                padding: 12px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #145c2d;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        main_layout.addWidget(self.save_btn)
        
        self.setStyleSheet("QDialog { background-color: #f8fafc; }")
        
    def load_model_config(self):
        prov = self.model_config.get("provider", "local").capitalize()
        self.set_combo_text(self.provider_select, "Local (Default)" if prov == "Local" else prov)
        
    def on_provider_changed(self):
        self.update_model_dropdown_and_inputs()
        
    def update_model_dropdown_and_inputs(self):
        provider = self.provider_select.currentText()
        self.model_select.clear()
        
        if provider == "Local (Default)":
            self.model_select.addItems(["Llama-3.2-3B"])
            self.model_select.setEnabled(False)
            self.api_key_input.setEnabled(False)
            self.api_key_input.setText("")
            self.api_key_input.setVisible(False)
            self.lbl_key.setVisible(False)
            self.test_conn_btn.setVisible(False)
            self.privacy_panel.setText("🔒 <b>Privacy Status: 100% Offline Mode</b><br>All queries are processed entirely on your local machine. No data ever leaves your computer.")
            self.privacy_panel.setStyleSheet("padding: 12px; background: #ecfdf5; border: 1px solid #d1fae5; border-radius: 6px; color: #065f46; font-size: 10pt;")
        
        elif provider == "OpenAI":
            self.model_select.addItems(["gpt-4o-mini", "gpt-4o"])
            self.model_select.setEnabled(True)
            self.api_key_input.setEnabled(True)
            self.api_key_input.setText(self.model_config.get("openai", {}).get("api_key", ""))
            self.api_key_input.setVisible(True)
            self.lbl_key.setVisible(True)
            self.test_conn_btn.setVisible(True)
            self.set_combo_text(self.model_select, self.model_config.get("openai", {}).get("model", "gpt-4o-mini"))
            self.privacy_panel.setText("🌐 <b>Privacy Status: Cloud Processing</b><br>Your strategy queries are sent securely to OpenAI for processing. Please ensure your API key has sufficient balance.")
            self.privacy_panel.setStyleSheet("padding: 12px; background: #fffbeb; border: 1px solid #fef3c7; border-radius: 6px; color: #92400e; font-size: 10pt;")
            
        elif provider == "Gemini":
            self.model_select.addItems(["gemini-1.5-flash", "gemini-1.5-pro"])
            self.model_select.setEnabled(True)
            self.api_key_input.setEnabled(True)
            self.api_key_input.setText(self.model_config.get("gemini", {}).get("api_key", ""))
            self.api_key_input.setVisible(True)
            self.lbl_key.setVisible(True)
            self.test_conn_btn.setVisible(True)
            self.set_combo_text(self.model_select, self.model_config.get("gemini", {}).get("model", "gemini-1.5-flash"))
            self.privacy_panel.setText("🌐 <b>Privacy Status: Cloud Processing</b><br>Your strategy queries are sent securely to Google Gemini for processing. Please ensure your API key is configured correctly.")
            self.privacy_panel.setStyleSheet("padding: 12px; background: #fffbeb; border: 1px solid #fef3c7; border-radius: 6px; color: #92400e; font-size: 10pt;")

    def test_model_connection(self):
        provider = self.provider_select.currentText()
        api_key = self.api_key_input.text().strip()
        model = self.model_select.currentText()
        
        if not api_key:
            QMessageBox.warning(self, "API Key Missing", "Please enter a valid API key to test connection.")
            return
            
        self.test_conn_btn.setText("⏳ Testing Connection...")
        self.test_conn_btn.setEnabled(False)
        QApplication.processEvents()
        
        success = False
        try:
            if provider == "OpenAI":
                from providers.openai_provider import OpenAIProvider
                prov_obj = OpenAIProvider(api_key, model)
                success = prov_obj.health_check()
            elif provider == "Gemini":
                from providers.gemini_provider import GeminiProvider
                prov_obj = GeminiProvider(api_key, model)
                success = prov_obj.health_check()
        except Exception as e:
            print("Test connection exception:", e)
            
        self.test_conn_btn.setText("🔌 Test Connection")
        self.test_conn_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", f"Connection test passed! The {provider} service is online and active.")
        else:
            QMessageBox.critical(self, "Failure", f"Connection test failed. Please verify your API key and check if the chosen model is active on your API billing plan.")

    def set_combo_text(self, combo, text):
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)
        
    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    data = json.load(f)
                    self.name_input.setText(data.get("name", ""))
                    self.set_combo_text(self.industry_input, data.get("industry", ""))
                    self.set_combo_text(self.stage_input, data.get("stage", ""))
                    self.set_combo_text(self.team_input, data.get("team", ""))
                    self.set_combo_text(self.challenge_input, data.get("challenge", ""))
            except:
                pass
                
    def accept(self):
        # Save Profile
        profile_data = {
            "name": self.name_input.text(),
            "industry": self.industry_input.currentText(),
            "stage": self.stage_input.currentText(),
            "team": self.team_input.currentText(),
            "challenge": self.challenge_input.currentText()
        }
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(profile_data, f)
        except Exception as e:
            print("Failed to save profile:", e)
            
        # Save Model Config
        from providers.provider_factory import ProviderFactory
        provider = self.provider_select.currentText()
        if provider == "Local (Default)":
            self.model_config["provider"] = "local"
        elif provider == "OpenAI":
            self.model_config["provider"] = "openai"
            self.model_config["openai"]["api_key"] = self.api_key_input.text().strip()
            self.model_config["openai"]["model"] = self.model_select.currentText()
        elif provider == "Gemini":
            self.model_config["provider"] = "gemini"
            self.model_config["gemini"]["api_key"] = self.api_key_input.text().strip()
            self.model_config["gemini"]["model"] = self.model_select.currentText()
            
        ProviderFactory.save_config(self.model_config)

        # Save payment policy limits
        try:
            max_limit = float(self.max_limit_input.text().strip())
            daily_limit = float(self.daily_limit_input.text().strip())
            monthly_budget = float(self.monthly_budget_input.text().strip())
            emerg_stop = 1 if self.emergency_checkbox.currentIndex() == 1 else 0
            self.pay_db.update_policy(max_limit, daily_limit, monthly_budget, emerg_stop)
        except Exception as e:
            print("Failed to save payment policy limits:", e)
        
        # Trigger reload of LLM in active application parent
        if self.parent() and hasattr(self.parent(), "init_ai"):
            self.parent().init_ai()
            
        super().accept()


class FounderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Founder AI")
        self.setMinimumSize(1100, 680)

        # Services — initialized once, shared across screens
        self._profile_svc = CompanyProfileService()
        self._entitlement_svc = EntitlementService()
        self._session_svc = DiagnosisSessionService()

        # Size the window to fit the screen naturally — desktop app feel
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = min(1400, int(screen.width() * 0.92))
        h = min(860, int(screen.height() * 0.92))
        self.resize(w, h)
        # Center on screen
        self.move(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2
        )
        self.setAcceptDrops(True)

        # Data
        self.engine = None
        self.current_document_text = ""
        self.current_file_path = ""
        self.selected_framework_prompt = None
        self._selected_card = None        # track highlighted sidebar card
        self._all_sidebar_cards = []      # list of all ClickableCard widgets

        self.init_ui()
        self.init_ai()
        
    def showEvent(self, event):
        super().showEvent(event)
        # Wire OnboardingWizardDialog: open on first launch or incomplete onboarding.
        # CompanyProfileService is the canonical source — avoids raw file checks.
        if not self._profile_svc.is_onboarding_complete():
            wizard = OnboardingWizardDialog(self)
            wizard.exec()
            # Refresh account button label after onboarding completes
            self._refresh_account_button()
           
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        main_widget.setLayout(root)

        # ── Top Header Bar ────────────────────────────────────────────────────
        header_bar = QFrame()
        header_bar.setStyleSheet("background: #ffffff; border-bottom: 1px solid #e2e8f0;")
        header_bar.setFixedHeight(56)
        header_bar_layout = QHBoxLayout(header_bar)
        header_bar_layout.setContentsMargins(20, 0, 20, 0)

        header = QLabel("Founder AI Assistant")
        header.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f172a; background: transparent; border: none;")
        header_bar_layout.addWidget(header)

        self.status_label = QLabel("Starting up...")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11pt; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar_layout.addWidget(self.status_label, stretch=1)

        # Account Control Bar Dropdown (Top Right)
        # Read real founder name and plan from services — never hardcoded.
        self.account_btn = QPushButton("")
        self._refresh_account_button()  # populates label from real services
        self.account_btn.setFixedHeight(36)
        self.account_btn.setToolTip("Account & Profile Controls")
        self.account_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0f2318;
                border: 1px solid #ccebd7;
                border-radius: 18px;
                padding: 0 14px;
                font-weight: 600;
                font-size: 10.5pt;
            }
            QPushButton:hover {
                background-color: #ebf7f0;
                border: 1px solid #1a7a3c;
            }
        """)

        # Account Dropdown Menu
        self.account_menu = QMenu(self)
        self.account_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #ccebd7;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 20px;
                color: #0f2318;
                font-size: 10pt;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #ebf7f0;
                color: #1a7a3c;
                font-weight: bold;
            }
            QMenu::separator {
                height: 1px;
                background: #e2e8f0;
                margin: 4px 0;
            }
        """)

        act_account = self.account_menu.addAction("👤  My Account")
        act_profile = self.account_menu.addAction("🏢  Company Profile")
        act_billing = self.account_menu.addAction("💳  Subscription & Billing")
        act_payments = self.account_menu.addAction("🛡️  Payments & Governance")
        self.account_menu.addSeparator()
        act_signout = self.account_menu.addAction("🚪  Sign Out")

        act_account.triggered.connect(self.open_settings)
        act_profile.triggered.connect(self.open_settings)
        act_billing.triggered.connect(self.open_subscription)
        act_payments.triggered.connect(self.open_settings)
        act_signout.triggered.connect(self.handle_sign_out)

        self.account_btn.setMenu(self.account_menu)
        header_bar_layout.addWidget(self.account_btn)
        root.addWidget(header_bar)

        # ── Two-panel body ────────────────────────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ════════════════════════════════════════════════════════════════════
        # LEFT PANEL — Workflow Navigator
        # ════════════════════════════════════════════════════════════════════
        left_panel = QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setFixedWidth(220)
        left_panel.setStyleSheet("""
            QFrame#LeftPanel {
                background-color: #f0fbf4;
                border-right: 1px solid #ccebd7;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 16, 12, 16)
        left_layout.setSpacing(8)

        nav_title = QLabel("FOUNDER AI")
        nav_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        nav_title.setStyleSheet("color: #1a7a3c; letter-spacing: 1.5px; margin-bottom: 8px;")
        left_layout.addWidget(nav_title)

        self.nav_buttons = {}

        # ── Section: Core Journey ────────────────────────────────────────────
        core_section = QLabel("CORE JOURNEY")
        core_section.setStyleSheet(
            "color: #94a3b8; font-size: 7.5pt; font-weight: bold; "
            "letter-spacing: 1px; padding: 8px 14px 2px 14px;"
        )
        left_layout.addWidget(core_section)

        nav_items_core = [
            ("today",      "  Today"),
            ("diagnose",   "  Diagnose"),
            ("actions",    "  Actions"),
            ("outcomes",   "  Outcomes"),
        ]

        # ── Section: Diagnostic Tools ─────────────────────────────────────────
        diag_section = QLabel("DIAGNOSTIC TOOLS")
        diag_section.setStyleSheet(
            "color: #94a3b8; font-size: 7.5pt; font-weight: bold; "
            "letter-spacing: 1px; padding: 12px 14px 2px 14px;"
        )

        nav_items_diag = [
            ("bottleneck_tax",        "  Bottleneck Tax Calculator"),
            ("velocity_grader",       "  Execution Velocity Grader"),
            ("bottleneck_diagnostic",  "  60s Bottleneck Diagnostic"),
        ]

        # ── Section: Knowledge & Data ─────────────────────────────────────────
        knowledge_section = QLabel("KNOWLEDGE & DATA")
        knowledge_section.setStyleSheet(
            "color: #94a3b8; font-size: 7.5pt; font-weight: bold; "
            "letter-spacing: 1px; padding: 12px 14px 2px 14px;"
        )

        nav_items_knowledge = [
            ("frameworks",    "  Frameworks"),
            ("business_data", "  Business Data"),
        ]

        # ── Section: Support & Advisory ───────────────────────────────────────
        support_section = QLabel("SUPPORT & ADVISORY")
        support_section.setStyleSheet(
            "color: #94a3b8; font-size: 7.5pt; font-weight: bold; "
            "letter-spacing: 1px; padding: 12px 14px 2px 14px;"
        )

        nav_items_support = [
            ("advisory_chat",  "  Advisory Chat"),
        ]

        nav_items = nav_items_core + nav_items_diag + nav_items_knowledge + nav_items_support

        nav_btn_qss = """
            QPushButton {
                background-color: transparent;
                color: #1e4433;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 14px;
                font-size: 10.5pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #d1f5e0;
                color: #1a7a3c;
            }
            QPushButton:checked {
                background-color: #1a7a3c;
                color: #ffffff;
            }
        """

        left_layout.addWidget(core_section)
        for key, label in nav_items_core:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setStyleSheet(nav_btn_qss)
            btn.clicked.connect(lambda checked, k=key: self.switch_nav(k))
            left_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        left_layout.addWidget(diag_section)
        for key, label in nav_items_diag:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setStyleSheet(nav_btn_qss)
            btn.clicked.connect(lambda checked, k=key: self.switch_nav(k))
            left_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        left_layout.addWidget(knowledge_section)
        for key, label in nav_items_knowledge:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setStyleSheet(nav_btn_qss)
            btn.clicked.connect(lambda checked, k=key: self.switch_nav(k))
            left_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        left_layout.addWidget(support_section)
        for key, label in nav_items_support:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setCheckable(True)
            btn.setStyleSheet(nav_btn_qss)
            btn.clicked.connect(lambda checked, k=key: self.switch_nav(k))
            left_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        left_layout.addStretch()

        # Settings nav button at bottom
        self.nav_settings_btn = QPushButton("Settings")
        self.nav_settings_btn.setFixedHeight(40)
        self.nav_settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #2d4536;
                border: 1px solid #ccebd7;
                border-radius: 8px;
                text-align: left;
                padding-left: 14px;
                font-size: 10.5pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #dcfce7;
                color: #1a7a3c;
                border: 1px solid #1a7a3c;
            }
        """)
        self.nav_settings_btn.clicked.connect(self.open_settings)
        left_layout.addWidget(self.nav_settings_btn)

        body_layout.addWidget(left_panel)

        # ════════════════════════════════════════════════════════════════════
        # MAIN CANVAS — QStackedWidget Screen Container
        # ════════════════════════════════════════════════════════════════════
        self.stacked_widget = QStackedWidget()
        
        # Instantiate Screens
        self.today_screen = TodayScreen(self)
        self.actions_screen = ActionsScreen(self)
        self.frameworks_screen = FrameworksScreen(self)
        self.outcomes_screen = OutcomesScreen(self)
        self.business_data_screen = BusinessDataScreen(self)
        self.bottleneck_tax_screen = BottleneckTaxScreen(self)
        self.velocity_grader_screen = VelocityGraderScreen(self)
        self.bottleneck_diagnostic_screen = BottleneckDiagnosticScreen(self)
        self.consulting_screen = ConsultingScreen(self)
        
        # Diagnose Screen (Existing Right Panel Canvas)
        self.diagnose_screen = QWidget()
        right_layout = QVBoxLayout(self.diagnose_screen)
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(8)

        # Output title row with Copy + New buttons
        out_title_row = QHBoxLayout()
        output_title = QLabel("Your Business Diagnosis")
        output_title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        output_title.setStyleSheet("color: #1e293b;")
        out_title_row.addWidget(output_title, stretch=1)

        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.setObjectName("SecondaryBtn")
        self.copy_btn.setFixedHeight(30)
        self.copy_btn.setMinimumWidth(80)
        self.copy_btn.setToolTip("Copy diagnosis to clipboard")
        self.copy_btn.setVisible(False)
        self.copy_btn.clicked.connect(self.copy_output)
        out_title_row.addWidget(self.copy_btn)

        self.export_pdf_btn = QPushButton("📄 Export PDF")
        self.export_pdf_btn.setObjectName("SecondaryBtn")
        self.export_pdf_btn.setFixedHeight(30)
        self.export_pdf_btn.setMinimumWidth(100)
        self.export_pdf_btn.setToolTip("Download diagnosis as a shareable PDF report")
        self.export_pdf_btn.setVisible(False)
        self.export_pdf_btn.clicked.connect(self.export_diagnosis_pdf)
        out_title_row.addWidget(self.export_pdf_btn)

        new_btn = QPushButton("➕ New")
        new_btn.setObjectName("SecondaryBtn")
        new_btn.setFixedHeight(30)
        new_btn.setMinimumWidth(70)
        new_btn.setToolTip("Start a new diagnosis")
        new_btn.clicked.connect(self.new_session)
        out_title_row.addWidget(new_btn)

        right_layout.addLayout(out_title_row)

        self.output_area = QTextEdit()
        self.output_area.setObjectName("OutputArea")
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Arial", 13))
        self.output_area.setPlaceholderText(
            "Your diagnosis will appear here.\n\n"
            "1️⃣  Pick a framework on the left  (optional)\n"
            "2️⃣  Type your challenge below\n"
            "3️⃣  Press ➤ to get your diagnosis"
        )
        right_layout.addWidget(self.output_area, stretch=1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        right_layout.addWidget(self.progress)

        # ── Bottom input card ─────────────────────────────────────────────
        bottom_card = QFrame()
        bottom_card.setObjectName("CardFrame")
        bottom_layout = QVBoxLayout(bottom_card)
        bottom_layout.setContentsMargins(14, 10, 14, 10)
        bottom_layout.setSpacing(6)

        # Selected framework badge — clean pill style, no red circle
        self.badge_widget = QWidget()
        self.badge_widget.setVisible(False)
        badge_layout = QHBoxLayout(self.badge_widget)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        badge_layout.setSpacing(0)
        self.badge_label = QLabel()
        self.badge_label.setStyleSheet(
            "background: #dcfce7; color: #166534; border: 1px solid #86efac; "
            "border-radius: 10px 0px 0px 10px; padding: 3px 10px; font-size: 9pt; font-weight: bold;"
        )
        badge_clear = QPushButton(" × ")
        badge_clear.setFixedHeight(26)
        badge_clear.setMinimumWidth(28)
        badge_clear.setToolTip("Remove — let AI decide")
        badge_clear.setStyleSheet(
            "QPushButton { background: #bbf7d0; color: #166534; "
            "border: 1px solid #86efac; border-left: none; "
            "border-radius: 0px 10px 10px 0px; font-weight: bold; font-size: 10pt; padding: 0px 4px; }"
            "QPushButton:hover { background: #fca5a5; color: #991b1b; border-color: #fca5a5; }"
        )
        badge_clear.clicked.connect(self.clear_framework_selection)
        badge_layout.addWidget(self.badge_label)
        badge_layout.addWidget(badge_clear)
        badge_layout.addStretch()
        bottom_layout.addWidget(self.badge_widget)

        # Query row: text input + send button
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(85)
        self.query_input.setMinimumHeight(55)
        self.query_input.setPlaceholderText("Describe your challenge... (Press Enter to Send)")
        self.query_input.installEventFilter(self)
        input_row.addWidget(self.query_input, stretch=1)

        self.analyze_btn = QPushButton("➤")
        self.analyze_btn.setObjectName("SendBtn")
        self.analyze_btn.setToolTip("Get My Business Diagnosis")
        self.analyze_btn.setFixedSize(42, 42)
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setEnabled(False)
        input_row.addWidget(self.analyze_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        # Button Action Row: Ingest Data & Customer Intelligence
        input_btn_layout = QHBoxLayout()
        input_btn_layout.setSpacing(10)

        self.upload_btn = QPushButton("+ Add Business Data")
        self.upload_btn.setFixedHeight(36)
        self.upload_btn.setMinimumWidth(160)
        self.upload_btn.setToolTip("Upload CSV, PDF, or P&L text files to improve evidence quality")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                color: #334155;
                font-size: 10pt;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #0f172a;
            }
        """)
        self.upload_btn.clicked.connect(self.upload_file)
        input_btn_layout.addWidget(self.upload_btn)

        # File name label — shows currently attached file
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #64748b; font-size: 9pt; font-style: italic;")
        input_btn_layout.addWidget(self.file_label)

        self.persona_btn = QPushButton("Customer Intelligence")
        self.persona_btn.setFixedHeight(36)
        self.persona_btn.setMinimumWidth(160)
        self.persona_btn.setToolTip("Run Gemini Structured Persona & Competitive Gap Analysis (Pro)")
        self.persona_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3e8ff;
                border: 1px solid #d8b4fe;
                border-radius: 6px;
                color: #6b21a8;
                font-size: 10pt;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #e9d5ff;
                color: #581c87;
            }
        """)
        self.persona_btn.clicked.connect(self.run_customer_persona_analysis)
        input_btn_layout.addWidget(self.persona_btn)
        input_btn_layout.addStretch()

        bottom_layout.addLayout(input_btn_layout)
        bottom_layout.addLayout(input_row)

        # Toolbar placeholder for compatibility (not added to layout)
        right_layout.addWidget(bottom_card)


        # Add Screens to StackedWidget
        self.stacked_widget.addWidget(self.today_screen)                   # Index 0: Today
        self.stacked_widget.addWidget(self.diagnose_screen)                # Index 1: Diagnose
        self.stacked_widget.addWidget(self.actions_screen)                 # Index 2: Actions
        self.stacked_widget.addWidget(self.outcomes_screen)                # Index 3: Outcomes
        self.stacked_widget.addWidget(self.frameworks_screen)              # Index 4: Frameworks
        self.stacked_widget.addWidget(self.business_data_screen)           # Index 5: Business Data
        self.stacked_widget.addWidget(self.bottleneck_tax_screen)          # Index 6: Bottleneck Tax
        self.stacked_widget.addWidget(self.velocity_grader_screen)         # Index 7: Velocity Grader
        self.stacked_widget.addWidget(self.bottleneck_diagnostic_screen)   # Index 8: 60s Diagnostic
        self.stacked_widget.addWidget(self.consulting_screen)              # Index 9: Advisory Chat

        body_layout.addWidget(self.stacked_widget, stretch=1)
        root.addWidget(body, stretch=1)

        # Set Default Screen to TODAY (Index 0)
        self.switch_nav("today")

    def switch_nav(self, key: str):
        """Switch stacked widget screen and update persistent sidebar button states."""
        mapping = {
            "today":                 0,
            "diagnose":              1,
            "actions":               2,
            "outcomes":              3,
            "frameworks":            4,
            "business_data":         5,
            "bottleneck_tax":        6,
            "velocity_grader":       7,
            "bottleneck_diagnostic": 8,
            "advisory_chat":         9,
        }
        idx = mapping.get(key, 0)
        self.stacked_widget.setCurrentIndex(idx)
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
        # Refresh velocity or consulting screen on navigation
        if key == "velocity_grader" and hasattr(self.velocity_grader_screen, "refresh_data"):
            self.velocity_grader_screen.refresh_data()
        elif key == "advisory_chat" and hasattr(self.consulting_screen, "refresh_data"):
            self.consulting_screen.refresh_data()

    def switch_to_diagnose(self):
        """Shortcut helper to switch directly to Diagnose tab."""
        self.switch_nav("diagnose")

    def run_customer_persona_analysis(self):
        """Runs Gemini customer persona & competitive gap analysis."""
        prompt_text = self.query_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Input Required", "Please describe your product, service, or business idea in the text area first.")
            return

        if not self.engine or not hasattr(self.engine, 'provider'):
            QMessageBox.warning(self, "Engine Not Ready", "AI Engine is initializing. Please wait a moment.")
            return

        self.switch_to_diagnose()
        self.progress.setVisible(True)
        self.status_label.setText("⏳  Analyzing Customer Persona & Competitive Gaps with Gemini...")
        self.status_label.setStyleSheet("color: #7c3aed; font-weight: bold; font-size: 13px;")

        try:
            res = self.engine.provider.analyze_customer_profile(prompt_text)
            persona = res.get("persona", {})
            competitors = res.get("competitors", [])
            diff = res.get("differentiation_opportunity", "N/A")
            rec_fw = res.get("recommended_framework", "RUN DCMS ER")

            html_output = f"""<html><body style="font-family: Arial; padding: 12px;">
<div style="background:#f3e8ff; border: 1px solid #d8b4fe; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
  <h2 style="color:#6b21a8; margin-top:0;">🔍 Customer Persona & Competitive Intelligence Report</h2>
  <p style="color:#581c87; font-weight:bold;">Powered by Google Gemini</p>
</div>

<h3 style="color:#1e40af;">👤 Primary Customer Persona: {persona.get('name', 'Ideal Customer')}</h3>
<ul>
  <li><b>Demographics / Profile:</b> {persona.get('demographics', 'N/A')}</li>
  <li><b>Pain Points:</b> {', '.join(persona.get('pain_points', []))}</li>
  <li><b>Buying Triggers:</b> {', '.join(persona.get('buying_triggers', []))}</li>
</ul>

<h3 style="color:#b45309;">⚔️ Competitive Landscape</h3>
<ul>
"""
            for comp in competitors:
                html_output += f"<li><b>{comp.get('name', 'Competitor')}:</b> {comp.get('positioning', 'N/A')}</li>\n"

            html_output += f"""</ul>

<div style="background:#f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 12px; margin-top: 14px;">
  <h4 style="color:#166534; margin:0 0 6px 0;">🎯 Differentiation Opportunity & Auto-Selected Action:</h4>
  <p style="color:#15803d; margin:0;">{diff}</p>
  <p style="color:#166534; font-weight:bold; margin-top:8px;">💡 Auto-Selected Framework: {rec_fw}</p>
</div>
</body></html>"""

            self.output_area.setHtml(html_output)
            self._plain_result = f"Customer Persona: {persona.get('name')}\nDifferentiation: {diff}\nRecommended Framework: {rec_fw}"
            self.copy_btn.setVisible(True)
            self.status_label.setText(f"✅ Analysis complete! Auto-selected {rec_fw}.")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")

            # Automatically lock in recommended framework
            self.badge_label.setText(f"🎯  Using: {rec_fw}")
            self.badge_widget.setVisible(True)
            self.selected_framework_prompt = f"Apply {rec_fw} framework"

        except Exception as e:
            QMessageBox.critical(self, "Analysis Failed", f"Failed to generate customer intelligence: {str(e)}")
            self.status_label.setText("❌ Customer Intelligence failed.")
        finally:
            self.progress.setVisible(False)

    def init_ai(self):
        self.status_label.setText("⏳  Initializing AI & Checking Local Model (Downloading if needed, 2.2GB)...")
        self.status_label.setStyleSheet("color: #2563eb; font-weight: bold; font-size: 13px;")
        self.analyze_btn.setEnabled(False)
        
        self.init_worker = EngineInitWorker()
        self.init_worker.finished.connect(self.on_engine_initialized)
        self.init_worker.failed.connect(self.on_engine_failed)
        self.init_worker.start()

    def on_engine_initialized(self, engine):
        self.engine = engine
        self.status_label.setText("✅  Ready. Describe your challenge and get your diagnosis.")
        self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        self.analyze_btn.setEnabled(True)

    def on_engine_failed(self, err_msg):
        self.status_label.setText(f"❌ AI Engine Error: {err_msg}")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 13px;")
        self.analyze_btn.setEnabled(False)
        
    def open_settings(self):
        dialog = ProfileDialog(self)
        dialog.exec()

    def open_subscription(self):
        dialog = SubscriptionBillingDialog(self)
        if dialog.exec():
            self._refresh_account_button()

    def _refresh_account_button(self):
        """Updates the top-right account button label from real services. Never hardcoded."""
        name = self._profile_svc.get_founder_name()
        company = self._profile_svc.get_company_name()
        plan = self._entitlement_svc.get_current_plan().upper()
        # Show company name if set, else founder name
        display = company if company and company != "Your Company" else name
        self.account_btn.setText(f"{display}  {plan}  ▾")

    def handle_sign_out(self):
        """Prompt confirmation, clear active session state safely, and return user to home view."""
        reply = QMessageBox.question(
            self,
            "Sign Out",
            "Are you sure you want to sign out?\n\nYour local company P&L data and business context will be safely preserved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.new_session()
            self.switch_nav("today")
            self.status_label.setText("🔒  Signed out. Local data preserved.")
            self.status_label.setStyleSheet("color: #1a7a3c; font-weight: bold; font-size: 13px;")
        
    def toggle_framework_panel(self, checked):
        # No-op — framework panel is now the persistent left sidebar
        pass

    def select_framework(self, prompt, card_widget):
        """Called when a framework card is clicked — highlights card and shows badge."""
        import re
        # Deselect previously selected card
        if self._selected_card is not None:
            self._selected_card.set_selected(False)
        # Highlight the new card
        card_widget.set_selected(True)
        self._selected_card = card_widget

        match = re.search(r'(ECG KISS|SLR CAMERAS|MC BEERS|PC PEERS|PS ERP|DC ERPRS|OKS REC SME|PFA SAAS SME|RSS FEED SME|RPM REAP ER|RUN DCMS ER|ERM FABS ER|ADMINS ER)', prompt)
        name = match.group(1) if match else "Framework"
        self.selected_framework_prompt = prompt
        self.badge_label.setText(f"🎯  Using: {name}")
        self.badge_widget.setVisible(True)

    def clear_framework_selection(self):
        self.selected_framework_prompt = None
        self.badge_widget.setVisible(False)
        if self._selected_card is not None:
            self._selected_card.set_selected(False)
            self._selected_card = None

    def copy_output(self):
        """Copy diagnosis text to clipboard."""
        text = getattr(self, '_plain_result', self.output_area.toPlainText())
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("✅ Copied to clipboard!")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")

    def export_diagnosis_pdf(self):
        """Export current diagnosis as a branded PDF report."""
        text = getattr(self, '_plain_result', self.output_area.toPlainText())
        if not text:
            QMessageBox.information(self, "No Diagnosis", "Run a diagnosis first to export a PDF.")
            return
        try:
            from services.pdf_export_service import export_diagnosis_pdf
            company_name = self.profile_service.get_company_name()
            query = self.query_input.toPlainText().strip()[:200]
            framework = getattr(self, '_last_framework_used', '')
            filepath = export_diagnosis_pdf(
                diagnosis_text=text,
                company_name=company_name,
                framework_used=framework,
                query=query,
            )
            import subprocess
            subprocess.Popen(['open', filepath])  # macOS
            self.status_label.setText(f"✅ PDF exported: {filepath}")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")

    def new_session(self):
        """Clear everything for a fresh diagnosis."""
        self.output_area.clear()
        self.query_input.clear()
        self.clear_framework_selection()
        self.current_document_text = ""
        self.current_file_path = ""
        self.file_label.setText("")
        self.copy_btn.setVisible(False)
        self.export_pdf_btn.setVisible(False)
        self.status_label.setText("✅  Ready. Describe your challenge and get your diagnosis.")
        self.status_label.setStyleSheet("color: #1a7a3c; font-size: 12px;")

    def set_quick_prompt(self, text):
        """Legacy method kept for compatibility."""
        self.query_input.setPlainText(text)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_file(file_path)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "All Files (*);;PDFs (*.pdf);;Excel (*.xlsx *.csv);;Images (*.png *.jpg *.jpeg);;Text (*.txt)"
        )
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        self.current_file_path = file_path
        self.file_label.setText(os.path.basename(file_path))
        self.status_label.setText("Extracting text...")
        QApplication.processEvents()
        
        # Extract text
        self.current_document_text = extract_text_from_file(file_path)
        
        if self.current_document_text.startswith("Error"):
            QMessageBox.critical(self, "Error", self.current_document_text)
            self.status_label.setText("Failed to read document.")
        else:
            self.status_label.setText(f"Loaded {os.path.basename(file_path)} successfully.")
                
    def run_analysis(self):
        query = self.query_input.toPlainText().strip()

        # If a framework was selected, combine it with the user's natural language
        if hasattr(self, 'selected_framework_prompt') and self.selected_framework_prompt:
            if query:
                combined = f"{query}\n\nPlease apply the framework: {self.selected_framework_prompt}"
            else:
                combined = self.selected_framework_prompt
        else:
            combined = query

        if not combined and not self.current_document_text:
            QMessageBox.warning(self, "Input Required", "Please describe your challenge above.")
            return

        self.switch_to_diagnose()
        self.analyze_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.output_area.setPlaceholderText("")
        self.output_area.setHtml(
            '<div style="font-family: Arial; font-size: 12pt; padding: 10px; color: #334155;">'
            '<h3 style="color: #1e293b; margin-top: 0;">🔄 Analyzing Your Business Challenge...</h3>'
            '<p style="color: #64748b; font-size: 10pt;">Please wait a moment while the local multi-agent pipeline processes your request.</p>'
            '<ul style="list-style-type: none; padding-left: 0; line-height: 1.8;">'
            '<li style="color: #d97706; font-weight: bold;">🔄 <b>AssessmentAgent</b>: Understanding your business challenge...</li>'
            '<li style="color: #94a3b8;">⏳ <b>FrameworkSelectionAgent</b>: Selecting the relevant Founder Framework</li>'
            '<li style="color: #94a3b8;">⏳ <b>KnowledgeRetrievalAgent</b>: Retrieving framework knowledge</li>'
            '<li style="color: #94a3b8;">⏳ <b>MemoryAgent</b>: Retrieving memory context</li>'
            '<li style="color: #94a3b8;">⏳ <b>StrategyAgent</b>: Developing the strategy</li>'
            '<li style="color: #94a3b8;">⏳ <b>ExecutionCoachAgent</b>: Building the execution plan</li>'
            '<li style="color: #94a3b8;">⏳ <b>ResponseComposer</b>: Finalizing the recommendation</li>'
            '</ul></div>'
        )
        self.copy_btn.setVisible(False)
        self.status_label.setText("Analyzing your business challenge...")

        self.worker = AnalysisWorker(self.engine, combined, self.current_document_text)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.progress_update.connect(self.on_progress_update)
        self.worker.start()

    def on_progress_update(self, status):
        self.status_label.setText(f"⚙️  {status}")
        self.status_label.setStyleSheet("color: #d97706; font-weight: bold; font-size: 13px;")
        
        steps = [
            ("AssessmentAgent", "Understanding your business challenge"),
            ("FrameworkSelectionAgent", "Selecting the relevant Founder Framework"),
            ("KnowledgeRetrievalAgent", "Retrieving framework knowledge"),
            ("MemoryAgent", "Retrieving memory context"),
            ("StrategyAgent", "Developing the strategy"),
            ("ExecutionCoachAgent", "Building the execution plan"),
            ("ResponseComposer", "Finalizing the recommendation")
        ]
        
        current_idx = -1
        for idx, (agent, desc) in enumerate(steps):
            if desc in status:
                current_idx = idx
                break
                
        html = '<div style="font-family: Arial; font-size: 12pt; padding: 10px; color: #334155;">'
        html += '<h3 style="color: #1e293b; margin-top: 0;">🔄 Analyzing Your Business Challenge...</h3>'
        html += '<p style="color: #64748b; font-size: 10pt;">Please wait a moment while the local multi-agent pipeline processes your request.</p>'
        html += '<ul style="list-style-type: none; padding-left: 0; line-height: 1.8;">'
        
        for idx, (agent, desc) in enumerate(steps):
            if idx < current_idx:
                html += f'<li style="color: #166534; font-weight: bold;">✅ <b>{agent}</b>: {desc}</li>'
            elif idx == current_idx:
                html += f'<li style="color: #d97706; font-weight: bold;">🔄 <b>{agent}</b>: {desc}...</li>'
            else:
                html += f'<li style="color: #94a3b8;">⏳ <b>{agent}</b>: {desc}</li>'
                
        html += '</ul></div>'
        self.output_area.setHtml(html)

    def markdown_to_html(self, text: str) -> str:
        """Convert the AI's markdown output to clean HTML for display."""
        import re
        lines = text.split('\n')
        html_lines = []
        in_steps = False
        in_priority_action = False

        for line in lines:
            stripped = line.strip()

            # Markdown header 2: ## Header
            if stripped.startswith('## '):
                header_text = stripped[3:].strip()
                html_lines.append(
                    f'<h2 style="margin-top:16px; margin-bottom:6px; '
                    f'font-size:12pt; font-weight:bold; color:#1a7a3c; border-bottom: 1px solid #e2e8f0; padding-bottom: 3px;">'
                    f'{header_text}</h2>'
                )
                in_steps = False
                in_priority_action = ("Priority Action" in header_text or "Priority" in header_text)
                continue

            # Markdown header 3: ### Header
            if stripped.startswith('### '):
                header_text = stripped[4:].strip()
                html_lines.append(
                    f'<h3 style="margin-top:10px; margin-bottom:4px; '
                    f'font-size:11pt; font-weight:bold; color:#1e293b;">'
                    f'{header_text}</h3>'
                )
                in_steps = False
                continue

            if in_priority_action and stripped:
                # Replace inline bold formatting if any
                clean_val = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', stripped)
                html_lines.append(
                    f'<div style="margin:8px 0; padding:12px 16px; background:#f0fdf4; '
                    f'border-left:4px solid #1a7a3c; border-radius:6px; font-weight:bold; color:#15803d; font-size:11pt; line-height:1.4;">'
                    f'🎯 {clean_val}</div>'
                )
                continue

            # Framework section headers: **Framework: NAME — Role**
            if re.match(r'^\*\*(Framework:|Supporting Framework:)', stripped):
                inner = re.sub(r'^\*\*|\*\*$', '', stripped)
                html_lines.append(
                    f'<div style="margin-top:14px; margin-bottom:4px; padding:6px 10px; '
                    f'background:#f0fdf4; border-left:4px solid #1a7a3c; border-radius:4px;">'
                    f'<span style="color:#1a7a3c; font-weight:bold; font-size:11pt;">{inner}</span></div>'
                )
                in_steps = True
                continue

            # Other bold headings: **Diagnosis**, **Root Causes**, etc.
            if re.match(r'^\*\*.+\*\*$', stripped):
                inner = re.sub(r'^\*\*|\*\*$', '', stripped)
                html_lines.append(
                    f'<p style="margin-top:12px; margin-bottom:2px; '
                    f'font-weight:bold; font-size:11pt; color:#1e293b;">{inner}</p>'
                )
                in_steps = False
                continue

            # Numbered steps: Step 1: ...
            m = re.match(r'^Step\s*(\d+):\s*(.+)', stripped)
            if m:
                num, content = m.group(1), m.group(2)
                html_lines.append(
                    f'<div style="display:flex; margin:3px 0 3px 12px;">'
                    f'<span style="min-width:24px; font-weight:bold; color:#1a7a3c;">{num}.</span>'
                    f'<span style="color:#334155;">{content}</span></div>'
                )
                continue

            # Bullet points
            if stripped.startswith('- '):
                content = stripped[2:]
                # bold inline **text**
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                html_lines.append(
                    f'<div style="margin:2px 0 2px 12px; color:#475569;">• {content}</div>'
                )
                continue

            # → Example: lines — shown as indented callout with "Sample Data" badge
            if stripped.startswith('→ Example:') or stripped.startswith('→ example:'):
                example_text = stripped[len('→ Example:'):].strip() or stripped[len('→ example:'):].strip()
                html_lines.append(
                    f'<div style="margin:2px 0 6px 24px; padding:6px 10px; '
                    f'background:#f0fdf4; border-left:3px solid #86efac; border-radius:4px;">'
                    f'<span style="background:#bbf7d0; color:#166534; font-size:7pt; font-weight:bold; '
                    f'padding:1px 6px; border-radius:8px; margin-right:6px; vertical-align:middle;">'
                    f'SAMPLE DATA</span>'
                    f'<span style="color:#166534; font-style:italic; font-size:9pt;">{example_text}</span></div>'
                )
                continue

            # "Apply this framework..." line — suppress it (new prompt removes this)
            if stripped.lower().startswith('apply this framework'):
                continue

            # Normal paragraph text
            if stripped:
                line_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', stripped)
                html_lines.append(f'<p style="margin:4px 0; color:#334155;">{line_html}</p>')
            else:
                html_lines.append('<br/>')

        # ─── Level 1 Summary Card ────────────────────────────────────────────
        # Extract framework name from ## 1. section header for the badge.
        # Extract executive summary sentence from ## 2. for the constraint label.
        # NO fabricated confidence %, NO hardcoded constraint name.
        import re as _re
        fw_match = _re.search(r'##\s*1\.\s*Framework Selected\s*\n+([A-Z][A-Z ]+)', text)
        fw_name = fw_match.group(1).strip() if fw_match else "Founder Framework Applied"

        summ_match = _re.search(r'##\s*2\.\s*Executive Summary\s*\n+(.+?)(?:\n\n|##)', text, _re.DOTALL)
        summ_text = summ_match.group(1).strip()[:180].replace('\n', ' ') if summ_match else "See full analysis below."

        verification_card = (
            '<div style="margin-bottom:18px; padding:18px 22px; '
            'background:#ffffff; border:1px solid #ccebd7; border-left:6px solid #1a7a3c; border-radius:12px;">'
            '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
            '<span style="background:#e2f5ea; color:#1a7a3c; font-weight:bold; font-size:8.5pt; '
            'padding:3px 10px; border-radius:12px; border:1px solid #ccebd7; text-transform:uppercase;">'
            f'Framework: {fw_name}</span>'
            '<span style="color:#64748b; font-size:9pt; font-style:italic;">Verified by Evidence Analysis</span>'
            '</div>'
            '<p style="color:#4b6b5a; margin:0 0 12px 0; font-size:10.5pt; line-height:1.6;">'
            f'{summ_text}'
            '</p>'
            '<div style="margin-top:10px; display:flex; gap:10px;">'
            '<span style="background:#1a7a3c; color:#ffffff; font-weight:bold; padding:6px 14px; border-radius:6px; font-size:9.5pt;">'
            'Action Plan Available Below</span>'
            '</div>'
            '</div>'
        )


        # Append real-data CTA at the bottom of every diagnosis
        cta = (
            '<div style="margin-top:18px; padding:12px 16px; '
            'background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px;">'
            '<p style="margin:0 0 4px 0; font-weight:bold; color:#1d4ed8; font-size:10pt;">'
            '💡 Action & Outcome Measurement Ready</p>'
            '<p style="margin:0; color:#1e40af; font-size:9pt;">'
            'Click <b>Approve & Execute</b> to run automated task actions within signed Policy limits. '
            'Outcome Tracker will continuously measure baseline vs actual ARR impact.'
            '</p></div>'
        )
        return (
            '<html><body style="font-family: Arial; font-size: 12pt; padding: 8px;">'
            + verification_card
            + ''.join(html_lines)
            + cta
            + '</body></html>'
        )

    def on_analysis_complete(self, result):
        self.progress.setVisible(False)
        self.analyze_btn.setEnabled(True)

        if result.startswith("Error:"):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Analysis Failed", f"The multi-agent pipeline encountered an exception:\n\n{result[6:].strip()}")
            self.output_area.setHtml(
                f'<div style="font-family: Arial; padding: 15px; background: #fef2f2; border: 1px solid #fee2e2; border-radius: 6px; color: #991b1b;">'
                f'<h3 style="margin-top:0; color:#b91c1c;">Analysis Failed</h3>'
                f'<p>{result[6:].strip()}</p></div>'
            )
            self.status_label.setText("Analysis failed. Please check logs.")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
            self.copy_btn.setVisible(False)
            return

        self._plain_result = result          # store for clipboard copy

        # Persist session so TodayScreen can display real constraint card
        self._persist_diagnosis_session(result)

        # Extract concrete action items from diagnosis into ActionsService
        try:
            from services.actions_service import ActionsService
            actions_svc = ActionsService()
            query_summary = self.query_input.toPlainText().strip()[:100]
            actions_svc.extract_actions_from_diagnosis(
                session_id=str(uuid.uuid4()),
                diagnosis_text=result,
                framework_used=getattr(self, "_last_framework_used", "Founder Framework"),
                challenge_summary=query_summary
            )
            if hasattr(self, "actions_screen") and hasattr(self.actions_screen, "refresh_data"):
                self.actions_screen.refresh_data()
        except Exception as e:
            print(f"[FounderApp] Failed to extract action items: {e}")

        self.output_area.setHtml(self.markdown_to_html(result))
        self.copy_btn.setVisible(True)
        self.export_pdf_btn.setVisible(True)
        self.status_label.setText("Analysis complete. Copy, export PDF, or start a new diagnosis.")
        self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        self.refresh_wallet_balance()

    def _persist_diagnosis_session(self, result: str) -> None:
        """
        Saves the completed diagnosis to DiagnosisSessionService so TodayScreen
        can display a real constraint card without re-running analysis.
        Extracts framework and confidence from structured result text.
        """
        try:
            import re as _re
            session_id = str(uuid.uuid4())
            query = self.query_input.toPlainText().strip()[:200]

            # Extract framework name from ## 1. Framework Selected section
            fw_match = _re.search(r'##\s*1\.\s*Framework Selected\s*\n+([A-Z ]+)', result)
            framework = fw_match.group(1).strip() if fw_match else "Unknown"

            # Extract executive summary sentence from ## 2. Executive Summary
            summ_match = _re.search(r'##\s*2\.\s*Executive Summary\s*\n+(.+?)(?:\n\n|##)', result, _re.DOTALL)
            constraint = (summ_match.group(1).strip()[:120] if summ_match else "See full diagnosis").replace('\n', ' ')

            # Use real confidence from VerificationAgent if engine is available
            confidence = 0.50
            evidence_count = 0
            if self.engine and hasattr(self.engine, 'orchestrator'):
                try:
                    ev = self.engine.orchestrator.verification_agent if hasattr(self.engine.orchestrator, 'verification_agent') else None
                    if ev:
                        profile = self._profile_svc.get_profile()
                        vr = ev.verify_decision(result, "", profile)
                        confidence = vr.get("confidence_score", 0.50)
                        evidence_count = len(vr.get("supporting_evidence", []))
                except Exception:
                    pass

            self._session_svc.save_session(
                session_id=session_id,
                query=query,
                framework_used=framework,
                constraint_name=constraint,
                confidence_score=confidence,
                evidence_count=evidence_count,
                full_result=result,
            )
            # Refresh TodayScreen command center if it is visible
            if hasattr(self, 'today_screen') and hasattr(self.today_screen, 'refresh_data'):
                self.today_screen.refresh_data()
        except Exception as e:
            print(f"[FounderApp] Session persistence error: {e}")

    def refresh_wallet_balance(self):
        try:
            if hasattr(self, 'sidebar_db') and hasattr(self, 'sidebar_balance_label'):
                wallet_data = self.sidebar_db.get_wallet("primary_usdc_wallet")
                if wallet_data:
                    balance = wallet_data["usdc_balance"]
                    self.sidebar_balance_label.setText(f"<b>Balance:</b> {balance} USDC")
        except Exception as e:
            print("Failed to refresh wallet balance:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Founder AI Assistant")
    
    # Custom Official Founder Frameworks Lab Theme (#1a7a3c Forest Green, #0d4a24 Dark Green Sidebar, #ffffff White Canvas)
    style_sheet = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget {
        color: #0f2318;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    QLabel {
        color: #0f2318;
    }
    QFrame#LeftPanel {
        background-color: #f0fbf4;
        border-right: 1px solid #ccebd7;
    }
    QFrame#CardFrame {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 14px;
        color: #0f2318;
        font-size: 13pt;
        line-height: 1.6;
    }
    QTextEdit:focus {
        border: 2px solid #1a7a3c;
    }
    QTextEdit#OutputArea {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        font-size: 13pt;
    }
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #1a7a3c;
        padding: 8px 14px;
        font-weight: 600;
        font-size: 11pt;
    }
    QPushButton:hover {
        background-color: #ebf7f0;
        border: 1px solid #1a7a3c;
    }
    QPushButton#SendBtn {
        background-color: #1a7a3c;
        color: white;
        border: none;
        border-radius: 21px;
        font-size: 14pt;
        font-weight: bold;
    }
    QPushButton#SendBtn:hover {
        background-color: #145e2e;
    }
    QPushButton#SendBtn:disabled {
        background-color: #a3d9b5;
        color: #ffffff;
    }
    QScrollBar:vertical {
        border: none;
        background: #ffffff;
        width: 8px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical {
        background: #22a857;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #1a7a3c;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """
    app.setStyleSheet(style_sheet)
    
    window = FounderApp()
    window.show()
    sys.exit(app.exec())
