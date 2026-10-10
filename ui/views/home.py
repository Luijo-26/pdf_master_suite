"""
ui/views/home.py
Pantalla de inicio estilo dashboard.
Ofrece acceso visual a las herramientas con tarjetas interactivas,
zona inteligente de soltar archivo que detecta el formato y redirige,
y panel de documentos recientes procesados localmente.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget
)

from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import get_recents, open_file, open_folder
from ui.theme import (
    C, TOOLS, ToolMeta, add_theme_listener, font, format_bytes,
    remove_theme_listener, rgba
)


class ToolCard(QFrame):
    """Tarjeta interactiva para una herramienta."""
    clicked = Signal()

    def __init__(self, tool: ToolMeta, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.tool = tool
        self.setObjectName("homeToolCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(115)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        # Icono con fondo temático suave
        self.icon_box = QFrame()
        self.icon_box.setFixedSize(50, 50)
        self._update_icon_box_style()

        ib_layout = QVBoxLayout(self.icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignCenter)
        self.ic_lbl = QLabel()
        self.ic_lbl.setPixmap(pixmap(tool.icon, 26, tool.color))
        self.ic_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(self.ic_lbl)
        layout.addWidget(self.icon_box)

        # Textos
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setAlignment(Qt.AlignVCenter)

        self.title_lbl = QLabel(tool.title)
        self.title_lbl.setFont(font(11.5, 600))
        self.title_lbl.setStyleSheet(f"color: {C.TEXT};")
        text_col.addWidget(self.title_lbl)

        self.desc_lbl = QLabel(tool.description)
        self.desc_lbl.setFont(font(9, 400))
        self.desc_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self.desc_lbl.setWordWrap(True)
        text_col.addWidget(self.desc_lbl)

        layout.addLayout(text_col, 1)
        self.update_card_style()

    def _update_icon_box_style(self):
        self.icon_box.setStyleSheet(f"""
            background: {rgba(self.tool.color, 0.16)};
            border: 1px solid {rgba(self.tool.color, 0.35)};
            border-radius: 14px;
        """)

    def update_card_style(self):
        self.title_lbl.setStyleSheet(f"color: {C.TEXT};")
        self.desc_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self._update_icon_box_style()
        self.setStyleSheet(f"""
            QFrame#homeToolCard {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 14px;
            }}
            QFrame#homeToolCard:hover {{
                background-color: {C.CARD_HOVER};
                border: 1px solid {rgba(self.tool.color, 0.6)};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class RecentItemCard(QFrame):
    """Tarjeta individual para un documento reciente."""
    preview_requested = Signal(str)

    def __init__(self, data: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.data = data
        file_path = data.get("path", "")
        self.setObjectName("recentCard")
        self.setFixedHeight(54)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(12)

        # Icono
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(pixmap("file", 18, C.ACCENT))
        layout.addWidget(self.icon_lbl)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        info_col.setAlignment(Qt.AlignVCenter)

        self.name_lbl = QLabel(data.get("name", os.path.basename(file_path)))
        self.name_lbl.setFont(font(9.5, 600))
        self.name_lbl.setStyleSheet(f"color: {C.TEXT};")
        info_col.addWidget(self.name_lbl)

        sub_parts = [data.get("tool", "PDF"), format_bytes(data.get("size", 0)), data.get("date", "")]
        self.sub_lbl = QLabel("  •  ".join(p for p in sub_parts if p))
        self.sub_lbl.setFont(font(8.5, 400))
        self.sub_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        info_col.addWidget(self.sub_lbl)
        layout.addLayout(info_col, 1)

        # Botones rápidos
        if file_path.lower().endswith(".pdf"):
            btn_prev = QPushButton("Ver")
            btn_prev.setObjectName("chip")
            btn_prev.setIcon(pixmap("eye", 12, C.ACCENT))
            btn_prev.setStyleSheet(f"color: {C.ACCENT}; font-weight: 600;")
            btn_prev.setCursor(Qt.PointingHandCursor)
            btn_prev.clicked.connect(lambda: self.preview_requested.emit(file_path))
            layout.addWidget(btn_prev)

        btn_open = QPushButton("Abrir")
        btn_open.setObjectName("chip")
        btn_open.setIcon(pixmap("external", 12, C.ACCENT_SOFT))
        btn_open.setCursor(Qt.PointingHandCursor)
        btn_open.clicked.connect(lambda: open_file(file_path))
        layout.addWidget(btn_open)

        btn_folder = QPushButton("Carpeta")
        btn_folder.setObjectName("chip")
        btn_folder.setIcon(pixmap("folder", 12, C.TEXT_2))
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.clicked.connect(lambda: open_folder(file_path))
        layout.addWidget(btn_folder)

        self.update_style()

    def update_style(self):
        self.icon_lbl.setPixmap(pixmap("file", 18, C.ACCENT))
        self.name_lbl.setStyleSheet(f"color: {C.TEXT};")
        self.sub_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        self.setStyleSheet(f"""
            QFrame#recentCard {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 10px;
            }}
            QFrame#recentCard:hover {{
                background-color: {C.CARD_HOVER};
                border-color: {C.BORDER_STRONG};
            }}
        """)


class HomeView(QWidget):
    tool_requested = Signal(str, list)  # tool_key, initial_files
    preview_requested = Signal(str)     # file_path para abrir en el visor

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cards: List[ToolCard] = []
        self._init_ui()
        add_theme_listener(self._on_theme_changed)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ background: {C.BG}; border: none; }}")

        container = QWidget()
        container.setObjectName("scrollContent")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(32, 28, 32, 28)
        c_layout.setSpacing(24)

        # 1. Cabecera de bienvenida
        header_col = QVBoxLayout()
        header_col.setSpacing(6)

        self.welcome_title = QLabel("¿Qué quieres hacer hoy?")
        self.welcome_title.setFont(font(20, 700))
        self.welcome_title.setStyleSheet(f"color: {C.TEXT};")
        header_col.addWidget(self.welcome_title)

        self.welcome_sub = QLabel("Selecciona una herramienta o suelta cualquier archivo aquí para comenzar de inmediato.")
        self.welcome_sub.setFont(font(10, 400))
        self.welcome_sub.setStyleSheet(f"color: {C.TEXT_2};")
        header_col.addWidget(self.welcome_sub)

        c_layout.addLayout(header_col)

        # 2. Zona de arrastre universal
        self.drop_zone = DropZone(
            title="Suelta cualquier archivo aquí",
            subtitle="Detectaremos si es PDF, imagen o Word para abrir la herramienta adecuada",
            button_text="Examinar archivos...",
            allow_multiple=True,
            compact=True,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        c_layout.addWidget(self.drop_zone)

        # 3. Cuadrícula de herramientas
        lbl_tools = QLabel("HERRAMIENTAS DISPONIBLES")
        lbl_tools.setProperty("role", "section")
        lbl_tools.setFont(font(9, 700))
        c_layout.addWidget(lbl_tools)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.cards = []
        for idx, tool in enumerate(TOOLS):
            card = ToolCard(tool, self)
            card.clicked.connect(lambda k=tool.key: self.tool_requested.emit(k, []))
            self.cards.append(card)
            r = idx // 2
            c = idx % 2
            grid.addWidget(card, r, c)

        c_layout.addLayout(grid)

        # 4. Sección de documentos recientes
        self.recent_box = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_box)
        self.recent_layout.setContentsMargins(0, 8, 0, 0)
        self.recent_layout.setSpacing(10)

        c_layout.addWidget(self.recent_box)

        c_layout.addStretch()
        self.scroll.setWidget(container)
        root_layout.addWidget(self.scroll)

        self.refresh_recents()

    def refresh_recents(self):
        """Actualiza la lista de archivos recientes en la pantalla de inicio."""
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        recents = get_recents()
        if not recents:
            self.recent_box.hide()
            return

        self.recent_box.show()
        lbl_recent = QLabel("DOCUMENTOS RECIENTES")
        lbl_recent.setProperty("role", "section")
        lbl_recent.setFont(font(9, 700))
        self.recent_layout.addWidget(lbl_recent)

        for item in recents[:4]:
            card = RecentItemCard(item, self.recent_box)
            card.preview_requested.connect(self.preview_requested.emit)
            self.recent_layout.addWidget(card)

    def _on_theme_changed(self):
        self.welcome_title.setStyleSheet(f"color: {C.TEXT};")
        self.welcome_sub.setStyleSheet(f"color: {C.TEXT_2};")
        self.scroll.setStyleSheet(f"QScrollArea {{ background: {C.BG}; border: none; }}")
        for card in self.cards:
            card.update_card_style()
        self.refresh_recents()

    def _on_files_dropped(self, files: List[str]):
        """Detecta inteligentemente la herramienta según el tipo de archivo."""
        if not files:
            return

        first = files[0].lower()
        if first.endswith((".docx", ".doc")):
            self.tool_requested.emit("word", files)
        elif first.endswith((".xlsx", ".xls")):
            self.tool_requested.emit("excel", files)
        elif first.endswith((".pptx", ".ppt")):
            self.tool_requested.emit("powerpoint", files)
        elif first.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
            self.tool_requested.emit("images", files)
        elif first.endswith(".pdf"):
            if len(files) > 1:
                self.tool_requested.emit("merge", files)
            else:
                self.tool_requested.emit("organize", files)
        else:
            self.tool_requested.emit("merge", files)

    def closeEvent(self, event):
        remove_theme_listener(self._on_theme_changed)
        super().closeEvent(event)
