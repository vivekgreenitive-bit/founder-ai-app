import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
                             QFrame, QComboBox, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

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
    
    def __init__(self, engine, query, document_text):
        super().__init__()
        self.engine = engine
        self.query = query
        self.document_text = document_text
        
    def run(self):
        try:
            result = self.engine.analyze_query(self.query, self.document_text)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class ProfileDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Profile Setup")
        self.setMinimumWidth(550)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header
        title = QLabel("Company Profile Setup")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #1f2937;")
        main_layout.addWidget(title)
        
        subtitle = QLabel("To provide personalized, actionable advice based on the Founder Frameworks, the AI needs to understand your current business landscape.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b; font-size: 13pt; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)
        
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(15)
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
        
        # Style all inputs
        input_style = """
            QLineEdit, QComboBox {
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                font-size: 13pt;
                color: #334155;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.name_input.setStyleSheet(input_style)
        self.industry_input.setStyleSheet(input_style)
        self.stage_input.setStyleSheet(input_style)
        self.team_input.setStyleSheet(input_style)
        self.challenge_input.setStyleSheet(input_style)
        
        # Label Styling
        label_font = QFont("Arial", 12, QFont.Weight.Bold)
        
        def add_styled_row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setFont(label_font)
            lbl.setStyleSheet("color: #334155;")
            self.form_layout.addRow(lbl, widget)
            
        add_styled_row("Business Name:", self.name_input)
        add_styled_row("Industry Segment:", self.industry_input)
        add_styled_row("Business Stage:", self.stage_input)
        add_styled_row("Team Size:", self.team_input)
        add_styled_row("Primary Challenge:", self.challenge_input)
        
        main_layout.addLayout(self.form_layout)
        
        # Load existing data
        self.profile_path = "company_profile.json"
        self.load_profile()
        
        # Save Button
        self.save_btn = QPushButton("Save Company Profile")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: white;
                font-weight: bold;
                font-size: 14pt;
                padding: 15px;
                border: none;
                border-radius: 8px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #145c2d;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        main_layout.addWidget(self.save_btn)
        
        # Add stretch to push everything to the top and prevent weird huge gaps
        main_layout.addStretch()
        
        self.setStyleSheet("QDialog { background-color: #f8fafc; }")
        
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
        data = {
            "name": self.name_input.text(),
            "industry": self.industry_input.currentText(),
            "stage": self.stage_input.currentText(),
            "team": self.team_input.currentText(),
            "challenge": self.challenge_input.currentText()
        }
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print("Failed to save profile:", e)
        super().accept()


class FounderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Founder Frameworks AI Consultant")
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
        header_bar.setStyleSheet("background: #0f172a; border: none;")
        header_bar.setFixedHeight(56)
        header_bar_layout = QHBoxLayout(header_bar)
        header_bar_layout.setContentsMargins(20, 0, 20, 0)

        header = QLabel("Founder Frameworks AI")
        header.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        header.setStyleSheet("color: white; background: transparent;")
        header_bar_layout.addWidget(header)

        self.status_label = QLabel("Starting up...")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 11pt; background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_bar_layout.addWidget(self.status_label, stretch=1)

        self.settings_btn = QPushButton("⚙️ Profile")
        self.settings_btn.setToolTip("Set Company Context")
        self.settings_btn.setFixedSize(100, 34)
        self.settings_btn.setStyleSheet(
            "QPushButton { background: #1e293b; color: #cbd5e1; border: 1px solid #334155; "
            "border-radius: 8px; font-size: 10pt; }"
            "QPushButton:hover { background: #334155; color: white; }"
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
        self.query_input.setPlaceholderText("Describe your biggest business challenge...")
        input_row.addWidget(self.query_input, stretch=1)

        self.analyze_btn = QPushButton("➤")
        self.analyze_btn.setObjectName("SendBtn")
        self.analyze_btn.setToolTip("Get My Business Diagnosis")
        self.analyze_btn.setFixedSize(42, 42)
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setEnabled(False)
        input_row.addWidget(self.analyze_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        bottom_layout.addLayout(input_row)

        # Toolbar: file label + upload
        toolbar_row = QHBoxLayout()
        toolbar_row.setSpacing(8)

        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #64748b; font-style: italic; font-size: 9pt;")
        toolbar_row.addWidget(self.file_label, stretch=1)

        self.upload_btn = QPushButton("📎 Upload a Document")
        self.upload_btn.setObjectName("SecondaryBtn")
        self.upload_btn.setFixedHeight(30)
        self.upload_btn.setMinimumWidth(160)
        self.upload_btn.clicked.connect(self.upload_file)
        toolbar_row.addWidget(self.upload_btn)

        bottom_layout.addLayout(toolbar_row)
        right_layout.addWidget(bottom_card)

        body_layout.addWidget(right_panel, stretch=1)
        root.addWidget(body, stretch=1)

    def init_ai(self):
        # We will initialize it synchronously for now, but in a real app 
        # this should be in a thread to not block the UI
        try:
            self.engine = FounderAIEngine()
            self.status_label.setText("✅  Ready. Describe your challenge and get your diagnosis.")
            self.status_label.setStyleSheet("color: #1a7a3c; font-size: 13px;")
            self.analyze_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"AI Engine Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
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
            self.status_label.setStyleSheet("color: #1a7a3c; font-size: 12px;")

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
        self.output_area.setPlainText("🔄  Analyzing your challenge...\n\nPlease wait a moment.")
        self.copy_btn.setVisible(False)
        self.status_label.setText("Analyzing your business challenge...")

        self.worker = AnalysisWorker(self.engine, combined, self.current_document_text)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.start()
        
    def markdown_to_html(self, text: str) -> str:
        """Convert the AI's markdown output to clean HTML for display."""
        import re
        lines = text.split('\n')
        html_lines = []
        in_steps = False

        for line in lines:
            stripped = line.strip()

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
        self._plain_result = result          # store for clipboard copy
        self.output_area.setHtml(self.markdown_to_html(result))
        self.copy_btn.setVisible(True)
        self.status_label.setText("✅  Analysis complete. Copy or start a new diagnosis.")
        self.status_label.setStyleSheet("color: #1a7a3c; font-size: 12px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
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
