"""
ui/components/sidebar.py
Menú lateral de navegación con diseño moderno, categorización clara por objetivo,
iconos vectoriales temáticos y píldoras de selección activa.
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)

from ui.icons import icon, logo_pixmap, pixmap
from ui.theme import C, TOOLS, ToolMeta, font, rgba


class NavButton(QPushButton):
    """Botón de navegación estilizado con icono temático e indicador activo."""

    def __init__(self, key: str, label_text: str, icon_name: str, accent_color: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label_text
        self.icon_name = icon_name
        self.accent_color = accent_color
        self._active = False

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setCheckable(False)

        # Contenido visual
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(20, 20)
        layout.addWidget(self.icon_lbl)

        self.text_lbl = QLabel(label_text)
        self.text_lbl.setFont(font(10, 500))
        layout.addWidget(self.text_lbl, 1)

        self.pill = QFrame()
        self.pill.setFixedSize(4, 20)
        self.pill.setStyleSheet(f"background: {accent_color}; border-radius: 2px;")
        self.pill.hide()
        layout.addWidget(self.pill)

        self.update_state()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self.update_state()

    def update_state(self):
        if self._active:
            self.icon_lbl.setPixmap(pixmap(self.icon_name, 18, self.accent_color))
            self.text_lbl.setStyleSheet(f"color: white; font-weight: 600;")
            self.pill.show()
            self.setStyleSheet(f"""
                NavButton {{
                    background: {rgba(self.accent_color, 0.16)};
                    border: 1px solid {rgba(self.accent_color, 0.35)};
                    border-radius: 10px;
                }}
            """)
        else:
            self.icon_lbl.setPixmap(pixmap(self.icon_name, 18, C.TEXT_2))
            self.text_lbl.setStyleSheet(f"color: {C.TEXT_2}; font-weight: 500;")
            self.pill.hide()
            self.setStyleSheet(f"""
                NavButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 10px;
                }}
                NavButton:hover {{
                    background: {rgba(C.CARD_HOVER, 0.8)};
                    border: 1px solid {C.BORDER};
                }}
            """)


class Sidebar(QFrame):
    navigate_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 16, 12, 16)
        main_layout.setSpacing(12)

        # 1. Cabecera con Logotipo
        header = QHBoxLayout()
        header.setSpacing(10)
        header.setContentsMargins(4, 0, 4, 10)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(logo_pixmap(32))
        logo_lbl.setFixedSize(32, 32)
        header.addWidget(logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        app_title = QLabel("PDF Master")
        app_title.setFont(font(12, 700))
        app_title.setStyleSheet("color: white;")
        title_col.addWidget(app_title)

        app_sub = QLabel("Suite Local Privada")
        app_sub.setFont(font(8.5, 400))
        app_sub.setStyleSheet(f"color: {C.TEXT_3};")
        title_col.addWidget(app_sub)

        header.addLayout(title_col, 1)
        main_layout.addLayout(header)

        # 2. Área de scroll para botones de navegación
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container.setObjectName("scrollContent")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(4)

        self.buttons: Dict[str, NavButton] = {}

        # Botón Inicio
        self.btn_home = NavButton("home", "Inicio", "home", C.ACCENT, self)
        self.btn_home.clicked.connect(lambda: self.navigate_requested.emit("home"))
        c_layout.addWidget(self.btn_home)
        self.buttons["home"] = self.btn_home

        # Secciones agrupadas
        groups = [
            ("ORGANIZAR", [t for t in TOOLS if t.group == "ORGANIZAR"]),
            ("OPTIMIZAR", [t for t in TOOLS if t.group == "OPTIMIZAR"]),
            ("CONVERTIR", [t for t in TOOLS if t.group == "CONVERTIR"]),
            ("SEGURIDAD", [t for t in TOOLS if t.group == "SEGURIDAD"]),
        ]

        for group_title, tools_list in groups:
            # Separador / etiqueta de grupo
            lbl_group = QLabel(group_title)
            lbl_group.setProperty("role", "section")
            lbl_group.setFont(font(8.5, 700))
            lbl_group.setContentsMargins(8, 14, 0, 4)
            c_layout.addWidget(lbl_group)

            for t in tools_list:
                btn = NavButton(t.key, t.title, t.icon, t.color, self)
                btn.clicked.connect(lambda checked=False, k=t.key: self.navigate_requested.emit(k))
                c_layout.addWidget(btn)
                self.buttons[t.key] = btn

        c_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 3. Pie del Sidebar
        footer = QFrame()
        footer.setStyleSheet(f"border-top: 1px solid {C.BORDER}; padding-top: 8px;")
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(4, 6, 4, 0)
        f_layout.setSpacing(2)

        badge_lbl = QLabel("100% Offline y Seguro")
        badge_lbl.setFont(font(8.5, 600))
        badge_lbl.setStyleSheet(f"color: {C.SUCCESS};")
        f_layout.addWidget(badge_lbl)

        info_lbl = QLabel("Tus archivos nunca salen de tu PC")
        info_lbl.setFont(font(8, 400))
        info_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        f_layout.addWidget(info_lbl)

        main_layout.addWidget(footer)

    def set_current(self, key: str):
        """Marca como activa la herramienta seleccionada y desmarca las demás."""
        for k, btn in self.buttons.items():
            btn.set_active(k == key)
