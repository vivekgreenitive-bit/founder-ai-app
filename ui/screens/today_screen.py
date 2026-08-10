"""
ui/screens/today_screen.py
Business Command Center — answers: "What needs my attention right now?"

Shows:
- Executive Summary Dashboard: 3 metric cards (Bottleneck Tax, Velocity Score, Open Actions)
- Proactive follow-up card for pending actions
- Most recent diagnosis constraint cards from DiagnosisSessionService
- Clean empty state CTA when no data exists yet
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.company_profile_service import CompanyProfileService
from services.diagnosis_session_service import DiagnosisSessionService
from services.actions_service import ActionsService
from agents.bottleneck_agent import BottleneckAgent
from agents.velocity_agent import VelocityAgent
from db.outcome_tracker import OutcomeTrackerDB


class TodayScreen(QWidget):
    """
    Default Home Screen: Business Command Center.
    Displays real data from services. Zero fabricated metrics.
    Includes proactive in-app follow-up and executive dashboard.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self._profile_svc = CompanyProfileService()
        self._session_svc = DiagnosisSessionService()
        self._actions_svc = ActionsService()
        self._outcome_db = OutcomeTrackerDB()
        self._velocity_agent = VelocityAgent()
        self._bottleneck_agent = BottleneckAgent()
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
        self._content_layout.setSpacing(16)

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

        # ═══════════════════════════════════════════════════════════════════════
        # EXECUTIVE SUMMARY DASHBOARD — 3 Metric Cards
        # ═══════════════════════════════════════════════════════════════════════
        sessions = self._session_svc.get_recent_sessions(limit=3)
        pending_actions = (
            self._actions_svc.get_actions_by_status("PENDING") +
            self._actions_svc.get_actions_by_status("IN_PROGRESS")
        )

        dashboard_row = QHBoxLayout()
        dashboard_row.setSpacing(14)

        # Card 1: Bottleneck Tax
        profile = self._profile_svc.get_profile()
        hourly_rate = float(profile.get("hourly_rate", "150") or "150")
        hours_low_leverage = float(profile.get("low_leverage_hours", "15") or "15")
        monthly_rev = float(profile.get("monthly_revenue", "30000") or "30000")
        tax_result = self._bottleneck_agent.calculate_tax(hourly_rate, hours_low_leverage, monthly_rev)
        monthly_tax = tax_result["monthly_tax"]
        severity = tax_result["severity"]

        sev_colors = {
            "CRITICAL": ("#b91c1c", "#fef2f2", "#fca5a5"),
            "HIGH":     ("#b45309", "#fffbeb", "#fde68a"),
            "MODERATE": ("#1d4ed8", "#eff6ff", "#bfdbfe"),
            "LOW":      ("#166534", "#f0fdf4", "#86efac"),
        }
        sev_text, sev_bg, sev_border = sev_colors.get(severity, ("#166534", "#f0fdf4", "#86efac"))

        tax_card = self._make_dashboard_card(
            "💰 BOTTLENECK TAX",
            f"${monthly_tax:,.0f}/mo",
            f"Severity: {severity}",
            sev_bg, sev_border, sev_text,
            nav_key="bottleneck_tax"
        )
        dashboard_row.addWidget(tax_card, stretch=1)

        # Card 2: Execution Velocity Score
        velocity = self._velocity_agent.compute_velocity()
        v_score = velocity["velocity_score"]
        v_status = velocity["status"]

        if v_score >= 80:
            v_text, v_bg, v_border = "#166534", "#f0fdf4", "#86efac"
        elif v_score >= 60:
            v_text, v_bg, v_border = "#b45309", "#fffbeb", "#fde68a"
        else:
            v_text, v_bg, v_border = "#b91c1c", "#fef2f2", "#fca5a5"

        vel_card = self._make_dashboard_card(
            "⚡ EXECUTION VELOCITY",
            f"{v_score} / 100",
            v_status,
            v_bg, v_border, v_text,
            nav_key="velocity_grader"
        )
        dashboard_row.addWidget(vel_card, stretch=1)

        # Card 3: Open Actions
        open_count = len(pending_actions)
        if open_count == 0:
            a_text, a_bg, a_border = "#166534", "#f0fdf4", "#86efac"
            a_status = "All Clear"
        elif open_count <= 3:
            a_text, a_bg, a_border = "#b45309", "#fffbeb", "#fde68a"
            a_status = "Needs Attention"
        else:
            a_text, a_bg, a_border = "#b91c1c", "#fef2f2", "#fca5a5"
            a_status = "Action Required"

        actions_card = self._make_dashboard_card(
            "🎯 OPEN ACTIONS",
            str(open_count),
            a_status,
            a_bg, a_border, a_text,
            nav_key="actions"
        )
        dashboard_row.addWidget(actions_card, stretch=1)

        self._content_layout.addLayout(dashboard_row)

        # ═══════════════════════════════════════════════════════════════════════
        # PROACTIVE FOLLOW-UP CARD
        # ═══════════════════════════════════════════════════════════════════════
        if pending_actions:
            followup_card = self._make_followup_card(pending_actions)
            self._content_layout.addWidget(followup_card)

        if sessions or pending_actions:
            self._build_populated_state(sessions)
        else:
            self._build_empty_state()

        self._content_layout.addStretch()

    # ── Executive Dashboard Card Builder ──────────────────────────────────────

    def _make_dashboard_card(self, title, value, subtitle, bg, border, text_color, nav_key=None):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{bg}; border:1px solid {border}; "
            f"border-top:3px solid {text_color}; border-radius:12px; }}"
        )
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color:{text_color}; font-size:7.5pt; font-weight:bold; letter-spacing:0.8px;")
        layout.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        v_lbl.setStyleSheet(f"color:{text_color};")
        layout.addWidget(v_lbl)

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"color:{text_color}; font-size:9pt; font-weight:500;")
        layout.addWidget(s_lbl)

        if nav_key and self.main_app and hasattr(self.main_app, "switch_nav"):
            card.mousePressEvent = lambda e, k=nav_key: self.main_app.switch_nav(k)

        return card

    # ── Proactive Follow-up Card ──────────────────────────────────────────────

    def _make_followup_card(self, pending_actions: list) -> QFrame:
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

    # ── Populated State ───────────────────────────────────────────────────────

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

    # ── Empty State ───────────────────────────────────────────────────────────

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

    # ── Constraint Card ───────────────────────────────────────────────────────

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
