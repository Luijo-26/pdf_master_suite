"""
ui/theme.py
Sistema de diseño de PDF Master Suite: paleta oscura, metadatos de herramientas,
hoja de estilos global (QSS) y utilidades de color.
"""

from dataclasses import dataclass
from typing import List

from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtWidgets import QApplication, QWidget


# -----------------------------------------------------------------------------
# PALETA
# -----------------------------------------------------------------------------
class C:
    BG = "#0E0F14"
    SIDEBAR = "#111218"
    SURFACE = "#16181F"
    CARD = "#1C1E27"
    CARD_HOVER = "#232632"
    INPUT = "#12131A"
    BORDER = "#262935"
    BORDER_STRONG = "#353948"
    TEXT = "#E8E9EF"
    TEXT_2 = "#A0A6B5"
    TEXT_3 = "#666C7C"
    ACCENT = "#7C6CFF"
    ACCENT_2 = "#A855F7"
    ACCENT_SOFT = "#B4AAFF"
    SUCCESS = "#22C55E"
    WARNING = "#F5A524"
    DANGER = "#F0506E"
    INFO = "#38BDF8"


FONT_FAMILY = "Segoe UI"


@dataclass(frozen=True)
class ToolMeta:
    key: str
    title: str
    description: str
    icon: str
    color: str
    group: str


TOOLS: List[ToolMeta] = [
    ToolMeta("merge", "Unir PDFs", "Combina varios PDF en uno solo, en el orden que elijas.", "merge", "#7C6CFF", "ORGANIZAR"),
    ToolMeta("split", "Dividir PDF", "Extrae páginas concretas o separa cada página en su propio archivo.", "scissors", "#14B8A6", "ORGANIZAR"),
    ToolMeta("organize", "Organizar páginas", "Reordena, gira y elimina páginas con vista previa en miniatura.", "grid", "#F59E0B", "ORGANIZAR"),
    ToolMeta("compress", "Comprimir PDF", "Reduce el peso del archivo manteniendo intacto su contenido.", "shrink", "#10B981", "OPTIMIZAR"),
    ToolMeta("images", "Imágenes a PDF", "Convierte fotos JPG, PNG, WEBP o BMP en un documento PDF.", "image", "#EC4899", "CONVERTIR"),
    ToolMeta("word", "Word a PDF", "Convierte uno o varios documentos de Word a PDF por lotes.", "filetext", "#3B82F6", "CONVERTIR"),
    ToolMeta("security", "Proteger / Desbloquear", "Añade o quita la contraseña de un PDF con cifrado AES.", "shield", "#F0506E", "SEGURIDAD"),
]

TOOLS_BY_KEY = {t.key: t for t in TOOLS}


# -----------------------------------------------------------------------------
# UTILIDADES DE COLOR
# -----------------------------------------------------------------------------
def qcolor(value: str, alpha: int = 255) -> QColor:
    c = QColor(value)
    c.setAlpha(max(0, min(255, int(alpha))))
    return c


def mix(c1: str, c2: str, t: float) -> QColor:
    """Interpola linealmente entre dos colores hex (t en 0..1)."""
    a, b = QColor(c1), QColor(c2)
    t = max(0.0, min(1.0, float(t)))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def rgba(value: str, alpha: float) -> str:
    """Devuelve 'rgba(r,g,b,a)' para usar en QSS."""
    c = QColor(value)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha:.3f})"


def repolish(widget: QWidget) -> None:
    """Fuerza a Qt a reaplicar el QSS tras cambiar una propiedad dinámica."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def font(size: float = 10, weight: int = 400) -> QFont:
    f = QFont(FONT_FAMILY)
    f.setPointSizeF(size)
    f.setWeight(QFont.Weight(weight))
    return f


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.2f} MB"


# -----------------------------------------------------------------------------
# HOJA DE ESTILOS GLOBAL
# -----------------------------------------------------------------------------
def build_stylesheet() -> str:
    return f"""
* {{
    font-family: "{FONT_FAMILY}";
    color: {C.TEXT};
    outline: none;
}}
QMainWindow, QWidget#root, QWidget#view {{
    background: {C.BG};
}}
QLabel {{ background: transparent; }}
QLabel[role="title"] {{ font-size: 22px; font-weight: 600; }}
QLabel[role="hero"] {{ font-size: 30px; font-weight: 700; }}
QLabel[role="subtitle"] {{ color: {C.TEXT_2}; font-size: 13px; }}
QLabel[role="section"] {{ color: {C.TEXT_3}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QLabel[role="h2"] {{ font-size: 16px; font-weight: 600; }}
QLabel[role="muted"] {{ color: {C.TEXT_2}; font-size: 13px; }}
QLabel[role="hint"] {{ color: {C.TEXT_3}; font-size: 12px; }}
QLabel[role="field"] {{ color: {C.TEXT_2}; font-size: 12px; font-weight: 600; }}
QLabel[state="ok"] {{ color: {C.SUCCESS}; }}
QLabel[state="error"] {{ color: {C.DANGER}; }}
QLabel[state="warning"] {{ color: {C.WARNING}; }}

QFrame#sidebar {{
    background: {C.SIDEBAR};
    border-right: 1px solid {C.BORDER};
}}
QFrame#panel {{
    background: {C.SURFACE};
    border: 1px solid {C.BORDER};
    border-radius: 16px;
}}
QFrame#card {{
    background: {C.CARD};
    border: 1px solid {C.BORDER};
    border-radius: 14px;
}}
QFrame#note {{
    background: {rgba(C.INFO, 0.08)};
    border: 1px solid {rgba(C.INFO, 0.25)};
    border-radius: 12px;
}}
QFrame#warnnote {{
    background: {rgba(C.WARNING, 0.08)};
    border: 1px solid {rgba(C.WARNING, 0.28)};
    border-radius: 12px;
}}
QFrame#actionbar {{
    background: {C.SURFACE};
    border-top: 1px solid {C.BORDER};
}}

