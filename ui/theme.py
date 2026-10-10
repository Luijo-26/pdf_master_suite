"""
ui/theme.py
Sistema de diseño de PDF Master Suite: paletas de color, temas dinámicos,
metadatos de herramientas, hoja de estilos global (QSS) y utilidades de color.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from core.settings import get_setting
from ui.icons import clear_icon_cache


# -----------------------------------------------------------------------------
# PALETAS DE TEMAS
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class ThemeDefinition:
    key: str
    name: str
    description: str
    is_dark: bool
    bg: str
    sidebar: str
    surface: str
    card: str
    card_hover: str
    input: str
    border: str
    border_strong: str
    text: str
    text_2: str
    text_3: str
    accent: str
    accent_2: str
    accent_soft: str
    success: str = "#22C55E"
    warning: str = "#F5A524"
    danger: str = "#F0506E"
    info: str = "#38BDF8"


THEMES: Dict[str, ThemeDefinition] = {
    "dark": ThemeDefinition(
        key="dark",
        name="Oscuro Cyber",
        description="Fondo oscuro equilibrado con alto contraste y acentos violeta.",
        is_dark=True,
        bg="#0E0F14",
        sidebar="#111218",
        surface="#16181F",
        card="#1C1E27",
        card_hover="#232632",
        input="#12131A",
        border="#262935",
        border_strong="#353948",
        text="#E8E9EF",
        text_2="#A0A6B5",
        text_3="#666C7C",
        accent="#7C6CFF",
        accent_2="#A855F7",
        accent_soft="#B4AAFF",
    ),
    "oled": ThemeDefinition(
        key="oled",
        name="Negro OLED",
        description="Negro absoluto y máximo contraste, ideal para pantallas OLED.",
        is_dark=True,
        bg="#000000",
        sidebar="#08080A",
        surface="#101014",
        card="#16161B",
        card_hover="#202026",
        input="#0D0D10",
        border="#22222A",
        border_strong="#33333F",
        text="#FFFFFF",
        text_2="#A8ACB9",
        text_3="#6B7082",
        accent="#8B5CF6",
        accent_2="#C084FC",
        accent_soft="#DDD6FE",
    ),
    "navy": ThemeDefinition(
        key="navy",
        name="Azul Espacial",
        description="Elegante paleta azul medianoche profesional y descansada.",
        is_dark=True,
        bg="#0A0F1D",
        sidebar="#0D1426",
        surface="#111A30",
        card="#17223F",
        card_hover="#1E2C52",
        input="#0F172C",
        border="#22335C",
        border_strong="#31477F",
        text="#EDF2F7",
        text_2="#94A3B8",
        text_3="#64748B",
        accent="#38BDF8",
        accent_2="#6366F1",
        accent_soft="#7DD3FC",
    ),
    "emerald": ThemeDefinition(
        key="emerald",
        name="Verde Esmeralda",
        description="Tonos verdes bosque profundos y relajantes para largas sesiones.",
        is_dark=True,
        bg="#091410",
        sidebar="#0C1B16",
        surface="#10241E",
        card="#152E27",
        card_hover="#1C3D34",
        input="#0D1E18",
        border="#20453A",
        border_strong="#2B5E4F",
        text="#ECFDF5",
        text_2="#A7F3D0",
        text_3="#6EE7B7",
        accent="#10B981",
        accent_2="#059669",
        accent_soft="#6EE7B7",
    ),
    "light": ThemeDefinition(
        key="light",
        name="Claro Nórdico",
        description="Diseño limpio, luminoso y suave en tonos claros de alta legibilidad.",
        is_dark=False,
        bg="#F4F5F8",
        sidebar="#EBEDF3",
        surface="#FFFFFF",
        card="#FFFFFF",
        card_hover="#F1F3F9",
        input="#F8FAFC",
        border="#E2E8F0",
        border_strong="#CBD5E1",
        text="#0F172A",
        text_2="#475569",
        text_3="#94A3B8",
        accent="#6366F1",
        accent_2="#8B5CF6",
        accent_soft="#4F46E5",
    ),
}

ACCENTS: Dict[str, Tuple[str, str, str, str]] = {
    # key: (primary, secondary, soft, label)
    "indigo": ("#7C6CFF", "#A855F7", "#B4AAFF", "Índigo"),
    "blue": ("#3B82F6", "#60A5FA", "#93C5FD", "Azul"),
    "emerald": ("#10B981", "#059669", "#6EE7B7", "Esmeralda"),
    "amber": ("#F59E0B", "#D97706", "#FCD34D", "Ámbar"),
    "rose": ("#F43F5E", "#E11D48", "#FDA4AF", "Rosa"),
}


# -----------------------------------------------------------------------------
# PALETA ACTIVA (Clase C con resolución dinámica de atributos)
# -----------------------------------------------------------------------------
class C:
    IS_DARK: bool = True
    BG: str = "#0E0F14"
    SIDEBAR: str = "#111218"
    SURFACE: str = "#16181F"
    CARD: str = "#1C1E27"
    CARD_HOVER: str = "#232632"
    INPUT: str = "#12131A"
    BORDER: str = "#262935"
    BORDER_STRONG: str = "#353948"
    TEXT: str = "#E8E9EF"
    TEXT_2: str = "#A0A6B5"
    TEXT_3: str = "#666C7C"
    ACCENT: str = "#7C6CFF"
    ACCENT_2: str = "#A855F7"
    ACCENT_SOFT: str = "#B4AAFF"
    SUCCESS: str = "#22C55E"
    WARNING: str = "#F5A524"
    DANGER: str = "#F0506E"
    INFO: str = "#38BDF8"


CURRENT_THEME_KEY: str = "dark"
CURRENT_ACCENT_KEY: str = "indigo"
_theme_listeners: List[Callable[[], None]] = []

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
    # ORGANIZAR
    ToolMeta("merge", "Unir PDFs", "Combina varios PDF en uno solo, en el orden que elijas.", "merge", "#7C6CFF", "ORGANIZAR"),
    ToolMeta("split", "Dividir PDF", "Extrae páginas concretas o separa cada página en su propio archivo.", "scissors", "#14B8A6", "ORGANIZAR"),
    ToolMeta("organize", "Organizar páginas", "Reordena, gira y elimina páginas con vista previa en miniatura.", "grid", "#F59E0B", "ORGANIZAR"),
    ToolMeta("rotate_bulk", "Rotar en bloque", "Gira todas las páginas, solo pares o solo impares a 90° o 180°.", "rotate_bulk", "#8B5CF6", "ORGANIZAR"),
    ToolMeta("crop", "Recortar PDF", "Ajusta y recorta los márgenes de página de tu documento.", "crop", "#EAB308", "ORGANIZAR"),

    # OPTIMIZAR
    ToolMeta("compress", "Comprimir PDF", "Reduce el peso del archivo manteniendo intacto su contenido.", "shrink", "#10B981", "OPTIMIZAR"),

    # EDITAR & ESTILO
    ToolMeta("watermark", "Marca de agua", "Inserta texto personalizado o una imagen sobre las páginas del PDF.", "stamp", "#F43F5E", "EDITAR"),
    ToolMeta("page_numbers", "Numerar páginas", "Añade números de página con ubicación, tipografía y formato a medida.", "hash", "#EC4899", "EDITAR"),

    # CONVERTIR A PDF
    ToolMeta("images", "Imágenes a PDF", "Convierte fotos JPG, PNG, WEBP o BMP en un documento PDF.", "image", "#EC4899", "CONVERTIR A PDF"),
    ToolMeta("word", "Word a PDF", "Convierte documentos de Word (.docx/.doc) a PDF por lotes.", "filetext", "#3B82F6", "CONVERTIR A PDF"),
    ToolMeta("excel", "Excel a PDF", "Convierte libros de cálculo de Excel (.xlsx/.xls) a formato PDF.", "excel", "#10B981", "CONVERTIR A PDF"),
    ToolMeta("powerpoint", "PowerPoint a PDF", "Convierte presentaciones de diapositivas (.pptx/.ppt) a PDF.", "powerpoint", "#F97316", "CONVERTIR A PDF"),

    # CONVERTIR DESDE PDF
    ToolMeta("pdf_to_images", "PDF a Imágenes", "Extrae las páginas del documento como imágenes JPG o PNG en alta resolución.", "pdf_image", "#06B6D4", "CONVERTIR DESDE PDF"),
    ToolMeta("pdf_to_word", "PDF a Word", "Convierte el texto y estructura de un PDF a documento Word (.docx).", "filetext", "#2563EB", "CONVERTIR DESDE PDF"),
    ToolMeta("pdf_to_text", "PDF a Texto (.txt)", "Extrae todo el texto plano legible del documento a un archivo .txt.", "text", "#64748B", "CONVERTIR DESDE PDF"),

    # SEGURIDAD
    ToolMeta("security", "Proteger / Desbloquear", "Añade o quita la contraseña de un PDF con cifrado bancario AES.", "shield", "#F0506E", "SEGURIDAD"),
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
    if widget and widget.style():
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


def add_theme_listener(listener: Callable[[], None]) -> None:
    """Registra un callback que se llamará cuando cambie el tema."""
    if listener not in _theme_listeners:
        _theme_listeners.append(listener)


def remove_theme_listener(listener: Callable[[], None]) -> None:
    if listener in _theme_listeners:
        _theme_listeners.remove(listener)


# -----------------------------------------------------------------------------
# HOJA DE ESTILOS GLOBAL (QSS)
# -----------------------------------------------------------------------------
def build_stylesheet() -> str:
    btn_pressed_bg = "#E2E8F0" if not C.IS_DARK else "#2B2E3B"
    btn_dis_bg = "#F1F5F9" if not C.IS_DARK else "#181A21"
    btn_dis_border = "#E2E8F0" if not C.IS_DARK else "#20222B"
    scrollbar_handle = "#CBD5E1" if not C.IS_DARK else "#2C2F3D"
    scrollbar_handle_hover = "#94A3B8" if not C.IS_DARK else "#3D4154"
    tooltip_bg = "#FFFFFF" if not C.IS_DARK else "#22242E"
    menu_bg = "#FFFFFF" if not C.IS_DARK else "#1A1C24"

    return f"""
