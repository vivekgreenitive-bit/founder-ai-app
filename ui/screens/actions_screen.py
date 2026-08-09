"""
ui/screens/actions_screen.py
Real Actions Workspace — shows action items extracted from diagnosis output.

Lifecycle:  PENDING → [Mark In Progress] → [Done / Partial / Failed]
            Results feed back into AssessmentAgent on the next diagnosis.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.actions_service import ActionsService


# ─── Outcome Note Dialog ──────────────────────────────────────────────────────

class OutcomeNoteDialog(QDialog):
    """Mini-dialog to capture what happened when marking an action outcome."""

    def __init__(self, action_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Outcome")
        self.setFixedSize(480, 280)
        self.setStyleSheet("QDialog { background:#ffffff; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        action_lbl = QLabel(f"Action: {action_text[:80]}{'...' if len(action_text) > 80 else ''}")
        action_lbl.setStyleSheet("color:#0f2318; font-weight:bold; font-size:10pt;")
        action_lbl.setWordWrap(True)
        layout.addWidget(action_lbl)

        layout.addWidget(QLabel("What happened? (optional — this trains future recommendations):"))

        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText(
            "e.g. 'Reduced sign-up form to 3 fields — conversion up 12% in 5 days'"
        )
        self.note_input.setMaximumHeight(100)
        self.note_input.setStyleSheet(
            "QTextEdit { border:1px solid #e2e8f0; border-radius:8px; "
            "padding:10px; font-size:10pt; }"
        )
        layout.addWidget(self.note_input)

        btn_box = QDialogButtonBox()
        self.done_btn = QPushButton("Mark Done")
        self.partial_btn = QPushButton("Mark Partial")
        self.failed_btn = QPushButton("Mark Failed")

        self.done_btn.setStyleSheet(
            "QPushButton { background:#1a7a3c; color:#fff; border-radius:6px; "
            "font-weight:bold; padding:8px 16px; border:none; }"
            "QPushButton:hover { background:#145e2e; }"
        )
        self.partial_btn.setStyleSheet(
            "QPushButton { background:#b45309; color:#fff; border-radius:6px; "
            "font-weight:bold; padding:8px 16px; border:none; }"
            "QPushButton:hover { background:#92400e; }"
        )
        self.failed_btn.setStyleSheet(
            "QPushButton { background:#dc2626; color:#fff; border-radius:6px; "
            "font-weight:bold; padding:8px 16px; border:none; }"
            "QPushButton:hover { background:#b91c1c; }"
        )

        self.chosen_status = None
        self.done_btn.clicked.connect(lambda: self._choose("DONE"))
        self.partial_btn.clicked.connect(lambda: self._choose("PARTIAL"))
        self.failed_btn.clicked.connect(lambda: self._choose("FAILED"))

        row = QHBoxLayout()
        row.addWidget(self.done_btn)
        row.addWidget(self.partial_btn)
        row.addWidget(self.failed_btn)
        layout.addLayout(row)

    def _choose(self, status: str):
        self.chosen_status = status
        self.accept()

    def get_note(self) -> str:
        return self.note_input.toPlainText().strip()


# ─── ActionsScreen ────────────────────────────────────────────────────────────

class ActionsScreen(QWidget):
    """
    Actions Workspace — real data from ActionsService.
    Three tabs: Pending / In Progress / Completed.
    Each action card has status toggle buttons.
    """

    STATUS_COLORS = {
        "PENDING":     ("#fffbeb", "#fde68a", "#b45309"),  # bg, border, text
        "IN_PROGRESS": ("#eff6ff", "#bfdbfe", "#1d4ed8"),
        "DONE":        ("#f0fdf4", "#86efac", "#166534"),
        "PARTIAL":     ("#fff7ed", "#fed7aa", "#c2410c"),
        "FAILED":      ("#fef2f2", "#fca5a5", "#b91c1c"),
    }

    STATUS_LABELS = {
        "PENDING":     "Pending",
        "IN_PROGRESS": "In Progress",
        "DONE":        "Done",
        "PARTIAL":     "Partial",
        "FAILED":      "Didn't Work",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self._svc = ActionsService()
        self._active_tab = "PENDING"
        self._canvas_layout = None
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        # Header
        hdr_row = QHBoxLayout()
        header = QLabel("Actions")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        hdr_row.addWidget(header, stretch=1)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet(
            "QPushButton { background:#f8fafc; border:1px solid #e2e8f0; "
            "border-radius:6px; color:#334155; font-size:9.5pt; padding:0 12px; }"
            "QPushButton:hover { background:#e2e8f0; }"
        )
        refresh_btn.clicked.connect(self.refresh_data)
        hdr_row.addWidget(refresh_btn)
        root.addLayout(hdr_row)

        sub = QLabel(
            "Action items extracted from your diagnosis. "
            "Mark each one when done — outcomes improve your next diagnosis."
        )
        sub.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Tab bar
        self._tab_bar = QHBoxLayout()
        self._tab_bar.setSpacing(6)
        self._tab_btns = {}

        for key, label in [
            ("PENDING", "Pending"),
            ("IN_PROGRESS", "In Progress"),
            ("DONE", "Completed"),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setCheckable(True)
            btn.setStyleSheet(self._tab_qss(False))
            btn.clicked.connect(lambda _, k=key: self._switch_tab(k))
            self._tab_btns[key] = btn
            self._tab_bar.addWidget(btn)
        self._tab_bar.addStretch()
        root.addLayout(self._tab_bar)

        # Scroll area for action cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._canvas = QWidget()
        self._canvas_layout = QVBoxLayout(self._canvas)
        self._canvas_layout.setContentsMargins(0, 4, 0, 4)
        self._canvas_layout.setSpacing(12)
        self._canvas_layout.addStretch()

        scroll.setWidget(self._canvas)
        root.addWidget(scroll, stretch=1)

        self._switch_tab("PENDING")

    # ── Tab ───────────────────────────────────────────────────────────────────

    def _switch_tab(self, key: str):
        self._active_tab = key
        for k, btn in self._tab_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._tab_qss(k == key))
        self._rebuild_cards()

    @staticmethod
    def _tab_qss(active: bool) -> str:
        if active:
            return (
                "QPushButton { background:#1a7a3c; color:#fff; border-radius:8px; "
                "font-weight:bold; font-size:9.5pt; padding:0 14px; border:none; }"
            )
        return (
            "QPushButton { background:#f0fbf4; color:#1e4433; border:1px solid #ccebd7; "
            "border-radius:8px; font-size:9.5pt; padding:0 14px; }"
            "QPushButton:hover { background:#d1f5e0; }"
        )

    # ── Cards ─────────────────────────────────────────────────────────────────

    def _rebuild_cards(self):
        """Clears and rebuilds action cards for the active tab."""
        while self._canvas_layout.count() > 1:
            item = self._canvas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Fetch actions for the active tab
        if self._active_tab == "DONE":
            items = (
                self._svc.get_actions_by_status("DONE") +
                self._svc.get_actions_by_status("PARTIAL") +
                self._svc.get_actions_by_status("FAILED")
            )
        else:
            items = self._svc.get_actions_by_status(self._active_tab)

        if not items:
            self._show_empty_state()
            return

        # Group by session/challenge
        current_challenge = None
        for action in items:
            challenge = action.get("challenge_summary", "")
            if challenge and challenge != current_challenge:
                current_challenge = challenge
                group_lbl = QLabel(f"From: {challenge[:80]}")
                group_lbl.setStyleSheet(
                    "color:#1a7a3c; font-size:8pt; font-weight:bold; "
                    "letter-spacing:0.5px; margin-top:4px;"
                )
                self._canvas_layout.insertWidget(
                    self._canvas_layout.count() - 1, group_lbl
                )
            card = self._make_action_card(action)
            self._canvas_layout.insertWidget(self._canvas_layout.count() - 1, card)

    def _show_empty_state(self):
        if self._active_tab == "PENDING":
            msg = (
                "No pending actions.\n\n"
                "Run a Diagnosis — action items will be automatically\n"
                "extracted and appear here."
            )
        elif self._active_tab == "IN_PROGRESS":
            msg = "No actions in progress."
        else:
            msg = (
                "No completed actions yet.\n\n"
                "When you mark actions as Done, Partial, or Failed,\n"
                "the results improve your next diagnosis."
            )
        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "color:#94a3b8; font-size:10.5pt; font-style:italic; padding:48px;"
        )
        lbl.setWordWrap(True)
        self._canvas_layout.insertWidget(0, lbl)

    def _make_action_card(self, action: dict) -> QFrame:
        status = action.get("status", "PENDING")
        bg, border, text_col = self.STATUS_COLORS.get(status, ("#fff", "#e2e8f0", "#333"))

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{bg}; border:1px solid {border}; "
            f"border-left:4px solid {text_col}; border-radius:10px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)

        # Header row: order badge + status pill
        hdr = QHBoxLayout()
        order_badge = QLabel(f"#{action.get('action_order', '?')}")
        order_badge.setStyleSheet(
            f"background:{text_col}; color:#fff; font-weight:bold; "
            f"font-size:8pt; padding:2px 7px; border-radius:8px; border:none;"
        )
        fw_lbl = QLabel(action.get("framework_used", ""))
        fw_lbl.setStyleSheet("color:#64748b; font-size:8.5pt; border:none;")
        status_pill = QLabel(self.STATUS_LABELS.get(status, status))
        status_pill.setStyleSheet(
            f"color:{text_col}; font-weight:bold; font-size:8.5pt; border:none;"
        )
        hdr.addWidget(order_badge)
        hdr.addWidget(fw_lbl)
        hdr.addStretch()
        hdr.addWidget(status_pill)
        card_layout.addLayout(hdr)

        # Action text
        action_lbl = QLabel(action.get("action_text", ""))
        action_lbl.setStyleSheet(
            "color:#0f2318; font-size:10.5pt; font-weight:600; border:none;"
        )
        action_lbl.setWordWrap(True)
        card_layout.addWidget(action_lbl)

        # Outcome note if present
        if action.get("outcome_note"):
            note_lbl = QLabel(f"Outcome: {action['outcome_note']}")
            note_lbl.setStyleSheet("color:#64748b; font-size:9pt; font-style:italic; border:none;")
            note_lbl.setWordWrap(True)
            card_layout.addWidget(note_lbl)

        # Action buttons — only show for actionable states
        if status in ("PENDING", "IN_PROGRESS"):
            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            if status == "PENDING":
                start_btn = self._make_btn(
                    "Start Working", "#1d4ed8", "#1e40af"
                )
                start_btn.clicked.connect(
                    lambda _, aid=action["id"]: self._on_start(aid)
                )
                btn_row.addWidget(start_btn)

            record_btn = self._make_btn("Record Outcome", "#1a7a3c", "#145e2e")
            record_btn.clicked.connect(
                lambda _, a=action: self._on_record_outcome(a)
            )
            btn_row.addWidget(record_btn)
            btn_row.addStretch()
            card_layout.addLayout(btn_row)

        return card

    @staticmethod
    def _make_btn(label: str, bg: str, bg_hover: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            f"QPushButton {{ background:{bg}; color:#fff; border-radius:6px; "
            f"font-weight:bold; font-size:9pt; padding:0 12px; border:none; }}"
            f"QPushButton:hover {{ background:{bg_hover}; }}"
        )
        return btn

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_start(self, action_id: str):
        self._svc.update_status(action_id, "IN_PROGRESS")
        self._switch_tab(self._active_tab)

    def _on_record_outcome(self, action: dict):
        dlg = OutcomeNoteDialog(action.get("action_text", ""), self)
        if dlg.exec():
            status = dlg.chosen_status or "DONE"
            note = dlg.get_note()
            self._svc.update_status(action["id"], status, note)
            # Refresh TodayScreen so follow-up card updates
            if self.main_app and hasattr(self.main_app, "today_screen"):
                ts = self.main_app.today_screen
                if hasattr(ts, "refresh_data"):
                    ts.refresh_data()
            self._switch_tab(self._active_tab)

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh_data(self):
        self._rebuild_cards()
