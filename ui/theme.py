"""
ui/theme.py — Founder AI Design Token System
Single source of truth for all QSS colors, typography, spacing, radius, and component styles.
All screens must import from here. Zero scattered QSS strings across files.
"""

# ─────────────────────────────────────────────────────────────────────────────
# COLOR TOKENS — Matches founderframeworkslab.com brand palette
# Neutral surfaces dominate; Forest Green is brand/action/success accent only.
# ─────────────────────────────────────────────────────────────────────────────

# Surfaces
COLOR_BG_APP         = "#f8fafc"   # Main window / page background
COLOR_BG_SIDEBAR     = "#f0fbf4"   # Left navigation panel
COLOR_BG_SURFACE     = "#ffffff"   # Card / elevated surface
COLOR_BG_MUTED       = "#f1f5f9"   # Input backgrounds, secondary surfaces

# Brand
COLOR_BRAND_PRIMARY  = "#1a7a3c"   # Forest Green — primary CTAs, active nav, badges
COLOR_BRAND_DARK     = "#145e2e"   # Hover state for primary
COLOR_BRAND_LIGHT    = "#e2f5ea"   # Light green pill backgrounds
COLOR_BRAND_MINT     = "#f0fbf4"   # Sidebar tint

# Text
COLOR_TEXT_PRIMARY   = "#0f2318"   # Headlines, primary labels (dark green-black)
COLOR_TEXT_SECONDARY = "#2d4536"   # Secondary body text
COLOR_TEXT_MUTED     = "#64748b"   # Captions, hints, meta
COLOR_TEXT_INVERSE   = "#ffffff"   # Text on dark/brand backgrounds

# Borders
COLOR_BORDER_SUBTLE  = "#e2e8f0"   # Default card borders
COLOR_BORDER_BRAND   = "#ccebd7"   # Branded/mint borders (sidebar, focus)
COLOR_BORDER_STRONG  = "#94a3b8"   # Input focus, emphasized borders

# Semantic
COLOR_SUCCESS        = "#1a7a3c"
COLOR_SUCCESS_BG     = "#e2f5ea"
COLOR_WARNING        = "#b45309"
COLOR_WARNING_BG     = "#fef3c7"
COLOR_DANGER         = "#dc2626"
COLOR_DANGER_BG      = "#fee2e2"
COLOR_INFO           = "#2563eb"
COLOR_INFO_BG        = "#eff6ff"

# Plan badges
COLOR_FREE_BG        = "#e2f5ea"
COLOR_FREE_FG        = "#1a7a3c"
COLOR_PRO_BG         = "#f3e8ff"
COLOR_PRO_FG         = "#7c3aed"

# ─────────────────────────────────────────────────────────────────────────────
# TYPOGRAPHY TOKENS
# ─────────────────────────────────────────────────────────────────────────────
FONT_FAMILY          = "Arial"      # Cross-platform fallback; macOS uses SF Pro
FONT_SIZE_DISPLAY    = "22pt"
FONT_SIZE_H1         = "18pt"
FONT_SIZE_H2         = "14pt"
FONT_SIZE_H3         = "12pt"
FONT_SIZE_BODY       = "10.5pt"
FONT_SIZE_SMALL      = "9.5pt"
FONT_SIZE_CAPTION    = "8.5pt"
FONT_SIZE_METRIC     = "20pt"
FONT_SIZE_BUTTON     = "10.5pt"

# ─────────────────────────────────────────────────────────────────────────────
# SPACING & RADIUS TOKENS
# ─────────────────────────────────────────────────────────────────────────────
RADIUS_SM            = "6px"
RADIUS_MD            = "8px"
RADIUS_LG            = "12px"
RADIUS_XL            = "16px"
RADIUS_PILL          = "20px"

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENT QSS BUILDERS
# All screens call these functions; never write raw QSS strings inline.
# ─────────────────────────────────────────────────────────────────────────────

def qss_app_window() -> str:
    return f"""
        QMainWindow {{
            background-color: {COLOR_BG_APP};
        }}
        QWidget#AppRoot {{
            background-color: {COLOR_BG_APP};
        }}
    """

def qss_sidebar() -> str:
    return f"""
        QWidget#Sidebar {{
            background-color: {COLOR_BG_SIDEBAR};
            border-right: 1px solid {COLOR_BORDER_BRAND};
        }}
    """