* {{
    font-family: "{FONT_FAMILY}";
    color: {C.TEXT};
    outline: none;
}}
QMainWindow, QWidget#root, QWidget#view, QWidget#scrollContent {{
    background: {C.BG};
}}
QLabel {{ background: transparent; color: {C.TEXT}; }}
QLabel[role="title"] {{ font-size: 22px; font-weight: 600; color: {C.TEXT}; }}
QLabel[role="hero"] {{ font-size: 30px; font-weight: 700; color: {C.TEXT}; }}
QLabel[role="subtitle"] {{ color: {C.TEXT_2}; font-size: 13px; }}
QLabel[role="section"] {{ color: {C.TEXT_3}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QLabel[role="h2"] {{ font-size: 16px; font-weight: 600; color: {C.TEXT}; }}
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
    background: {rgba(C.INFO, 0.12 if not C.IS_DARK else 0.08)};
    border: 1px solid {rgba(C.INFO, 0.35 if not C.IS_DARK else 0.25)};
    border-radius: 12px;
}}
QFrame#warnnote {{
    background: {rgba(C.WARNING, 0.12 if not C.IS_DARK else 0.08)};
    border: 1px solid {rgba(C.WARNING, 0.35 if not C.IS_DARK else 0.28)};
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
QPushButton:pressed {{ background: {btn_pressed_bg}; }}
QPushButton:disabled {{ color: {C.TEXT_3}; background: {btn_dis_bg}; border-color: {btn_dis_border}; }}

