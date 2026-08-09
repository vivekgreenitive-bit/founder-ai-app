"""
ui/screens/today_screen.py
Business Command Center — answers: "What needs my attention right now?"

Shows:
- Personalized greeting from CompanyProfileService (real data)
- Proactive follow-up card for pending actions ("You had N actions — how did they go?")
- Most recent diagnosis constraint card from DiagnosisSessionService (real data)
- Clean empty state CTA when no data exists yet (no fabricated metrics)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.company_profile_service import CompanyProfileService
from services.diagnosis_session_service import DiagnosisSessionService
from services.actions_service import ActionsService
from db.outcome_tracker import OutcomeTrackerDB


class TodayScreen(QWidget):
    """
    Default Home Screen: Business Command Center.
    Displays real data from services. Zero fabricated metrics.
    Includes proactive in-app follow-up for open action items.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self._profile_svc = CompanyProfileService()
        self._session_svc = DiagnosisSessionService()
        self._actions_svc = ActionsService()
        self._outcome_db = OutcomeTrackerDB()
        self._content_layout = None
        self.init_ui()

    def init_ui(self):
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(28, 24, 28, 24)
        self._root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._canvas = QWidget()
        self._content_layout = QVBoxLayout(self._canvas)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(20)

        scroll.setWidget(self._canvas)
        self._root_layout.addWidget(scroll)

        self._build_content()

    def _build_content(self):
        """Clears and rebuilds all content from real data sources."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        name = self._profile_svc.get_company_name()
        if name == "Your Company":
            name = self._profile_svc.get_founder_name()

        # Header
        header = QLabel(f"Good morning, {name}")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        self._content_layout.addWidget(header)

        sub = QLabel("Here's what needs your attention today.")
        sub.setStyleSheet("color: #4b6b5a; font-size: 11pt; margin-bottom: 4px;")
        self._content_layout.addWidget(sub)

        sessions = self._session_svc.get_recent_sessions(limit=3)
        pending_actions = self._actions_svc.get_actions_by_status("PENDING") + self._actions_svc.get_actions_by_status("IN_PROGRESS")

        # 1. Proactive Follow-up Prompt Card if there are open actions
        if pending_actions:
            followup_card = self._make_followup_card(pending_actions)
            self._content_layout.addWidget(followup_card)

        if sessions or pending_actions:
            self._build_populated_state(sessions)
        else:
            self._build_empty_state()

        self._content_layout.addStretch()

    def _make_followup_card(self, pending_actions: list) -> QFrame:
        """Proactive AI Follow-up card prompting the user on open action items."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #fffbeb;
                border: 1px solid #fde68a;
                border-left: 6px solid #b45309;
                border-radius: 12px;
                padding: 16px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        icon = QLabel("🤖")
        icon.setStyleSheet("font-size: 16pt;")
        title = QLabel("AI Follow-up: Open Action Items")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #92400e;")

        count_badge = QLabel(f"{len(pending_actions)} Open")
        count_badge.setStyleSheet("background:#fef3c7; color:#b45309; font-weight:bold; font-size:8.5pt; padding:2px 8px; border-radius:8px;")

        top_row.addWidget(icon)
        top_row.addWidget(title)
        top_row.addWidget(count_badge)
        top_row.addStretch()
        layout.addLayout(top_row)

        latest_action = pending_actions[0]
        desc = QLabel(f"From your last diagnosis: \"{latest_action.get('action_text', '')[:100]}\"")
        desc.setStyleSheet("color: #78350f; font-size: 10pt; font-weight: 500;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        update_btn = QPushButton("Update Status & Record Outcome")
        update_btn.setFixedHeight(32)
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #b45309;
                color: #ffffff;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9.5pt;
                padding: 0 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #92400e;
            }
        """)
        if self.main_app and hasattr(self.main_app, "switch_nav"):
            update_btn.clicked.connect(lambda: self.main_app.switch_nav("actions"))

        btn_row.addWidget(update_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _build_populated_state(self, sessions):
        if sessions:
            attn_lbl = QLabel("RECENT DIAGNOSES")
            attn_lbl.setStyleSheet("color: #1a7a3c; font-size: 8.5pt; font-weight: bold; letter-spacing: 1.2px; margin-top: 8px;")
            self._content_layout.addWidget(attn_lbl)

            for session in sessions[:2]:
                card = self._make_constraint_card(session)
                self._content_layout.addWidget(card)

        action_row = QHBoxLayout()
        new_btn = QPushButton("Run New Diagnosis")
        new_btn.setFixedHeight(40)
        new_btn.setStyleSheet(
            "QPushButton { background:#1a7a3c; color:#fff; border-radius:8px; "
            "font-weight:bold; font-size:10.5pt; padding:0 18px; border:none; }"
            "QPushButton:hover { background:#145e2e; }"
        )
        if self.main_app and hasattr(self.main_app, "switch_to_diagnose"):
            new_btn.clicked.connect(self.main_app.switch_to_diagnose)

        view_actions_btn = QPushButton("View All Actions")
        view_actions_btn.setFixedHeight(40)
        view_actions_btn.setStyleSheet(
            "QPushButton { background:#ffffff; color:#1a7a3c; border:1px solid #ccebd7; "
            "border-radius:8px; font-weight:600; font-size:10.5pt; padding:0 18px; }"
            "QPushButton:hover { background:#f0fbf4; }"
        )
        if self.main_app and hasattr(self.main_app, "switch_nav"):
            view_actions_btn.clicked.connect(lambda: self.main_app.switch_nav("actions"))

        action_row.addWidget(new_btn)
        action_row.addWidget(view_actions_btn)
        action_row.addStretch()
        self._content_layout.addLayout(action_row)

    def _build_empty_state(self):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ccebd7;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Understand what's holding your business back")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a7a3c;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc = QLabel(
            "Describe a business challenge. Founder AI will identify your primary\n"
            "constraint using evidence-backed analysis — no guesswork."
        )
        desc.setStyleSheet("color: #4b6b5a; font-size: 10.5pt; line-height: 1.5;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        cta_btn = QPushButton("Start My First Diagnosis")
        cta_btn.setFixedSize(230, 44)
        cta_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
                border: none;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        if self.main_app and hasattr(self.main_app, "switch_to_diagnose"):
            cta_btn.clicked.connect(self.main_app.switch_to_diagnose)

        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addWidget(cta_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._content_layout.addWidget(card, stretch=1)

    def _make_constraint_card(self, session: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ccebd7;
                border-left: 4px solid #1a7a3c;
                border-radius: 10px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 14, 18, 14)
        card_layout.setSpacing(6)

        hdr = QHBoxLayout()
        fw_badge = QLabel(session.get("framework", "Framework"))
        fw_badge.setStyleSheet("background:#e2f5ea; color:#1a7a3c; font-weight:bold; font-size:8pt; padding:2px 8px; border-radius:8px; border:1px solid #ccebd7;")
        ts_lbl = QLabel(session.get("timestamp", "")[:10])
        ts_lbl.setStyleSheet("color:#94a3b8; font-size:8.5pt;")
        hdr.addWidget(fw_badge)
        hdr.addStretch()
        hdr.addWidget(ts_lbl)
        card_layout.addLayout(hdr)

        constraint_lbl = QLabel(session.get("constraint", "Analysis complete — view full diagnosis."))
        constraint_lbl.setStyleSheet("color:#0f2318; font-size:10.5pt; font-weight:600;")
        constraint_lbl.setWordWrap(True)
        card_layout.addWidget(constraint_lbl)

        conf = session.get("confidence", 0.0)
        ev_count = session.get("evidence_count", 0)
        if conf > 0:
            conf_pct = int(conf * 100)
            meta_lbl = QLabel(f"Confidence: {conf_pct}%  •  Evidence signals: {ev_count}")
            meta_lbl.setStyleSheet("color:#64748b; font-size:9pt;")
            card_layout.addWidget(meta_lbl)

        cta_row = QHBoxLayout()
        view_btn = QPushButton("View Diagnosis")
        view_btn.setFixedHeight(30)
        view_btn.setStyleSheet(
            "QPushButton { background:#1a7a3c; color:#fff; border-radius:6px; "
            "font-weight:bold; font-size:9pt; padding:0 12px; border:none; }"
            "QPushButton:hover { background:#145e2e; }"
        )
        if self.main_app and hasattr(self.main_app, "switch_to_diagnose"):
            view_btn.clicked.connect(self.main_app.switch_to_diagnose)
        cta_row.addWidget(view_btn)
        cta_row.addStretch()
        card_layout.addLayout(cta_row)

        return card

    def refresh_data(self):
        self._build_content()
