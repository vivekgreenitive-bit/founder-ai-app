import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QLabel, 
                             QFileDialog, QProgressBar, QMessageBox)
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


class FounderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Founder Frameworks AI Consultant")
        self.setMinimumSize(800, 600)
        
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
        header = QLabel("Founder Frameworks AI")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
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
        self.query_input.setPlaceholderText("E.g., Based on these financials, which framework should I use to stop cash burn?")
        layout.addWidget(self.query_input)
        
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
            
    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", 
            "All Files (*);;PDFs (*.pdf);;Excel (*.xlsx *.csv);;Images (*.png *.jpg *.jpeg);;Text (*.txt)"
        )
        if file_path:
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
