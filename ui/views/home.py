"""
ui/views/home.py
Pantalla de inicio estilo dashboard.
Ofrece acceso visual a las 7 herramientas con tarjetas interactivas,
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
from ui.theme import C, TOOLS, ToolMeta, font, format_bytes, rgba


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
        icon_box = QFrame()
        icon_box.setFixedSize(50, 50)
        icon_box.setStyleSheet(f"""
            background: {rgba(tool.color, 0.16)};
            border: 1px solid {rgba(tool.color, 0.35)};
            border-radius: 14px;
        """)
        ib_layout = QVBoxLayout(icon_box)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        ib_layout.setAlignment(Qt.AlignCenter)
        ic_lbl = QLabel()
        ic_lbl.setPixmap(pixmap(tool.icon, 26, tool.color))
        ic_lbl.setAlignment(Qt.AlignCenter)
        ib_layout.addWidget(ic_lbl)
        layout.addWidget(icon_box)

        # Textos
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.setAlignment(Qt.AlignVCenter)

        title_lbl = QLabel(tool.title)
        title_lbl.setFont(font(11.5, 600))
        title_lbl.setStyleSheet("color: white;")
        text_col.addWidget(title_lbl)

        desc_lbl = QLabel(tool.description)
        desc_lbl.setFont(font(9, 400))
        desc_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        desc_lbl.setWordWrap(True)
        text_col.addWidget(desc_lbl)

        layout.addLayout(text_col, 1)

        self.setStyleSheet(f"""
            QFrame#homeToolCard {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 14px;
            }}
            QFrame#homeToolCard:hover {{
                background-color: {C.CARD_HOVER};
                border: 1px solid {rgba(tool.color, 0.6)};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class RecentItemCard(QFrame):
    """Tarjeta individual para un documento reciente."""

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
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 18, C.ACCENT))
        layout.addWidget(icon_lbl)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        info_col.setAlignment(Qt.AlignVCenter)

        name_lbl = QLabel(data.get("name", os.path.basename(file_path)))
        name_lbl.setFont(font(9.5, 600))
        name_lbl.setStyleSheet("color: white;")
        info_col.addWidget(name_lbl)

        sub_parts = [data.get("tool", "PDF"), format_bytes(data.get("size", 0)), data.get("date", "")]
        sub_lbl = QLabel("  •  ".join(p for p in sub_parts if p))
        sub_lbl.setFont(font(8.5, 400))
        sub_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        info_col.addWidget(sub_lbl)
        layout.addLayout(info_col, 1)

        # Botones rápidos
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

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ background: {C.BG}; border: none; }}")

        container = QWidget()
        container.setObjectName("scrollContent")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(32, 28, 32, 28)
        c_layout.setSpacing(24)

        # 1. Cabecera de bienvenida
        header_col = QVBoxLayout()
        header_col.setSpacing(6)

        title_lbl = QLabel("¿Qué quieres hacer hoy?")
        title_lbl.setFont(font(20, 700))
        title_lbl.setStyleSheet("color: white;")
        header_col.addWidget(title_lbl)

        sub_lbl = QLabel("Selecciona una herramienta o suelta cualquier archivo aquí para comenzar de inmediato.")
        sub_lbl.setFont(font(10, 400))
        sub_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        header_col.addWidget(sub_lbl)

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

        # Agrupar herramientas en 2 columnas
        for idx, tool in enumerate(TOOLS):
            card = ToolCard(tool, self)
            card.clicked.connect(lambda k=tool.key: self.tool_requested.emit(k, []))
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
        scroll.setWidget(container)
        root_layout.addWidget(scroll)

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

        # Mostrar hasta 4 recientes en el inicio
        for item in recents[:4]:
            self.recent_layout.addWidget(RecentItemCard(item, self.recent_box))

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
