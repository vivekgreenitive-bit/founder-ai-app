import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                             QFrame, QComboBox, QScrollArea, QSizePolicy, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence

from document_processor import extract_text_from_file
from ai_engine import FounderAIEngine


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
                    background-color: {self.bg};
                    border: 2px solid {self.color};
                    border-left: 5px solid {self.color};
                    border-radius: 6px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ClickableCard {{
                    background-color: white;
                    border: 1px solid {self.border};
                    border-left: 4px solid {self.color};
                    border-radius: 6px;
                }}
                ClickableCard:hover {{
                    background-color: {self.bg};
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
        
        # Trigger reload of LLM in active application parent
        if self.parent() and hasattr(self.parent(), "init_ai"):
            self.parent().init_ai()
            
        super().accept()


class FounderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Founder AI Assistant")
        self.setMinimumSize(960, 640)

        # Size the window to fit the screen naturally — desktop app feel
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = min(1280, int(screen.width() * 0.90))
        h = min(820, int(screen.height() * 0.90))
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
        # Automated onboarding: Force profile setup if it doesn't exist
        if not os.path.exists("company_profile.json"):
            QMessageBox.information(self, "Welcome", "Welcome to Founder AI! Let's set up your Company Profile first so the AI can provide personalized advice.")
            self.open_settings()
           
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

        self.settings_btn = QPushButton("⚙️ Profile")
        self.settings_btn.setToolTip("Set Company Context")
        self.settings_btn.setFixedSize(100, 34)
        self.settings_btn.setStyleSheet(
            "QPushButton { background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; "
            "border-radius: 8px; font-size: 10pt; }"
            "QPushButton:hover { background: #e2e8f0; color: #0f172a; }"
        )
        self.settings_btn.clicked.connect(self.open_settings)
        header_bar_layout.addWidget(self.settings_btn)
        root.addWidget(header_bar)

        # ── Two-panel body ────────────────────────────────────────────────────
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # ════════════════════════════════════════════════════════════════════
        # LEFT PANEL — Framework Navigator
        # ════════════════════════════════════════════════════════════════════
        left_panel = QFrame()
        left_panel.setObjectName("LeftPanel")
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet("""
            QFrame#LeftPanel {
                background-color: #f8fafc;
                border-right: 1px solid #e2e8f0;
                border: none;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_title = QLabel("  Choose a Framework")
        left_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        left_title.setFixedHeight(38)
        left_title.setStyleSheet(
            "color: #475569; background: #f1f5f9; "
            "border-bottom: 1px solid #e2e8f0; padding-left: 10px;"
        )
        left_layout.addWidget(left_title)

        # Scrollable list of all categories + cards
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_scroll.setStyleSheet("background: #f8fafc; border: none;")

        sidebar_content = QWidget()
        sidebar_content.setStyleSheet("background: #f8fafc;")
        sidebar_inner = QVBoxLayout(sidebar_content)
        sidebar_inner.setContentsMargins(5, 5, 5, 5)
        sidebar_inner.setSpacing(2)

        categories = [
            {
                "title": "🗓  PLANNING",
                "color": "#1a7a3c",
                "bg": "#f0fdf4",
                "border": "#bbf7d0",
                "items": [
                    ("ECG KISS", "Overall Business Diagnostic", "Define your end goal, identify gaps, and simulate solutions.", "Run the ECG KISS overall business diagnosis on my situation and identify my biggest operational gap."),
                    ("SLR CAMERAS", "Yearly Planning", "Plan your yearly milestones, allocate resources, schedule.", "Apply the SLR CAMERAS framework to help me build a structured yearly plan for my business."),
                    ("MC BEERS", "Quarterly Planning", "Break down quarterly goals into sprints.", "Use the MC BEERS framework to break down my goals into a 90-day execution sprint."),
                    ("PC PEERS", "Monthly Planning", "Manage monthly priorities, people, execution checkpoints.", "Apply the PC PEERS framework to create a focused monthly planning structure for my team."),
                    ("PS ERP", "Weekly Planning", "Organize weekly focus so you stop wasting time on low-value tasks.", "Use the PS ERP framework to organize my weekly priorities and stop wasting time on low-value tasks."),
                    ("DC ERPRS", "Daily Planning", "Structure each day to maximize output and create momentum.", "Apply the DC ERPRS framework to structure my daily schedule and make every day count."),
                ]
            },
            {
                "title": "⚙️  OPERATIONS",
                "color": "#b45309",
                "bg": "#fffbeb",
                "border": "#fde68a",
                "items": [
                    ("OKS REC SME", "Business System Architecture", "Build systems that run without you.", "Use the OKS REC SME framework to design a system that removes me as the bottleneck."),
                    ("PFA SAAS SME", "Business Process Mapping", "Define and streamline core business processes.", "Apply the PFA SAAS SME framework to document and optimize a core business process."),
                    ("RSS FEED SME", "SOP Builder", "Create SOPs so your team executes consistently.", "Use the RSS FEED SME framework to create an SOP so my team stops making errors on routine tasks."),
                ]
            },
            {
                "title": "🚀  EXECUTION",
                "color": "#1d4ed8",
                "bg": "#eff6ff",
                "border": "#bfdbfe",
                "items": [
                    ("RPM REAP ER", "Business Execution Strategy", "Diagnose why execution is failing.", "Apply the RPM REAP ER framework to diagnose why my execution is breaking down and fix it."),
                    ("RUN DCMS ER", "Revenue Generation", "Identify and fix revenue leaks.", "Use the RUN DCMS ER framework to find and fix the revenue leaks in my business."),
                    ("ERM FABS ER", "Business Evaluation", "Evaluate what is working and what needs to change.", "Apply the ERM FABS ER framework to evaluate what is working and what needs to change immediately."),
                    ("ADMINS ER", "Crisis Management", "Manage an active business crisis with a clear plan.", "Use the ADMINS ER framework to help me manage the current crisis in my business."),
                ]
            },
        ]

        for idx, cat in enumerate(categories):
            # Add spacing before every section except the first
            if idx > 0:
                sidebar_inner.addSpacing(8)

            # Category header — compact pill label
            cat_header = QLabel(cat["title"])
            cat_header.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            cat_header.setFixedHeight(22)
            cat_header.setStyleSheet(
                f"color: {cat['color']}; background: {cat['bg']}; "
                f"border: 1px solid {cat['border']}; border-radius: 4px; "
                f"padding-left: 8px; letter-spacing: 1px;"
            )
            sidebar_inner.addWidget(cat_header)

            # Framework cards — tightly spaced
            for name, subtitle, desc, prompt in cat["items"]:
                fw_card = ClickableCard(
                    name, subtitle, desc, prompt,
                    cat["color"], cat["bg"], cat["border"],
                    self.select_framework
                )
                self._all_sidebar_cards.append(fw_card)
                sidebar_inner.addWidget(fw_card)

        # No addStretch — cards expand to fill the full sidebar height on any screen
        sidebar_scroll.setWidget(sidebar_content)
        left_layout.addWidget(sidebar_scroll)
        body_layout.addWidget(left_panel)

        # ════════════════════════════════════════════════════════════════════
        # RIGHT PANEL — Output + Input
        # ════════════════════════════════════════════════════════════════════
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
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
        bottom_layout.addLayout(input_row)

        # Toolbar placeholder for compatibility (not added to layout)
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #64748b; font-style: italic; font-size: 9pt;")

        right_layout.addWidget(bottom_card)

        body_layout.addWidget(right_panel, stretch=1)
        root.addWidget(body, stretch=1)

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

    def new_session(self):
        """Clear everything for a fresh diagnosis."""
        self.output_area.clear()
        self.query_input.clear()
        self.clear_framework_selection()
        self.current_document_text = ""
        self.current_file_path = ""
        self.file_label.setText("")
        self.copy_btn.setVisible(False)
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

        # Append real-data CTA at the bottom of every diagnosis
        cta = (
            '<div style="margin-top:18px; padding:12px 16px; '
            'background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px;">'
            '<p style="margin:0 0 4px 0; font-weight:bold; color:#1d4ed8; font-size:10pt;">'
            '💡 These examples use sample data.</p>'
            '<p style="margin:0; color:#1e40af; font-size:9pt;">'
            'Share your real numbers — revenue, team size, costs, timelines — '
            'in the input below and I will apply each framework step directly to your actual situation.'
            '</p></div>'
        )
        return (
            '<html><body style="font-family: Arial; font-size: 12pt; padding: 8px;">'
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
                f'<h3 style="margin-top:0; color:#b91c1c;">⚠️ Analysis Failed</h3>'
                f'<p>{result[6:].strip()}</p></div>'
            )
            self.status_label.setText("❌ Analysis failed. Please check logs.")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
            self.copy_btn.setVisible(False)
            return

        self._plain_result = result          # store for clipboard copy
        self.output_area.setHtml(self.markdown_to_html(result))
        self.copy_btn.setVisible(True)
        self.status_label.setText("✅  Analysis complete. Copy or start a new diagnosis.")
        self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Founder AI Assistant")
    
    # Custom StyleSheet based on founderframeworkslab.com theme
    style_sheet = """
    QMainWindow {
        background-color: #f1f5f9;
    }
    QLabel {
        color: #0f172a;
    }
    QFrame#LeftPanel {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    QFrame#CardFrame {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px;
        color: #334155;
        font-family: Arial;
        font-size: 14pt;
    }
    QTextEdit:focus {
        border: 2px solid #1a7a3c;
    }
    QTextEdit#OutputArea {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        font-size: 14pt;
        line-height: 1.5;
    }
    QPushButton {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        color: #0f172a;
        padding: 10px 16px;
        font-weight: bold;
        font-size: 13pt;
    }
    QPushButton:hover {
        background-color: #f8fafc;
        border: 1px solid #94a3b8;
    }
    QPushButton#SecondaryBtn {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
    }
    QPushButton#SecondaryBtn:hover {
        background-color: #e2e8f0;
    }
    /* Pill-shaped suggestion chips */
    QPushButton#ChipBtn {
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        color: #475569;
        padding: 8px 16px;
        font-size: 12pt;
        font-weight: normal;
    }
    QPushButton#ChipBtn:hover {
        background-color: #e2e8f0;
        color: #0f172a;
        border: 1px solid #cbd5e1;
    }
    /* Special styling for the main action button */
    QPushButton#AnalyzeBtn {
        background-color: #1a7a3c;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 16px;
        font-size: 16pt;
        font-weight: bold;
    }
    QPushButton#AnalyzeBtn:hover {
        background-color: #145c2d;
    }
    QPushButton#AnalyzeBtn:disabled {
        background-color: #94a3b8;
    }
    /* Framework toggle button */
    QPushButton#FwToggleBtn {
        background-color: #f8fafc;
        color: #475569;
        border: 1.5px dashed #cbd5e1;
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 11pt;
        text-align: left;
    }
    QPushButton#FwToggleBtn:hover {
        background-color: #f1f5f9;
        border-color: #1a7a3c;
        color: #1a7a3c;
    }
    QPushButton#FwToggleBtn:checked {
        background-color: #f0fdf4;
        border-color: #1a7a3c;
        color: #1a7a3c;
        border-style: solid;
    }
    /* Inline send button */
    QPushButton#SendBtn {
        background-color: #1a7a3c;
        color: white;
        border: none;
        border-radius: 21px;
        font-size: 16pt;
        font-weight: bold;
    }
    QPushButton#SendBtn:hover {
        background-color: #145c2d;
    }
    QPushButton#SendBtn:disabled {
        background-color: #94a3b8;
    }
    QToolTip {
        background-color: #1e293b;
        color: #f1f5f9;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 10pt;
    }
    QProgressBar {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        text-align: center;
        background-color: #f1f5f9;
        height: 12px;
    }
    QProgressBar::chunk {
        background-color: #d97706;
        border-radius: 6px;
    }
    """
    app.setStyleSheet(style_sheet)
    
    window = FounderApp()
    window.show()
    sys.exit(app.exec())
