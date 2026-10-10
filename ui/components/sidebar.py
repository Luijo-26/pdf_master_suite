"""
ui/components/sidebar.py
Menú lateral de navegación con diseño moderno, categorización clara por objetivo,
iconos vectoriales temáticos y píldoras de selección activa.
"""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)

from core.version import APP_VERSION
from ui.icons import logo_pixmap, pixmap
from ui.theme import (
    C, TOOLS, ToolMeta, add_theme_listener, font, remove_theme_listener, rgba
)


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
        self.pill.setStyleSheet(f"background: {self.accent_color}; border-radius: 2px;")
        if self._active:
            self.icon_lbl.setPixmap(pixmap(self.icon_name, 18, self.accent_color))
            self.text_lbl.setStyleSheet(f"color: {C.TEXT}; font-weight: 700;")
            self.pill.show()
            self.setStyleSheet(f"""
                NavButton {{
                    background: {rgba(self.accent_color, 0.16)};
                    border: 1px solid {rgba(self.accent_color, 0.40)};
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
    check_updates_requested = Signal()

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

        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(logo_pixmap(32))
        self.logo_lbl.setFixedSize(32, 32)
        header.addWidget(self.logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        self.app_title = QLabel("PDF Master")
        self.app_title.setFont(font(12, 700))
        self.app_title.setStyleSheet(f"color: {C.TEXT};")
        title_col.addWidget(self.app_title)

        self.app_sub = QLabel("Suite Local Privada")
        self.app_sub.setFont(font(8.5, 400))
        self.app_sub.setStyleSheet(f"color: {C.TEXT_3};")
        title_col.addWidget(self.app_sub)

        header.addLayout(title_col, 1)
        main_layout.addLayout(header)

        # 2. Caja de búsqueda rápida de herramientas
        self.search_box = QFrame()
        self._update_search_box_style()

        s_layout = QHBoxLayout(self.search_box)
        s_layout.setContentsMargins(8, 4, 8, 4)
        s_layout.setSpacing(6)

        self.s_icon = QLabel()
        self.s_icon.setPixmap(pixmap("search", 13, C.TEXT_3))
        s_layout.addWidget(self.s_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar herramienta...")
        self.search_input.setFont(font(9, 400))
        self.search_input.setStyleSheet(f"border: none; background: transparent; color: {C.TEXT};")
        self.search_input.textChanged.connect(self._on_search_changed)
        s_layout.addWidget(self.search_input, 1)

        main_layout.addWidget(self.search_box)

        # 3. Área de scroll para botones de navegación
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        container.setObjectName("scrollContent")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(3)

        self.buttons: Dict[str, NavButton] = {}
        self.group_items: Dict[str, Tuple[QLabel, List[Tuple[NavButton, ToolMeta]]]] = {}

        # Botón Inicio
        self.btn_home = NavButton("home", "Inicio", "home", C.ACCENT, self)
        self.btn_home.clicked.connect(lambda: self.navigate_requested.emit("home"))
        c_layout.addWidget(self.btn_home)
        self.buttons["home"] = self.btn_home

        # Botón Visor de PDF
        self.btn_viewer = NavButton("viewer", "Visor de PDF", "eye", "#38BDF8", self)
        self.btn_viewer.clicked.connect(lambda: self.navigate_requested.emit("viewer"))
        c_layout.addWidget(self.btn_viewer)
        self.buttons["viewer"] = self.btn_viewer

        # Secciones agrupadas
        category_order = [
            "ORGANIZAR",
            "OPTIMIZAR",
            "EDITAR",
            "CONVERTIR A PDF",
            "CONVERTIR DESDE PDF",
            "SEGURIDAD",
        ]

        for cat in category_order:
            tools_in_cat = [t for t in TOOLS if t.group == cat]
            if not tools_in_cat:
                continue

            lbl_group = QLabel(cat)
            lbl_group.setProperty("role", "section")
            lbl_group.setFont(font(8.5, 700))
            lbl_group.setStyleSheet(f"color: {C.TEXT_3}; padding: 10px 8px 3px 8px;")
            c_layout.addWidget(lbl_group)

            cat_buttons: List[Tuple[NavButton, ToolMeta]] = []
            for t in tools_in_cat:
                btn = NavButton(t.key, t.title, t.icon, t.color, self)
                btn.clicked.connect(lambda checked=False, k=t.key: self.navigate_requested.emit(k))
                c_layout.addWidget(btn)
                self.buttons[t.key] = btn
                cat_buttons.append((btn, t))

            self.group_items[cat] = (lbl_group, cat_buttons)

        c_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 4. Botón de Configuración (anclado antes del pie)
        self.btn_settings = NavButton("settings", "Configuración", "settings", C.ACCENT, self)
        self.btn_settings.clicked.connect(lambda: self.navigate_requested.emit("settings"))
        main_layout.addWidget(self.btn_settings)
        self.buttons["settings"] = self.btn_settings

        # 5. Pie del Sidebar
        self.footer = QFrame()
        self._update_footer_style()
        f_layout = QVBoxLayout(self.footer)
        f_layout.setContentsMargins(4, 6, 4, 0)
        f_layout.setSpacing(2)

        self.badge_lbl = QLabel("100% Offline y Seguro")
        self.badge_lbl.setFont(font(8.5, 600))
        self.badge_lbl.setStyleSheet(f"color: {C.SUCCESS};")
        f_layout.addWidget(self.badge_lbl)

        self.info_lbl = QLabel("Tus archivos nunca salen de tu PC")
        self.info_lbl.setFont(font(8, 400))
        self.info_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        f_layout.addWidget(self.info_lbl)

        # Fila de versión y comprobación de actualización
        ver_row = QHBoxLayout()
        ver_row.setContentsMargins(0, 4, 0, 0)
        ver_row.setSpacing(6)

        self.v_badge = QLabel(f"v{APP_VERSION}")
        self.v_badge.setFont(font(8, 600))
        self.v_badge.setStyleSheet(f"color: {C.TEXT_3};")
        ver_row.addWidget(self.v_badge)

        self.btn_update_check = QPushButton("Buscar cambios")
        self.btn_update_check.setObjectName("link")
        self.btn_update_check.setFont(font(8, 500))
        self.btn_update_check.setCursor(Qt.PointingHandCursor)
        self.btn_update_check.setIcon(QIcon(pixmap("refresh", 11, C.TEXT_3)))
        self.btn_update_check.setToolTip("Comprobar si existe una versión más reciente")
        self.btn_update_check.clicked.connect(self.check_updates_requested.emit)
        ver_row.addWidget(self.btn_update_check, 0, Qt.AlignRight)

        f_layout.addLayout(ver_row)
        main_layout.addWidget(self.footer)

        # Escuchar cambios dinámicos de tema
        add_theme_listener(self._on_theme_changed)

    def _update_search_box_style(self):
        self.search_box.setStyleSheet(f"""
            QFrame {{
                background: {C.INPUT};
                border: 1px solid {C.BORDER};
                border-radius: 8px;
            }}
            QFrame:focus-within {{
                border: 1px solid {C.ACCENT};
            }}
        """)

    def _update_footer_style(self):
        self.footer.setStyleSheet(f"border-top: 1px solid {C.BORDER}; padding-top: 8px;")

    def _on_theme_changed(self):
        """Reaplica colores cuando el tema o acento cambian."""
        self.app_title.setStyleSheet(f"color: {C.TEXT};")
        self.app_sub.setStyleSheet(f"color: {C.TEXT_3};")
        self._update_search_box_style()
        self.search_input.setStyleSheet(f"border: none; background: transparent; color: {C.TEXT};")
        self.s_icon.setPixmap(pixmap("search", 13, C.TEXT_3))

        self.btn_home.accent_color = C.ACCENT
        self.btn_viewer.accent_color = C.INFO if C.IS_DARK else C.ACCENT
        self.btn_settings.accent_color = C.ACCENT

        for btn in self.buttons.values():
            btn.update_state()

        self._update_footer_style()
        self.badge_lbl.setStyleSheet(f"color: {C.SUCCESS};")
        self.info_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        self.v_badge.setStyleSheet(f"color: {C.TEXT_3};")
        self.btn_update_check.setIcon(QIcon(pixmap("refresh", 11, C.TEXT_3)))

    def set_current(self, key: str):
        """Marca como activa la herramienta seleccionada y desmarca las demás."""
        for k, btn in self.buttons.items():
            btn.set_active(k == key)

    def _on_search_changed(self, text: str):
        """Filtra en tiempo real los botones y encabezados de categoría."""
        query = text.lower().strip()

        # El botón Home solo se muestra si la búsqueda está vacía o coincide con 'inicio' / 'home'
        if "home" in self.buttons:
            self.buttons["home"].setVisible(not query or "inicio" in query or "home" in query)

        # El botón Visor se muestra si la búsqueda está vacía o coincide con visor / pdf / ver / leer
        if "viewer" in self.buttons:
            self.buttons["viewer"].setVisible(not query or "visor" in query or "pdf" in query or "ver" in query or "leer" in query)

        # El botón de Configuración solo se muestra si la búsqueda está vacía o coincide con 'config'
        if "settings" in self.buttons:
            self.buttons["settings"].setVisible(not query or "config" in query or "ajuste" in query or "tema" in query)

        for cat, (lbl_group, items) in self.group_items.items():
            visible_count = 0
            for btn, meta in items:
                match = (
                    not query or
                    query in meta.title.lower() or
                    query in meta.description.lower() or
                    query in meta.key.lower() or
                    query in cat.lower()
                )
                btn.setVisible(match)
                if match:
                    visible_count += 1
            lbl_group.setVisible(visible_count > 0)

    def closeEvent(self, event):
        remove_theme_listener(self._on_theme_changed)
        super().closeEvent(event)
