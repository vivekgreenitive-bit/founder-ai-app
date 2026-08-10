"""
ui/screens/velocity_grader_screen.py
Execution Velocity Grader UI Screen.
Displays 0-100 Execution Velocity Scorecard, cycle time metrics, and performance recommendations.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from agents.velocity_agent import VelocityAgent


class VelocityGraderScreen(QWidget):
    """
    Execution Velocity Scorecard UI Screen.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.agent = VelocityAgent()
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QLabel("⚡ Execution Velocity Grader")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        root.addWidget(header)

        sub = QLabel(
            "Measures how fast your startup executes decisions into measured outcomes. "
            "Higher execution velocity directly correlates with faster ARR growth and higher valuation multiples."
        )
        sub.setStyleSheet("color: #4b6b5a; font-size: 10.5pt;")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Velocity Meter Card
        card = QFrame()
        card.setStyleSheet("background: #ffffff; border: 1px solid #ccebd7; border-radius: 12px; padding: 24px;")
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        title_lbl = QLabel("CURRENT EXECUTION VELOCITY SCORE")
        title_lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #1a7a3c; letter-spacing: 1px;")

        self.status_badge = QLabel("HEALTHY")
        self.status_badge.setStyleSheet("background: #e2f5ea; color: #1a7a3c; font-weight: bold; font-size: 8.5pt; padding: 3px 10px; border-radius: 10px;")

        top_row.addWidget(title_lbl)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        layout.addLayout(top_row)

        # Meter Progress Bar
        self.score_num_lbl = QLabel("85 / 100")
        self.score_num_lbl.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.score_num_lbl.setStyleSheet("color: #0f2318;")
        layout.addWidget(self.score_num_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(85)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e2e8f0;
                border-radius: 7px;
            }
            QProgressBar::chunk {
                background-color: #1a7a3c;
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # 3 Metrics Breakdown Row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)

        self.m1_lbl = self._make_metric_box("Completed Actions", "0", metrics_row)
        self.m2_lbl = self._make_metric_box("Completion Rate", "100%", metrics_row)
        self.m3_lbl = self._make_metric_box("Avg Cycle Time", "1.5 Days", metrics_row)

        layout.addLayout(metrics_row)
        root.addWidget(card)

        # Recommendation CTA
        rec_card = QFrame()
        rec_card.setStyleSheet("background: #f0fbf4; border: 1px solid #ccebd7; border-left: 4px solid #1a7a3c; border-radius: 8px; padding: 14px;")
        rec_layout = QVBoxLayout(rec_card)

        rec_title = QLabel("💡 Execution Speed Recommendation")
        rec_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        rec_title.setStyleSheet("color: #1a7a3c;")
        rec_layout.addWidget(rec_title)

        self.rec_body = QLabel("Your execution velocity is healthy. Keep resolving pending actions in the Actions workspace to maintain momentum.")
        self.rec_body.setStyleSheet("color: #2d4536; font-size: 10pt;")
        self.rec_body.setWordWrap(True)
        rec_layout.addWidget(self.rec_body)

        root.addWidget(rec_card)

        btn_row = QHBoxLayout()
        self.actions_btn = QPushButton("Open Actions Workspace ➔")
        self.actions_btn.setFixedHeight(40)
        self.actions_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10pt;
                padding: 0 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        if self.main_app and hasattr(self.main_app, "switch_nav"):
            self.actions_btn.clicked.connect(lambda: self.main_app.switch_nav("actions"))

        btn_row.addWidget(self.actions_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addStretch()
        self.refresh_data()

    def _make_metric_box(self, title: str, default_val: str, parent_layout: QHBoxLayout) -> QLabel:
        box = QFrame()
        box.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px;")
        b_layout = QVBoxLayout(box)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #64748b; font-size: 8.5pt; font-weight: bold;")
        val_lbl = QLabel(default_val)
        val_lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        val_lbl.setStyleSheet("color: #0f2318;")
        b_layout.addWidget(t_lbl)
        b_layout.addWidget(val_lbl)
        parent_layout.addWidget(box, stretch=1)
        return val_lbl

    def refresh_data(self):
        res = self.agent.compute_velocity()
        score = res["velocity_score"]
        status = res["status"]

        self.score_num_lbl.setText(f"{score} / 100")
        self.progress_bar.setValue(score)
        self.status_badge.setText(status)

        self.m1_lbl.setText(str(res["completed_count"]))
        self.m2_lbl.setText(f"{res['completion_rate_pct']}%")
        self.m3_lbl.setText(f"{res['avg_cycle_days']} Days")

        self.rec_body.setText(res["message"])
