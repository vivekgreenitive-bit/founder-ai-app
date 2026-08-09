"""
ui/screens/business_data_screen.py
Business Data Center — shows all uploaded files that Founder AI uses for evidence.
Provides: view, manage, and clear uploaded business data per session.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from document_processor import extract_text_from_file
import os


class BusinessDataScreen(QWidget):
    """
    Business Data Center.
    Shows what data Founder AI has access to, with controls to add or remove files.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self._files: list = []  # list of {"name": str, "path": str, "size": str}
        self._canvas_layout = None
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QLabel("Business Data")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        root.addWidget(header)

        sub = QLabel(
            "Files you attach are used by Founder AI to improve evidence quality "
            "and confidence during analysis. Data stays on your device."
        )
        sub.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Action row
        action_row = QHBoxLayout()
        add_btn = QPushButton("+ Add Business Data")
        add_btn.setFixedHeight(38)
        add_btn.setStyleSheet(
            "QPushButton { background:#1a7a3c; color:#fff; border-radius:8px; "
            "font-weight:bold; font-size:10pt; padding:0 18px; border:none; }"
            "QPushButton:hover { background:#145e2e; }"
        )
        add_btn.clicked.connect(self._add_file)

        supported_lbl = QLabel("Supported: CSV, PDF, TXT, XLSX")
        supported_lbl.setStyleSheet("color:#94a3b8; font-size:9pt;")

        action_row.addWidget(add_btn)
        action_row.addWidget(supported_lbl)
        action_row.addStretch()
        root.addLayout(action_row)

        # Privacy notice
        privacy = QFrame()
        privacy.setStyleSheet(
            "QFrame { background:#e2f5ea; border:1px solid #ccebd7; border-radius:8px; }"
        )
        p_layout = QHBoxLayout(privacy)
        p_layout.setContentsMargins(14, 10, 14, 10)
        p_icon = QLabel("🔒")
        p_text = QLabel(
            "Privacy: All uploaded data is processed locally on your device. "
            "Nothing is sent to external servers unless you're using Gemini cloud mode."
        )
        p_text.setStyleSheet("color:#1a7a3c; font-size:9.5pt;")
        p_text.setWordWrap(True)
        p_layout.addWidget(p_icon)
        p_layout.addWidget(p_text, stretch=1)
        root.addWidget(privacy)

        # Scrollable file list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._canvas = QWidget()
        self._canvas_layout = QVBoxLayout(self._canvas)
        self._canvas_layout.setContentsMargins(0, 0, 0, 0)
        self._canvas_layout.setSpacing(10)
        self._canvas_layout.addStretch()

        scroll.setWidget(self._canvas)
        root.addWidget(scroll, stretch=1)

        self._refresh_list()

    def _add_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Business Document", "",
            "Business Documents (*.csv *.pdf *.txt *.xlsx);;All Files (*)"
        )
        if not path:
            return
        name = os.path.basename(path)
        size_kb = os.path.getsize(path) // 1024
        size_str = f"{size_kb} KB" if size_kb < 1024 else f"{size_kb // 1024} MB"

        # Avoid duplicates
        if any(f["path"] == path for f in self._files):
            QMessageBox.information(self, "Already Added", f"{name} is already in your business data.")
            return

        # Try to extract text to confirm it's readable
        text = extract_text_from_file(path)
        if text.startswith("Error"):
            QMessageBox.warning(self, "Could Not Read File", f"Could not extract content from {name}.\n\n{text}")
            return

        self._files.append({"name": name, "path": path, "size": size_str, "text": text})

        # Sync to main app's current_document_text if available
        if self.main_app and hasattr(self.main_app, "current_document_text"):
            self.main_app.current_document_text = text
            if hasattr(self.main_app, "file_label"):
                self.main_app.file_label.setText(name)

        self._refresh_list()

    def _remove_file(self, path: str):
        self._files = [f for f in self._files if f["path"] != path]
        # Clear from main app if this was the active file
        if self.main_app and hasattr(self.main_app, "current_document_text"):
            remaining = next(iter(self._files), None)
            self.main_app.current_document_text = remaining["text"] if remaining else ""
            if hasattr(self.main_app, "file_label"):
                self.main_app.file_label.setText(remaining["name"] if remaining else "")
        self._refresh_list()

    def _refresh_list(self):
        # Clear existing cards
        while self._canvas_layout.count() > 1:
            item = self._canvas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._files:
            empty = QLabel("No business data attached yet.\nAdd CSV, PDF, or TXT files to improve diagnosis quality.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color:#94a3b8; font-size:10pt; font-style:italic; padding:40px;")
            empty.setWordWrap(True)
            self._canvas_layout.insertWidget(0, empty)
            return

        for f in self._files:
            card = self._make_file_card(f)
            self._canvas_layout.insertWidget(self._canvas_layout.count() - 1, card)

    def _make_file_card(self, f: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background:#ffffff; border:1px solid #e2e8f0; "
            "border-left:4px solid #1a7a3c; border-radius:10px; }"
        )
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 16, 12)

        icon = QLabel("📄")
        icon.setStyleSheet("font-size:18pt; border:none;")

        info = QVBoxLayout()
        name_lbl = QLabel(f["name"])
        name_lbl.setStyleSheet("font-weight:bold; color:#0f2318; font-size:10.5pt; border:none;")
        size_lbl = QLabel(f"{f['size']}  •  Ready for analysis")
        size_lbl.setStyleSheet("color:#64748b; font-size:9pt; border:none;")
        info.addWidget(name_lbl)
        info.addWidget(size_lbl)

        remove_btn = QPushButton("Remove")
        remove_btn.setFixedHeight(30)
        remove_btn.setStyleSheet(
            "QPushButton { background:#fff0f0; color:#dc2626; border:1px solid #fca5a5; "
            "border-radius:6px; font-weight:bold; font-size:9pt; padding:0 10px; }"
            "QPushButton:hover { background:#fee2e2; }"
        )
        remove_btn.clicked.connect(lambda _, p=f["path"]: self._remove_file(p))

        row.addWidget(icon)
        row.addLayout(info, stretch=1)
        row.addWidget(remove_btn)
        return card

    def get_combined_text(self) -> str:
        """Returns all attached file content concatenated."""
        return "\n\n".join(f.get("text", "") for f in self._files)
