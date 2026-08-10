"""
ui/screens/consulting_screen.py
1:1 Founder Consulting & Advisory Chat UI Screen.
Secured with unique Session ID (cs_...) and cryptographic Founder Token (usr_...).
Powered by Google Cloud Vertex AI / Gemini 1.5 Pro backend.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QLineEdit, QScrollArea, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from services.consulting_service import ConsultingService


class ChatWorker(QThread):
    """Background worker to call Google Cloud consulting service without freezing UI."""
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, service: ConsultingService, message_text: str):
        super().__init__()
        self.service = service
        self.message_text = message_text

    def run(self):
        try:
            res = self.service.send_message(self.message_text)
            self.finished.emit(res)
        except Exception as e:
            self.failed.emit(str(e))


class ConsultingScreen(QWidget):
    """
    1:1 Founder Advisory Chat Interface.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.service = ConsultingService()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # ── Header Bar ────────────────────────────────────────────────────────
        hdr_card = QFrame()
        hdr_card.setStyleSheet("background: #ffffff; border: 1px solid #ccebd7; border-radius: 12px; padding: 14px 18px;")
        hc_layout = QHBoxLayout(hdr_card)
        hc_layout.setContentsMargins(0, 0, 0, 0)

        left_hdr = QVBoxLayout()
        title_row = QHBoxLayout()
        title_lbl = QLabel("💬 1:1 Founder Advisory Chat")
        title_lbl.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #0f2318;")

        gcp_badge = QLabel("☁️ Google Cloud Enterprise Secured")
        gcp_badge.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-size: 8pt; font-weight: bold; padding: 3px 8px; border-radius: 10px; border: 1px solid #bfdbfe;")

        title_row.addWidget(title_lbl)
        title_row.addWidget(gcp_badge)
        title_row.addStretch()
        left_hdr.addLayout(title_row)

        self.session_lbl = QLabel("Session Loading...")
        self.session_lbl.setStyleSheet("color: #64748b; font-size: 8.5pt;")
        left_hdr.addWidget(self.session_lbl)

        hc_layout.addLayout(left_hdr, stretch=1)

        new_session_btn = QPushButton("➕ New Chat Session")
        new_session_btn.setFixedHeight(34)
        new_session_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #1a7a3c;
                border: 1px solid #ccebd7;
                border-radius: 8px;
                font-weight: bold;
                font-size: 9pt;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: #f0fbf4;
            }
        """)
        new_session_btn.clicked.connect(self._start_new_session)
        hc_layout.addWidget(new_session_btn)

        root.addWidget(hdr_card)

        # ── Quick Advice Prompts Bar ───────────────────────────────────────────
        prompts_layout = QHBoxLayout()
        prompts_layout.setSpacing(8)

        quick_prompts = [
            ("⚡ Fix Bottleneck Tax", "How do I delegate tasks to reduce my monthly founder tax?"),
            ("🚀 Accelerate Velocity", "What step can I take today to improve our execution velocity?"),
            ("🎯 Align Quarterly Goal", "How should we structure our sprints to reach our quarterly goal?"),
        ]

        for label, text in quick_prompts:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8fafc;
                    color: #2d4536;
                    border: 1px solid #e2e8f0;
                    border-radius: 14px;
                    font-size: 8.5pt;
                    font-weight: 600;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background: #e2f5ea;
                    color: #1a7a3c;
                    border-color: #ccebd7;
                }
            """)
            btn.clicked.connect(lambda checked, t=text: self._send_quick_prompt(t))
            prompts_layout.addWidget(btn)

        prompts_layout.addStretch()
        root.addLayout(prompts_layout)

        # ── Chat Messages Canvas (Scroll Area) ────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.chat_canvas = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_canvas)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_canvas)
        root.addWidget(self.scroll, stretch=1)

        # ── Message Input Bar ──────────────────────────────────────────────────
        input_card = QFrame()
        input_card.setStyleSheet("background: #ffffff; border: 1px solid #ccebd7; border-radius: 12px; padding: 8px 12px;")
        ic_layout = QHBoxLayout(input_card)
        ic_layout.setContentsMargins(4, 4, 4, 4)
        ic_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask your Google Cloud Advisory Partner a question...")
        self.input_field.setFixedHeight(38)
        self.input_field.setStyleSheet("border: none; font-size: 10.5pt; color: #0f2318;")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send Message ➔")
        self.send_btn.setFixedSize(130, 38)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 9.5pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)

        ic_layout.addWidget(self.input_field, stretch=1)
        ic_layout.addWidget(self.send_btn)

        root.addWidget(input_card)

        self.refresh_data()

    # ── Chat Logic ────────────────────────────────────────────────────────────

    def refresh_data(self):
        """Loads and renders active chat session messages."""
        session_info = self.service.get_or_create_session()
        token = session_info["founder_token"]
        session_id = session_info["session_id"]
        messages = session_info["messages"]

        self.session_lbl.setText(f"Founder Token: <b>{token}</b>  •  Session: <b>{session_id}</b>")

        # Clear existing message widgets
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not messages:
            self._render_welcome_message()
        else:
            for msg in messages:
                self._render_bubble(msg["sender"], msg["text"], msg.get("timestamp", ""))

        self._scroll_to_bottom()

    def _render_welcome_message(self):
        welcome_box = QFrame()
        welcome_box.setStyleSheet("background: #f0fbf4; border: 1px solid #ccebd7; border-radius: 12px; padding: 18px;")
        wb_layout = QVBoxLayout(welcome_box)
        wb_layout.setSpacing(6)

        w_title = QLabel("👋 Welcome to 1:1 Founder Advisory")
        w_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        w_title.setStyleSheet("color: #1a7a3c;")

        w_desc = QLabel(
            "Your Google Cloud-backed AI Strategic Advisor is ready. "
            "Ask any question about growth strategy, operational delegation, fundraising, or bottleneck resolution. "
            "All sessions are encrypted and bound to your founder token."
        )
        w_desc.setStyleSheet("color: #2d4536; font-size: 10pt; line-height: 1.4;")
        w_desc.setWordWrap(True)

        wb_layout.addWidget(w_title)
        wb_layout.addWidget(w_desc)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, welcome_box)

    def _render_bubble(self, sender: str, text: str, timestamp: str):
        row = QHBoxLayout()

        bubble = QFrame()
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(14, 10, 14, 10)

        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 10pt; line-height: 1.4;")

        ts_lbl = QLabel(timestamp)
        ts_lbl.setStyleSheet("font-size: 7.5pt; margin-top: 4px;")

        if sender == "founder":
            row.addStretch()
            bubble.setStyleSheet("background-color: #1a7a3c; border-radius: 12px; border-bottom-right-radius: 2px;")
            lbl.setStyleSheet("color: #ffffff; font-size: 10pt;")
            ts_lbl.setStyleSheet("color: #a3d9b5; font-size: 7.5pt;")
            row.addWidget(bubble, stretch=0)
        else:
            bubble.setStyleSheet("background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 12px; border-bottom-left-radius: 2px;")
            lbl.setStyleSheet("color: #0f2318; font-size: 10pt;")
            ts_lbl.setStyleSheet("color: #64748b; font-size: 7.5pt;")
            row.addWidget(bubble, stretch=0)
            row.addStretch()

        b_layout.addWidget(lbl)
        b_layout.addWidget(ts_lbl)

        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self._render_bubble("founder", text, "Just now")
        self._scroll_to_bottom()

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Advisor Thinking...")

        # Run background thread
        self.worker = ChatWorker(self.service, text)
        self.worker.finished.connect(self._on_response)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _send_quick_prompt(self, text: str):
        self.input_field.setText(text)
        self.send_message()

    def _on_response(self, msg: dict):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send Message ➔")
        self._render_bubble("advisor", msg["text"], msg.get("timestamp", "Just now"))
        self._scroll_to_bottom()

    def _on_fail(self, error_msg: str):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("Send Message ➔")
        self._render_bubble("advisor", f"Unable to reach GCP backend: {error_msg}", "Now")
        self._scroll_to_bottom()

    def _start_new_session(self):
        self.service.new_session()
        self.refresh_data()

    def _scroll_to_bottom(self):
        QApplication.processEvents()
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
