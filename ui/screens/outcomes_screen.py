from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from db.outcome_tracker import OutcomeTrackerDB

class OutcomesScreen(QWidget):
    """
    Dedicated Outcomes Dashboard Screen.
    Backed by OutcomeTrackerDB SQLite history (baseline vs target vs actual ARR impact).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.db = OutcomeTrackerDB()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        header = QLabel("📈 Measured Business Outcomes")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        layout.addWidget(header)

        sub_header = QLabel("Verified business impact, ARR influence, and baseline vs actual metrics")
        sub_header.setStyleSheet("color: #4b6b5a; font-size: 11pt; margin-bottom: 10px;")
        layout.addWidget(sub_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        outcomes = self.db.get_outcome_history()

        if not outcomes:
            # Informative Empty State
            empty_card = QFrame()
            empty_card.setStyleSheet("background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 24px;")
            empty_layout = QVBoxLayout(empty_card)
            
            empty_title = QLabel("No measured outcomes yet.")
            empty_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            empty_title.setStyleSheet("color: #0f2318;")
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            empty_desc = QLabel("Complete an approved action and measure its result to start building your business learning history.")
            empty_desc.setStyleSheet("color: #4b6b5a; font-size: 10pt;")
            empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            empty_layout.addWidget(empty_title)
            empty_layout.addWidget(empty_desc)
            container_layout.addWidget(empty_card)
        else:
            for item in outcomes:
                card = QFrame()
                card.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 16px;")
                card_layout = QVBoxLayout(card)
                
                title = QLabel(f"<b>{item['problem']}</b> ({item['framework']})")
                title.setStyleSheet("color: #6ee7b7; font-size: 12pt;")
                
                metrics = QLabel(f"Metric: {item['metric']} • Baseline: {item['baseline']} ➔ Target: {item['target']} ➔ Actual: {item['actual'] or 'N/A'}")
                metrics.setStyleSheet("color: #f1f5f9; font-size: 10.5pt; margin-top: 4px;")
                
                arr = QLabel(f"<b>Status:</b> {item['status']} • <b>ARR Influenced:</b> +${item['arr_impact']:,.2f}")
                arr.setStyleSheet("color: #38bdf8; font-size: 10.5pt; margin-top: 2px;")
                
                card_layout.addWidget(title)
                card_layout.addWidget(metrics)
                card_layout.addWidget(arr)
                container_layout.addWidget(card)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