QPushButton#primary {{
    border: none;
    color: white;
    padding: 12px 28px;
    font-size: 14px;
    border-radius: 12px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C.ACCENT}, stop:1 {C.ACCENT_2});
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C.ACCENT_2}, stop:1 {C.ACCENT});
}}
QPushButton#primary:pressed {{
    background: {C.ACCENT};
}}
QPushButton#primary:disabled {{ background: {btn_dis_bg}; color: {C.TEXT_3}; }}

QPushButton#accent {{
    border: none; color: white;
    background: {C.ACCENT};
    padding: 10px 20px;
}}
QPushButton#accent:hover {{ background: {C.ACCENT_2}; }}

QPushButton#ghost {{
    background: transparent;
    border: 1px solid transparent;
    color: {C.TEXT_2};
}}
QPushButton#ghost:hover {{ background: {rgba(C.ACCENT, 0.10)}; color: {C.TEXT}; }}

QPushButton#danger {{
    background: {rgba(C.DANGER, 0.10)};
    border: 1px solid {rgba(C.DANGER, 0.30)};
    color: {C.DANGER};
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
QPushButton#link:hover {{ color: {C.ACCENT}; text-decoration: underline; }}

QPushButton#iconbtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QPushButton#iconbtn:hover {{ background: {rgba(C.ACCENT, 0.12)}; }}