def qss_nav_button() -> str:
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {COLOR_TEXT_SECONDARY};
            border: none;
            border-radius: {RADIUS_MD};
            text-align: left;
            padding: 10px 14px;
            font-size: {FONT_SIZE_BODY};
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BRAND_LIGHT};
            color: {COLOR_BRAND_PRIMARY};
        }}
        QPushButton:checked {{
            background-color: {COLOR_BRAND_PRIMARY};
            color: {COLOR_TEXT_INVERSE};
        }}
    """

def qss_primary_button() -> str:
    return f"""
        QPushButton {{
            background-color: {COLOR_BRAND_PRIMARY};
            color: {COLOR_TEXT_INVERSE};
            border: none;
            border-radius: {RADIUS_MD};
            padding: 0 20px;
            font-size: {FONT_SIZE_BUTTON};
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BRAND_DARK};
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BG_MUTED};
            color: {COLOR_TEXT_MUTED};
        }}
    """

def qss_secondary_button() -> str:
    return f"""
        QPushButton {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_SECONDARY};
            border: 1px solid {COLOR_BORDER_SUBTLE};
            border-radius: {RADIUS_MD};
            padding: 0 16px;
            font-size: {FONT_SIZE_BUTTON};
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {COLOR_BG_MUTED};
            border-color: {COLOR_BORDER_STRONG};
            color: {COLOR_TEXT_PRIMARY};
        }}
        QPushButton:disabled {{
            color: {COLOR_TEXT_MUTED};
            border-color: {COLOR_BORDER_SUBTLE};
        }}
    """

def qss_card() -> str:
    return f"""
        QFrame {{
            background-color: {COLOR_BG_SURFACE};
            border: 1px solid {COLOR_BORDER_SUBTLE};
            border-radius: {RADIUS_LG};
        }}
    """

def qss_card_branded() -> str:
    return f"""
        QFrame {{
            background-color: {COLOR_BG_SURFACE};
            border: 1px solid {COLOR_BORDER_BRAND};
            border-left: 4px solid {COLOR_BRAND_PRIMARY};
            border-radius: {RADIUS_LG};
        }}
    """

def qss_header_bar() -> str:
    return f"""
        QWidget#HeaderBar {{
            background-color: {COLOR_BG_SURFACE};
            border-bottom: 1px solid {COLOR_BORDER_SUBTLE};
        }}
    """

def qss_text_input() -> str:
    return f"""
        QLineEdit, QPlainTextEdit, QTextEdit {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_PRIMARY};
            border: 1px solid {COLOR_BORDER_SUBTLE};
            border-radius: {RADIUS_MD};
            padding: 8px 12px;
            font-size: {FONT_SIZE_BODY};
            selection-background-color: {COLOR_BRAND_LIGHT};
        }}
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{
            border: 2px solid {COLOR_BRAND_PRIMARY};
        }}
    """

def qss_account_menu() -> str:
    return f"""
        QMenu {{
            background-color: {COLOR_BG_SURFACE};
            border: 1px solid {COLOR_BORDER_SUBTLE};
            border-radius: {RADIUS_MD};
            padding: 6px;
        }}
        QMenu::item {{
            padding: 8px 20px;
            color: {COLOR_TEXT_PRIMARY};
            font-size: {FONT_SIZE_BODY};
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {COLOR_BRAND_LIGHT};
            color: {COLOR_BRAND_PRIMARY};
            font-weight: bold;
        }}
        QMenu::separator {{
            height: 1px;
            background: {COLOR_BORDER_SUBTLE};
            margin: 4px 0;
        }}
    """

def qss_status_bar_ready() -> str:
    return f"color: {COLOR_BRAND_PRIMARY}; font-weight: bold; font-size: 11px;"

def qss_status_bar_error() -> str:
    return f"color: {COLOR_DANGER}; font-weight: bold; font-size: 11px;"

def qss_status_bar_loading() -> str:
    return f"color: {COLOR_WARNING}; font-weight: bold; font-size: 11px;"

def qss_badge_free() -> str:
    return f"""
        background: {COLOR_FREE_BG};
        color: {COLOR_FREE_FG};
        font-weight: bold;
        font-size: {FONT_SIZE_CAPTION};
        padding: 2px 8px;
        border-radius: {RADIUS_PILL};
        border: 1px solid {COLOR_BORDER_BRAND};
    """

def qss_badge_pro() -> str:
    return f"""
        background: {COLOR_PRO_BG};
        color: {COLOR_PRO_FG};
        font-weight: bold;
        font-size: {FONT_SIZE_CAPTION};
        padding: 2px 8px;
        border-radius: {RADIUS_PILL};
    """

def qss_focus_pill(category: str) -> str:
    """For Diagnose screen focus area selector pills."""
    return f"""
        QPushButton {{
            background-color: {COLOR_BG_SURFACE};
            color: {COLOR_TEXT_SECONDARY};
            border: 1px solid {COLOR_BORDER_SUBTLE};
            border-radius: {RADIUS_PILL};
            padding: 6px 16px;
            font-size: {FONT_SIZE_SMALL};
            font-weight: 600;
        }}
        QPushButton:checked {{
            background-color: {COLOR_BRAND_PRIMARY};
            color: {COLOR_TEXT_INVERSE};
            border: none;
        }}
        QPushButton:hover:!checked {{
            background-color: {COLOR_BRAND_LIGHT};
            color: {COLOR_BRAND_PRIMARY};
            border-color: {COLOR_BORDER_BRAND};
        }}
    """
