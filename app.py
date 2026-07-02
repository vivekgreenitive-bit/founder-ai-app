import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from document_processor import extract_text_from_file
from ai_engine import FounderAIEngine

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
        self.setMinimumSize(900, 700)
        self.setAcceptDrops(True)
        
        # Data
        self.engine = None
        self.current_document_text = ""
        self.current_file_path = ""
        
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
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        main_widget.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Founder Frameworks AI")
        header.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header, stretch=1)
        
        self.settings_btn = QPushButton("⚙️ Profile")
        self.settings_btn.setToolTip("Set Company Context")
        self.settings_btn.setFixedSize(120, 45)
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
        
        # Status Label
        self.status_label = QLabel("Initializing AI Engine...")
        self.status_label.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Card: Consultation Area
        card = QFrame()
        card.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Header with Title and Upload Button
        query_header_layout = QHBoxLayout()
        query_title = QLabel("Ask the AI Consultant")
        query_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        query_header_layout.addWidget(query_title, stretch=1)
        
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #64748b; font-style: italic; font-size: 12pt;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        query_header_layout.addWidget(self.file_label)
        
        self.upload_btn = QPushButton("📎 Upload Context")
        self.upload_btn.setObjectName("SecondaryBtn")
        self.upload_btn.setFixedSize(160, 40)
        self.upload_btn.clicked.connect(self.upload_file)
        query_header_layout.addWidget(self.upload_btn)
        
        card_layout.addLayout(query_header_layout)
        
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(100)
        self.query_input.setPlaceholderText("E.g., I am losing business and I work 16 hours a day.")
        card_layout.addWidget(self.query_input)
        
        # 1-Click Diagnostic Buttons
        quick_btns_layout = QHBoxLayout()
        quick_btns_layout.setSpacing(10)
        
        btn1 = QPushButton("Delegation")
        btn1.setObjectName("ChipBtn")
        btn1.clicked.connect(lambda: self.set_quick_prompt("Act as my COO. Run the OKS REC SME framework on my daily schedule and tell me how to delegate tasks to remove myself as the bottleneck."))
        quick_btns_layout.addWidget(btn1)
        
        btn2 = QPushButton("SOP Creation")
        btn2.setObjectName("ChipBtn")
        btn2.clicked.connect(lambda: self.set_quick_prompt("Run the RSS FEED SME framework. Help me create an SOP structure so my team stops making errors on routine tasks."))
        quick_btns_layout.addWidget(btn2)
        
        btn3 = QPushButton("Diagnostic")
        btn3.setObjectName("ChipBtn")
        btn3.clicked.connect(lambda: self.set_quick_prompt("Run the ECG KISS diagnostic framework on my business to help me identify gaps and simulate strategic solutions for growth."))
        quick_btns_layout.addWidget(btn3)
        
        btn4 = QPushButton("Quarterly Planning")
        btn4.setObjectName("ChipBtn")
        btn4.clicked.connect(lambda: self.set_quick_prompt("Use the MC BEERS framework to help me break down our yearly goals into a rigid 90-day execution plan."))
        quick_btns_layout.addWidget(btn4)
        
        card_layout.addLayout(quick_btns_layout)
        layout.addWidget(card)
        
        # Analyze Button
        self.analyze_btn = QPushButton("Analyze with Founder Frameworks")
        self.analyze_btn.setObjectName("AnalyzeBtn")
        self.analyze_btn.clicked.connect(self.run_analysis)
        self.analyze_btn.setEnabled(False)
        layout.addWidget(self.analyze_btn)
        
        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Output Area
        output_title = QLabel("AI Analysis:")
        output_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(output_title)
        
        self.output_area = QTextEdit()
        self.output_area.setObjectName("OutputArea")
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Arial", 13))
        layout.addWidget(self.output_area, stretch=1)
        
    def init_ai(self):
        # We will initialize it synchronously for now, but in a real app 
        # this should be in a thread to not block the UI
        try:
            self.engine = FounderAIEngine()
            self.status_label.setText("AI Engine Ready (Using FounderFrameworks.txt)")
            self.status_label.setStyleSheet("color: green;")
            self.analyze_btn.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"AI Engine Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            
    def open_settings(self):
        dialog = ProfileDialog(self)
        dialog.exec()
        
    def set_quick_prompt(self, text):
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
        if not query and not self.current_document_text:
            QMessageBox.warning(self, "Input Required", "Please upload a document or type a question.")
            return
            
        self.analyze_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.output_area.clear()
        self.status_label.setText("Analyzing...")
        
        # Run in thread
        self.worker = AnalysisWorker(self.engine, query, self.current_document_text)
        self.worker.finished.connect(self.on_analysis_complete)
        self.worker.start()
        
    def on_analysis_complete(self, result):
        self.progress.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.output_area.setPlainText(result)
        self.status_label.setText("Analysis Complete.")

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