QPushButton {{
    background: {C.CARD};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 600;
    color: {C.TEXT};
}}
QPushButton:hover {{ background: {C.CARD_HOVER}; border-color: {C.BORDER_STRONG}; }}
QPushButton:pressed {{ background: #2B2E3B; }}
QPushButton:disabled {{ color: {C.TEXT_3}; background: #181A21; border-color: #20222B; }}

QPushButton#primary {{
    border: none;
    color: white;
    padding: 12px 28px;
    font-size: 14px;
    border-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C.ACCENT}, stop:1 {C.ACCENT_2});
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8D7FFF, stop:1 #B56CFA);
}}
QPushButton#primary:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6B5BEF, stop:1 #9645E6);
}}
QPushButton#primary:disabled {{ background: #262833; color: #6B7180; }}

QPushButton#accent {{
    border: none; color: white;
    background: {C.ACCENT};
    padding: 10px 20px;
}}
QPushButton#accent:hover {{ background: #8D7FFF; }}

QPushButton#ghost {{
    background: transparent;
    border: 1px solid transparent;
    color: {C.TEXT_2};
}}
QPushButton#ghost:hover {{ background: rgba(255,255,255,0.06); color: {C.TEXT}; }}

QPushButton#danger {{
    background: {rgba(C.DANGER, 0.10)};
    border: 1px solid {rgba(C.DANGER, 0.30)};
    color: #FF8FA3;
}}
QPushButton#danger:hover {{ background: {rgba(C.DANGER, 0.20)}; }}

QPushButton#chip {{
    background: {C.INPUT};
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 12px;
    color: {C.TEXT_2};
}}
QPushButton#chip:hover {{ border-color: {C.ACCENT}; color: {C.TEXT}; }}

QPushButton#link {{
    background: transparent;
    border: none;
    padding: 2px 2px;
    color: {C.ACCENT_SOFT};
    font-size: 12px;
}}
QPushButton#link:hover {{ color: white; text-decoration: underline; }}

QPushButton#iconbtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QPushButton#iconbtn:hover {{ background: rgba(255,255,255,0.07); }}

QLineEdit {{
    background: {C.INPUT};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 13px;
    selection-background-color: {C.ACCENT};
}}
QLineEdit:hover {{ border-color: {C.BORDER_STRONG}; }}
QLineEdit:focus {{ border: 1px solid {C.ACCENT}; }}
QLineEdit:disabled {{ color: {C.TEXT_3}; }}
QLineEdit[state="error"] {{ border: 1px solid {C.DANGER}; }}
QLineEdit[state="ok"] {{ border: 1px solid {rgba(C.SUCCESS, 0.7)}; }}

QScrollArea, QScrollArea > QWidget > QWidget#scrollContent {{
    background: transparent;
    border: none;
}}
QListView, QListWidget {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #2C2F3D; border-radius: 3px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: #3D4154; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: #2C2F3D; border-radius: 3px; min-width: 36px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QToolTip {{
    background: #22242E;
    color: {C.TEXT};
    border: 1px solid {C.BORDER_STRONG};
    padding: 6px 9px;
    border-radius: 6px;
    font-size: 12px;
}}
QMenu {{
    background: #1A1C24;
    border: 1px solid {C.BORDER_STRONG};
    border-radius: 12px;
    padding: 6px;
}}
QMenu::item {{
    padding: 9px 22px 9px 12px;
    border-radius: 8px;
    font-size: 13px;
}}
QMenu::item:selected {{ background: {rgba(C.ACCENT, 0.20)}; }}
QMenu::item:disabled {{ color: {C.TEXT_3}; }}
QMenu::separator {{ height: 1px; background: {C.BORDER}; margin: 5px 8px; }}
QMenu::icon {{ padding-left: 10px; }}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(C.BG))
    pal.setColor(QPalette.WindowText, QColor(C.TEXT))
    pal.setColor(QPalette.Base, QColor(C.INPUT))
    pal.setColor(QPalette.AlternateBase, QColor(C.SURFACE))
    pal.setColor(QPalette.Text, QColor(C.TEXT))
    pal.setColor(QPalette.Button, QColor(C.CARD))
    pal.setColor(QPalette.ButtonText, QColor(C.TEXT))
    pal.setColor(QPalette.Highlight, QColor(C.ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    pal.setColor(QPalette.ToolTipBase, QColor("#22242E"))
    pal.setColor(QPalette.ToolTipText, QColor(C.TEXT))
    pal.setColor(QPalette.PlaceholderText, QColor(C.TEXT_3))
    pal.setColor(QPalette.Link, QColor(C.ACCENT_SOFT))
    app.setPalette(pal)

    app.setFont(font(10))
    app.setStyleSheet(build_stylesheet())
