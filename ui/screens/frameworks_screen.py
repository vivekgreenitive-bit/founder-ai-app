from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class FrameworksScreen(QWidget):
    """
    Dedicated 2-Column Interactive Frameworks Library Screen matching founderframeworkslab.com.
    Left Column: Selectable Framework Cards with Category Pills.
    Right Column: Full Mnemonic Breakdown & Structured Details.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.active_category = "Planning"
        self.selected_framework_key = "ECG KISS"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Header Section ───────────────────────────────────────────────────
        header = QLabel("Framework Library")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("color: #0f2318;")
        layout.addWidget(header)

        sub_header = QLabel("Explore the 13 Lab-tested execution blueprints from the Founder Frameworks playbook.")
        sub_header.setStyleSheet("color: #4b6b5a; font-size: 11pt;")
        layout.addWidget(sub_header)

        # ── Category Filter Bar ──────────────────────────────────────────────
        cat_bar = QHBoxLayout()
        cat_bar.setSpacing(12)
        cat_bar.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.cat_btns = {}
        for cat in ["Planning", "Operations", "Execution"]:
            btn = QPushButton(cat)
            btn.setFixedHeight(34)
            btn.setFixedWidth(110)
            btn.setCheckable(True)
            if cat == "Planning":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #2d4536;
                    border: 1px solid #ccebd7;
                    border-radius: 17px;
                    font-weight: 600;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #ebf7f0;
                    color: #1a7a3c;
                }
                QPushButton:checked {
                    background-color: #ffffff;
                    color: #1a7a3c;
                    border: 2px solid #1a7a3c;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, c=cat: self.select_category(c))
            cat_bar.addWidget(btn)
            self.cat_btns[cat] = btn

        layout.addLayout(cat_bar)

        # ── Main 2-Column Body Layout ────────────────────────────────────────
        body_layout = QHBoxLayout()
        body_layout.setSpacing(20)

        # --- LEFT COLUMN: Framework List Cards ---
        left_column = QFrame()
        left_column.setFixedWidth(300)
        left_column.setStyleSheet("background: transparent; border: none;")
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.list_scroll = QScrollArea()
        self.list_scroll.setWidgetResizable(True)
        self.list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_scroll.setStyleSheet("background: transparent;")

        self.list_container = QWidget()
        self.list_container_layout = QVBoxLayout(self.list_container)
        self.list_container_layout.setContentsMargins(0, 0, 0, 0)
        self.list_container_layout.setSpacing(8)

        self.list_scroll.setWidget(self.list_container)
        left_layout.addWidget(self.list_scroll)
        body_layout.addWidget(left_column)

        # --- RIGHT COLUMN: Detailed Framework View Card ---
        self.right_detail_card = QFrame()
        self.right_detail_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ebf7f0;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        self.right_layout = QVBoxLayout(self.right_detail_card)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(14)

        body_layout.addWidget(self.right_detail_card, stretch=1)
        layout.addLayout(body_layout, stretch=1)

        # Framework Database with Full Mnemonic Details
        self.framework_data = {
            "ECG KISS": {
                "category": "Planning",
                "badge": "OVERALL BUSINESS",
                "tagline": "The diagnostic starting point to audit, align, and bridge the GAP in your overall business strategy.",
                "is_free": True,
                "mnemonics": [
                    ("E", "End Goal", "The business's north star providing direction and purpose."),
                    ("C", "Current Pain Points", "Identify key bottlenecks grounding your strategy in real facts."),
                    ("G", "GAP", "The measurable distance between where you are and where you aim to be."),
                    ("K", "Keep", "High-value activities to preserve and double down on."),
                    ("I", "Improve", "Processes needing optimization and operational polish."),
                    ("S", "Stop", "Low-ROI distractions to immediately eliminate."),
                    ("S", "Start", "New strategic initiatives required to achieve the GAP.")
                ]
            },
            "SLR CAMERAS": {
                "category": "Planning",
                "badge": "YEARLY",
                "tagline": "A resource-centric yearly planning engine for startups to map milestones and ensure growth.",
                "is_free": True,
                "mnemonics": [
                    ("S", "Strategic Targets", "Set firm annual revenue and product milestones."),
                    ("L", "Levers", "Identify primary growth drivers for the next 12 months."),
                    ("R", "Resource Allocation", "Distribute capital and talent to core priorities.")
                ]
            },
            "MC BEERS": {
                "category": "Planning",
                "badge": "QUARTERLY",
                "tagline": "Break down annual goals into focused 90-day execution sprints.",
                "is_free": False,
                "mnemonics": [
                    ("M", "Milestones", "Define 3 core non-negotiable quarterly outcomes."),
                    ("C", "Capacity Audit", "Ensure team bandwith aligns with sprint goals.")
                ]
            },
            "PC PEERS": {
                "category": "Planning",
                "badge": "MONTHLY",
                "tagline": "Manage monthly priorities, people, and execution checkpoints.",
                "is_free": False,
                "mnemonics": [
                    ("P", "Priorities", "Select top 3 focus areas for the month."),
                    ("C", "Checkpoints", "Weekly progress reviews to keep velocity high.")
                ]
            },
            "PS ERP": {
                "category": "Planning",
                "badge": "WEEKLY",
                "tagline": "Organize weekly focus so you stop wasting time on low-value tasks.",
                "is_free": False,
                "mnemonics": [
                    ("P", "Priority Focus", "Identify non-negotiable weekly deliverables."),
                    ("S", "Schedule Shielding", "Block calendar focus blocks for deep work.")
                ]
            },
            "DC ERPRS": {
                "category": "Planning",
                "badge": "DAILY",
                "tagline": "Structure each day to maximize output and create execution momentum.",
                "is_free": False,
                "mnemonics": [
                    ("D", "Daily Wins", "Select 3 high-impact tasks for the day."),
                    ("C", "Clear Blockers", "Resolve impediments early in the morning.")
                ]
            },
            "OKS REC SME": {
                "category": "Operations",
                "badge": "SYSTEMS",
                "tagline": "The core methodology for building system-dependent businesses and removing bottlenecks.",
                "is_free": False,
                "mnemonics": [
                    ("O", "Operating Rules", "Document standard operating procedures for routine tasks."),
                    ("K", "Key Metrics", "Define real-time indicators for operational health.")
                ]
            },
            "PFA SAAS SME": {
                "category": "Operations",
                "badge": "PROCESS MAPPING",
                "tagline": "A streamlining framework for defining and optimizing core business process arteries.",
                "is_free": False,
                "mnemonics": [
                    ("P", "Process Mapping", "Map step-by-step handoffs across team functions.")
                ]
            },
            "RSS FEED SME": {
                "category": "Operations",
                "badge": "SOP BUILDER",
                "tagline": "Create SOPs so your team executes consistently without founder intervention.",
                "is_free": False,
                "mnemonics": [
                    ("R", "Routine Checklist", "Build daily operational checklists for error-free output.")
                ]
            },
            "RPM REAP ER": {
                "category": "Execution",
                "badge": "EXECUTION STRATEGY",
                "tagline": "The ultimate framework for overcoming team inertia and delivering high-stakes results.",
                "is_free": False,
                "mnemonics": [
                    ("R", "Result Target", "State exact quantitative result required."),
                    ("P", "Purpose", "Define why this outcome is critical right now.")
                ]
            },
            "RUN DCMS ER": {
                "category": "Execution",
                "badge": "REVENUE GENERATION",
                "tagline": "A cash-flow centered framework for managing sales funnels and increasing MRR.",
                "is_free": False,
                "mnemonics": [
                    ("R", "Revenue Bottleneck", "Diagnose top barrier in conversion funnel.")
                ]
            },
            "ERM FABS ER": {
                "category": "Execution",
                "badge": "EVALUATION",
                "tagline": "Evaluate what is working and what needs immediate strategic intervention.",
                "is_free": False,
                "mnemonics": [
                    ("E", "Evaluation Audit", "Perform bi-weekly execution scorecard review.")
                ]
            },
            "ADMINS ER": {
                "category": "Execution",
                "badge": "CRISIS MANAGEMENT",
                "tagline": "Manage an active business crisis with structured emergency protocols.",
                "is_free": False,
                "mnemonics": [
                    ("A", "Assess Damage", "Calculate immediate risk and cash impact.")
                ]
            }
        }

        # Initial render
        self.render_framework_list()
        self.render_framework_detail("ECG KISS")

    def select_category(self, cat: str):
        self.active_category = cat
        for c, btn in self.cat_btns.items():
            btn.setChecked(c == cat)
        
        # Pick first framework in category
        for name, data in self.framework_data.items():
            if data["category"] == cat:
                self.selected_framework_key = name
                break
        
        self.render_framework_list()
        self.render_framework_detail(self.selected_framework_key)

    def render_framework_list(self):
        # Clear existing cards
        while self.list_container_layout.count():
            item = self.list_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name, data in self.framework_data.items():
            if data["category"] != self.active_category:
                continue

            is_selected = (name == self.selected_framework_key)
            card = QFrame()
            card.setFixedHeight(54)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            
            border_color = "#1a7a3c" if is_selected else "#e2e8f0"
            bg_color = "#f4fbf7" if is_selected else "#ffffff"
            text_color = "#1a7a3c" if is_selected else "#2d4536"

            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 10px;
                    padding: 6px 12px;
                }}
                QFrame:hover {{
                    border: 1px solid #1a7a3c;
                }}
            """)

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 0, 10, 0)

            title_lbl = QLabel(f"<b>{name}</b>")
            title_lbl.setStyleSheet(f"color: {text_color}; font-size: 11pt; border: none; background: transparent;")
            card_layout.addWidget(title_lbl, stretch=1)

            badge_lbl = QLabel(data["badge"])
            badge_lbl.setStyleSheet(
                "color: #1a7a3c; background: #e2f5ea; font-size: 7.5pt; "
                "font-weight: bold; padding: 3px 6px; border-radius: 4px; border: none;"
            )
            card_layout.addWidget(badge_lbl)

            # Store key on card & make clickable
            card.mousePressEvent = lambda event, k=name: self.on_card_click(k)
            self.list_container_layout.addWidget(card)

        self.list_container_layout.addStretch()

    def on_card_click(self, key: str):
        self.selected_framework_key = key
        self.render_framework_list()
        self.render_framework_detail(key)

    def render_framework_detail(self, key: str):
        # Clear right detail layout
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # clear nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        data = self.framework_data.get(key, self.framework_data["ECG KISS"])

        # Title Row
        title_row = QHBoxLayout()
        name_lbl = QLabel(key)
        name_lbl.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: #1a7a3c;")
        title_row.addWidget(name_lbl)

        badge_lbl = QLabel(data["badge"])
        badge_lbl.setStyleSheet(
            "color: #1a7a3c; background: #e2f5ea; font-size: 9pt; "
            "font-weight: bold; padding: 4px 10px; border-radius: 12px; border: 1px solid #bbf7d0;"
        )
        title_row.addWidget(badge_lbl)
        
        tier_lbl = QLabel("✓ INCLUDED" if data["is_free"] else "🔒 PRO")
        tier_lbl.setStyleSheet(
            "color: #ffffff; background: #166534; font-size: 9pt; font-weight: bold; padding: 4px 10px; border-radius: 12px;"
            if data["is_free"] else
            "color: #ffffff; background: #7c3aed; font-size: 9pt; font-weight: bold; padding: 4px 10px; border-radius: 12px;"
        )
        title_row.addWidget(tier_lbl)
        title_row.addStretch()
        self.right_layout.addLayout(title_row)

        # Tagline
        tag_lbl = QLabel(data["tagline"])
        tag_lbl.setStyleSheet("color: #4b6b5a; font-size: 11.5pt; margin-bottom: 10px;")
        tag_lbl.setWordWrap(True)
        self.right_layout.addWidget(tag_lbl)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #ebf7f0;")
        self.right_layout.addWidget(divider)

        # Scrollable Mnemonic Breakdown
        m_scroll = QScrollArea()
        m_scroll.setWidgetResizable(True)
        m_scroll.setFrameShape(QFrame.Shape.NoFrame)
        m_scroll.setStyleSheet("background: transparent;")

        m_container = QWidget()
        m_layout = QVBoxLayout(m_container)
        m_layout.setContentsMargins(0, 8, 0, 8)
        m_layout.setSpacing(12)

        for letter, title, desc in data["mnemonics"]:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #f0fdf4;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(14)

            # Circle Letter Pill
            circle = QLabel(letter)
            circle.setFixedSize(32, 32)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            circle.setStyleSheet(
                "color: #1a7a3c; background: #e2f5ea; border-radius: 16px; border: 1px solid #86efac;"
            )
            row_layout.addWidget(circle)

            # Text Info
            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            
            m_title = QLabel(f"<b>{title}</b>")
            m_title.setStyleSheet("color: #0f2318; font-size: 11pt;")
            
            m_desc = QLabel(desc)
            m_desc.setStyleSheet("color: #4b6b5a; font-size: 10pt;")
            m_desc.setWordWrap(True)

            text_box.addWidget(m_title)
            text_box.addWidget(m_desc)
            row_layout.addLayout(text_box, stretch=1)

            m_layout.addWidget(row)

        m_layout.addStretch()
        m_scroll.setWidget(m_container)
        self.right_layout.addWidget(m_scroll, stretch=1)

        # Bottom Action Bar
        act_bar = QHBoxLayout()
        run_btn = QPushButton("Run Diagnosis with This Framework")
        run_btn.setFixedHeight(38)
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a7a3c;
                color: #ffffff;
                border-radius: 8px;
                font-weight: bold;
                font-size: 10.5pt;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #145e2e;
            }
        """)
        if self.main_app and hasattr(self.main_app, "switch_to_diagnose"):
            run_btn.clicked.connect(self.main_app.switch_to_diagnose)

        act_bar.addWidget(run_btn)
        act_bar.addStretch()
        self.right_layout.addLayout(act_bar)

