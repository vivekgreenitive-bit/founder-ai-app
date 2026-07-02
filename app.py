import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFrame)
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
        self.setWindowTitle("Company Profile")
        self.setMinimumWidth(400)
        
        self.layout = QFormLayout(self)
        
        self.industry_input = QLineEdit()
        self.revenue_input = QLineEdit()
        self.goal_input = QLineEdit()
        
        self.layout.addRow("Industry:", self.industry_input)
        self.layout.addRow("Current Revenue:", self.revenue_input)
        self.layout.addRow("1-Year Goal:", self.goal_input)
        
        # Load existing data
        self.profile_path = "company_profile.json"
        self.load_profile()
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    data = json.load(f)
                    self.industry_input.setText(data.get("industry", ""))
                    self.revenue_input.setText(data.get("revenue", ""))
                    self.goal_input.setText(data.get("goal", ""))
            except:
                pass
                
    def accept(self):
        data = {
            "industry": self.industry_input.text(),
            "revenue": self.revenue_input.text(),
            "goal": self.goal_input.text()
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
        
        # Card 1: Data Source
        card1 = QFrame()
        card1.setObjectName("CardFrame")
        card1_layout = QVBoxLayout(card1)
        card1_layout.setContentsMargins(20, 20, 20, 20)
        
        upload_title = QLabel("1. Provide Context (Optional)")
        upload_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        card1_layout.addWidget(upload_title)
        
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected. You can drag and drop a PDF, CSV, or TXT file anywhere on this window.")
        self.file_label.setStyleSheet("color: #64748b; font-style: italic;")
        self.upload_btn = QPushButton("Browse Files")
        self.upload_btn.setObjectName("SecondaryBtn")
        self.upload_btn.clicked.connect(self.upload_file)
        file_layout.addWidget(self.file_label, stretch=1)
        file_layout.addWidget(self.upload_btn)
        card1_layout.addLayout(file_layout)
        layout.addWidget(card1)
        
        # Card 2: Query Area
        card2 = QFrame()
        card2.setObjectName("CardFrame")
        card2_layout = QVBoxLayout(card2)
        card2_layout.setContentsMargins(20, 20, 20, 20)
        card2_layout.setSpacing(15)
        
        query_title = QLabel("2. Ask the AI Consultant")
        query_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        card2_layout.addWidget(query_title)
        
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(100)
        self.query_input.setPlaceholderText("E.g., Based on these financials, which framework should I use to stop cash burn?")
        card2_layout.addWidget(self.query_input)
        
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
        
        card2_layout.addLayout(quick_btns_layout)
        layout.addWidget(card2)
        
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
