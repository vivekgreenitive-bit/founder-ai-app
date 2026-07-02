import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox)
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
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Founder Frameworks AI")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header, stretch=1)
        
        self.settings_btn = QPushButton("⚙️ Profile")
        self.settings_btn.setToolTip("Set Company Context")
        self.settings_btn.setFixedSize(100, 40)
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn)
        
        layout.addLayout(header_layout)
        
        # Status Label
        self.status_label = QLabel("Initializing AI Engine...")
        self.status_label.setStyleSheet("color: gray;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # File Upload Area
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected.")
        self.upload_btn = QPushButton("Upload Document (PDF, Excel, Image)")
        self.upload_btn.clicked.connect(self.upload_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.upload_btn)
        layout.addLayout(file_layout)
        
        # Query Area
        layout.addWidget(QLabel("Ask the AI Consultant:"))
        self.query_input = QTextEdit()
        self.query_input.setMaximumHeight(80)
        self.query_input.setPlaceholderText("E.g., Based on these financials, which framework should I use to stop cash burn? (You can drag & drop files here!)")
        layout.addWidget(self.query_input)
        
        # 1-Click Diagnostic Buttons
        quick_btns_layout = QHBoxLayout()
        
        btn1 = QPushButton("Delegation")
        btn1.clicked.connect(lambda: self.set_quick_prompt("Act as my COO. Run the OKS REC SME framework on my daily schedule and tell me how to delegate tasks to remove myself as the bottleneck."))
        quick_btns_layout.addWidget(btn1)
        
        btn2 = QPushButton("SOP Creation")
        btn2.clicked.connect(lambda: self.set_quick_prompt("Run the RSS FEED SME framework. Help me create an SOP structure so my team stops making errors on routine tasks."))
        quick_btns_layout.addWidget(btn2)
        
        btn3 = QPushButton("Diagnostic")
        btn3.clicked.connect(lambda: self.set_quick_prompt("Run the ECG KISS diagnostic framework on my business to help me identify gaps and simulate strategic solutions for growth."))
        quick_btns_layout.addWidget(btn3)
        
        btn4 = QPushButton("Quarterly Planning")
        btn4.clicked.connect(lambda: self.set_quick_prompt("Use the MC BEERS framework to help me break down our yearly goals into a rigid 90-day execution plan."))
        quick_btns_layout.addWidget(btn4)
        
        layout.addLayout(quick_btns_layout)
        
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
        layout.addWidget(QLabel("AI Analysis:"))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Arial", 12))
        layout.addWidget(self.output_area)
        
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
        background-color: #fdfdfc;
    }
    QLabel {
        color: #1f2937;
    }
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 10px;
        color: #374151;
        font-family: Arial;
        font-size: 13pt;
    }
    QPushButton {
        background-color: #f3f4f6;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        color: #1f2937;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e5e7eb;
    }
    /* Special styling for the main action button */
    QPushButton#AnalyzeBtn {
        background-color: #1a7a3c;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-size: 14pt;
    }
    QPushButton#AnalyzeBtn:hover {
        background-color: #145c2d;
    }
    QPushButton#AnalyzeBtn:disabled {
        background-color: #9ca3af;
    }
    QProgressBar {
        border: 1px solid #e5e7eb;
        border-radius: 4px;
        text-align: center;
        background-color: #f3f4f6;
    }
    QProgressBar::chunk {
        background-color: #d97706;
    }
    """
    app.setStyleSheet(style_sheet)
    
    window = FounderApp()
    window.show()
    sys.exit(app.exec())