QLineEdit {{
    background: {C.INPUT};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 13px;
    color: {C.TEXT};
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
QScrollBar::handle:vertical {{ background: {scrollbar_handle}; border-radius: 3px; min-height: 36px; }}
QScrollBar::handle:vertical:hover {{ background: {scrollbar_handle_hover}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: {scrollbar_handle}; border-radius: 3px; min-width: 36px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0px; height: 0px; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}

QToolTip {{
    background: {tooltip_bg};
    color: {C.TEXT};
    border: 1px solid {C.BORDER_STRONG};
    padding: 6px 9px;
    border-radius: 6px;
    font-size: 12px;
}}
QMenu {{
    background: {menu_bg};
    color: {C.TEXT};
    border: 1px solid {C.BORDER_STRONG};
    border-radius: 12px;
    padding: 6px;
}}
QMenu::item {{
    padding: 9px 22px 9px 12px;
    border-radius: 8px;
    font-size: 13px;
    color: {C.TEXT};
}}
QMenu::item:selected {{ background: {rgba(C.ACCENT, 0.16)}; color: {C.TEXT}; }}
QMenu::item:disabled {{ color: {C.TEXT_3}; }}
QMenu::separator {{ height: 1px; background: {C.BORDER}; margin: 5px 8px; }}
QMenu::icon {{ padding-left: 10px; }}
"""


# -----------------------------------------------------------------------------
# APLICACIÓN DE TEMA
# -----------------------------------------------------------------------------
def apply_theme(
    app: Optional[QApplication] = None,
    theme_key: Optional[str] = None,
    accent_key: Optional[str] = None,
) -> None:
    """
    Aplica el tema y acento elegidos actualizando la paleta global C, la caché
    de iconos, la hoja de estilos QSS y la QPalette de la aplicación Qt.
    """
    global CURRENT_THEME_KEY, CURRENT_ACCENT_KEY

    if theme_key is None:
        theme_key = get_setting("theme", "dark")
    if accent_key is None:
        accent_key = get_setting("accent", "indigo")

    if theme_key not in THEMES:
        theme_key = "dark"
    if accent_key not in ACCENTS:
        accent_key = "indigo"

    CURRENT_THEME_KEY = theme_key
    CURRENT_ACCENT_KEY = accent_key

    th = THEMES[theme_key]
    acc_primary, acc_secondary, acc_soft, _ = ACCENTS[accent_key]

    # Actualizar atributos de C dinámicamente
    C.IS_DARK = th.is_dark
    C.BG = th.bg
    C.SIDEBAR = th.sidebar
    C.SURFACE = th.surface
    C.CARD = th.card
    C.CARD_HOVER = th.card_hover
    C.INPUT = th.input
    C.BORDER = th.border
    C.BORDER_STRONG = th.border_strong
    C.TEXT = th.text
    C.TEXT_2 = th.text_2
    C.TEXT_3 = th.text_3
    C.ACCENT = acc_primary
    C.ACCENT_2 = acc_secondary
    C.ACCENT_SOFT = acc_soft
    C.SUCCESS = th.success
    C.WARNING = th.warning
    C.DANGER = th.danger
    C.INFO = th.info

    # Limpiar caché de pixmaps para que los iconos se regeneren con los nuevos colores
    clear_icon_cache()

    if app is None:
        app = QApplication.instance()

    if app is not None:
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
        pal.setColor(QPalette.ToolTipBase, QColor("#FFFFFF" if not C.IS_DARK else "#22242E"))
        pal.setColor(QPalette.ToolTipText, QColor(C.TEXT))
        pal.setColor(QPalette.PlaceholderText, QColor(C.TEXT_3))
        pal.setColor(QPalette.Link, QColor(C.ACCENT_SOFT))
        app.setPalette(pal)

        app.setFont(font(10))
        app.setStyleSheet(build_stylesheet())

    # Notificar a componentes que necesiten repintarse
    for listener in list(_theme_listeners):
        try:
            listener()
        except Exception:
            pass
