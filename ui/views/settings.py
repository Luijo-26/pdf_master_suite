"""
ui/views/settings.py
Vista de configuración de PDF Master Suite.
Permite elegir temas visuales en tiempo real, colores de acento,
y preferencias de comportamiento del visor y de la aplicación.
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from core.settings import get_setting, reset_settings, set_setting
from core.version import APP_VERSION
from ui.icons import pixmap
from ui.theme import (
    ACCENTS, CURRENT_ACCENT_KEY, CURRENT_THEME_KEY, C, THEMES,
    ThemeDefinition, add_theme_listener, apply_theme, font, remove_theme_listener, rgba
)


class ThemeCard(QFrame):
    """Tarjeta interactiva para seleccionar un tema visual con previsualización."""
    selected = Signal(str)

    def __init__(self, theme: ThemeDefinition, is_active: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.theme = theme
        self.is_active = is_active
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(115)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Fila superior: Nombre del tema + Muestra de color (paleta)
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.name_lbl = QLabel(theme.name)
        self.name_lbl.setFont(font(11, 700))
        top_row.addWidget(self.name_lbl, 1)

        # Muestra visual de los 3 colores clave del tema
        preview_box = QHBoxLayout()
        preview_box.setSpacing(5)
        for col_hex in (theme.bg, theme.card, theme.accent):
            dot = QFrame()
            dot.setFixedSize(16, 16)
            dot.setStyleSheet(f"""
                background-color: {col_hex};
                border: 1px solid {rgba(theme.text, 0.25)};
                border-radius: 8px;
            """)
            preview_box.addWidget(dot)

        top_row.addLayout(preview_box)
        layout.addLayout(top_row)

        # Descripción
        self.desc_lbl = QLabel(theme.description)
        self.desc_lbl.setFont(font(9, 400))
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl, 1)

        self.update_style()

    def set_active(self, active: bool):
        if self.is_active != active:
            self.is_active = active
            self.update_style()

    def update_style(self):
        self.name_lbl.setStyleSheet(f"color: {C.TEXT};")
        self.desc_lbl.setStyleSheet(f"color: {C.TEXT_2};")

        if self.is_active:
            self.setStyleSheet(f"""
                ThemeCard {{
                    background-color: {rgba(C.ACCENT, 0.12)};
                    border: 2px solid {C.ACCENT};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ThemeCard {{
                    background-color: {C.CARD};
                    border: 1px solid {C.BORDER};
                    border-radius: 14px;
                }}
                ThemeCard:hover {{
                    background-color: {C.CARD_HOVER};
                    border: 1px solid {C.BORDER_STRONG};
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.theme.key)
        super().mousePressEvent(event)


class AccentChip(QPushButton):
    """Píldora interactiva para seleccionar el color de acento."""

    def __init__(self, key: str, primary: str, label: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.key = key
        self.primary = primary
        self.label_text = label
        self.is_active = is_active
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 14, 0)
        layout.setSpacing(8)

        # Círculo del color
        self.dot = QFrame()
        self.dot.setFixedSize(14, 14)
        self.dot.setStyleSheet(f"background: {primary}; border-radius: 7px;")
        layout.addWidget(self.dot)

        # Texto del color
        self.txt = QLabel(label)
        self.txt.setFont(font(9.5, 600))
        layout.addWidget(self.txt)

        self.update_style()

    def set_active(self, active: bool):
        if self.is_active != active:
            self.is_active = active
            self.update_style()

    def update_style(self):
        self.txt.setStyleSheet(f"color: {C.TEXT};")
        if self.is_active:
            self.setStyleSheet(f"""
                AccentChip {{
                    background: {rgba(self.primary, 0.20)};
                    border: 2px solid {self.primary};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                AccentChip {{
                    background: {C.INPUT};
                    border: 1px solid {C.BORDER};
                    border-radius: 10px;
                }}
                AccentChip:hover {{
                    background: {C.CARD_HOVER};
                    border: 1px solid {C.BORDER_STRONG};
                }}
            """)


class SettingsView(QWidget):
    toast_requested = Signal(str, str, str, object)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("view")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 28, 36, 24)
        main_layout.setSpacing(20)

        # 1. Cabecera
        header = QHBoxLayout()
        header.setSpacing(16)

        icon_card = QFrame()
        icon_card.setFixedSize(48, 48)
        self.icon_card = icon_card
        self._update_icon_card_style()

        ic_layout = QVBoxLayout(icon_card)
        ic_layout.setContentsMargins(0, 0, 0, 0)
        ic_layout.setAlignment(Qt.AlignCenter)
        self.ic_lbl = QLabel()
        self.ic_lbl.setPixmap(pixmap("settings", 24, C.ACCENT))
        self.ic_lbl.setAlignment(Qt.AlignCenter)
        ic_layout.addWidget(self.ic_lbl)
        header.addWidget(icon_card)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_lbl = QLabel("Configuración")
        self.title_lbl.setFont(font(18, 700))
        text_col.addWidget(self.title_lbl)

        self.sub_lbl = QLabel("Personaliza la apariencia, el tema visual y las preferencias de la aplicación.")
        self.sub_lbl.setFont(font(10, 400))
        text_col.addWidget(self.sub_lbl)
        header.addLayout(text_col, 1)

        main_layout.addLayout(header)

        # 2. Contenedor con Scroll para las secciones de configuración
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("scrollContent")
        self.c_layout = QVBoxLayout(content)
        self.c_layout.setContentsMargins(0, 4, 12, 16)
        self.c_layout.setSpacing(24)

        # SECCIÓN A: TEMAS VISUALES
        self._build_theme_section()

        # SECCIÓN B: COLOR DE ACENTO
        self._build_accent_section()

        # SECCIÓN C: COMPORTAMIENTO Y VISOR
        self._build_behavior_section()

        # SECCIÓN D: INFORMACIÓN Y RESTABLECIMIENTO
        self._build_info_section()

        self.c_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        # Escuchar cambios de tema para repintar los elementos
        add_theme_listener(self._on_theme_changed)

    def _update_icon_card_style(self):
        self.icon_card.setStyleSheet(f"""
            background: {rgba(C.ACCENT, 0.16)};
            border: 1px solid {rgba(C.ACCENT, 0.40)};
            border-radius: 12px;
        """)

    def _build_theme_section(self):
        sec = QVBoxLayout()
        sec.setSpacing(10)

        lbl = QLabel("Tema Visual")
        lbl.setFont(font(12, 700))
        sec.addWidget(lbl)

        desc = QLabel("Selecciona el esquema de color que prefieras. El cambio se aplica de inmediato.")
        desc.setFont(font(9.5, 400))
        desc.setStyleSheet(f"color: {C.TEXT_2};")
        sec.addWidget(desc)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.theme_cards: Dict[str, ThemeCard] = {}
        cur_theme = get_setting("theme", CURRENT_THEME_KEY)

        keys = ["dark", "oled", "navy", "emerald", "light"]
        for idx, key in enumerate(keys):
            if key in THEMES:
                th = THEMES[key]
                card = ThemeCard(th, is_active=(key == cur_theme), parent=self)
                card.selected.connect(self._on_theme_selected)
                self.theme_cards[key] = card
                row = idx // 2
                col = idx % 2
                grid.addWidget(card, row, col)

        sec.addLayout(grid)
        self.c_layout.addLayout(sec)

    def _build_accent_section(self):
        sec = QVBoxLayout()
        sec.setSpacing(10)

        lbl = QLabel("Color de Énfasis (Acento)")
        lbl.setFont(font(12, 700))
        sec.addWidget(lbl)

        desc = QLabel("Personaliza el tono de los botones de acción, selección y detalles visuales.")
        desc.setFont(font(9.5, 400))
        desc.setStyleSheet(f"color: {C.TEXT_2};")
        sec.addWidget(desc)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(10)

        self.accent_chips: Dict[str, AccentChip] = {}
        cur_accent = get_setting("accent", CURRENT_ACCENT_KEY)

        for key, (primary, sec_col, soft, label) in ACCENTS.items():
            chip = AccentChip(key, primary, label, is_active=(key == cur_accent), parent=self)
            chip.clicked.connect(lambda ch=False, k=key: self._on_accent_selected(k))
            self.accent_chips[key] = chip
            chips_row.addWidget(chip)

        chips_row.addStretch()
        sec.addLayout(chips_row)
        self.c_layout.addLayout(sec)

    def _build_behavior_section(self):
        sec = QVBoxLayout()
        sec.setSpacing(10)

        lbl = QLabel("Comportamiento y Flujo de Trabajo")
        lbl.setFont(font(12, 700))
        sec.addWidget(lbl)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 14px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(14)

        # Opción 1: Abrir visor automáticamente al finalizar
        auto_open = get_setting("auto_open_viewer", True)
        self.chk_auto_open = QCheckBox("Abrir visor de PDF automáticamente al finalizar tareas")
        self.chk_auto_open.setChecked(auto_open)
        self.chk_auto_open.setFont(font(10, 500))
        self.chk_auto_open.setStyleSheet(f"color: {C.TEXT}; spacing: 10px;")
        self.chk_auto_open.toggled.connect(lambda v: set_setting("auto_open_viewer", v))
        c_layout.addWidget(self.chk_auto_open)

        desc_1 = QLabel("Permite revisar inmediatamente el resultado final generado sin pasos adicionales.")
        desc_1.setFont(font(9, 400))
        desc_1.setStyleSheet(f"color: {C.TEXT_2}; padding-left: 24px;")
        c_layout.addWidget(desc_1)

        sep = QFrame()
        sep.setStyleSheet(f"background: {C.BORDER}; min-height: 1px; max-height: 1px;")
        c_layout.addWidget(sep)

        # Opción 2: Comprobar actualizaciones automáticamente al iniciar
        auto_updates = get_setting("check_updates_startup", True)
        self.chk_auto_updates = QCheckBox("Comprobar actualizaciones automáticamente al iniciar")
        self.chk_auto_updates.setChecked(auto_updates)
        self.chk_auto_updates.setFont(font(10, 500))
        self.chk_auto_updates.setStyleSheet(f"color: {C.TEXT}; spacing: 10px;")
        self.chk_auto_updates.toggled.connect(lambda v: set_setting("check_updates_startup", v))
        c_layout.addWidget(self.chk_auto_updates)

        desc_2 = QLabel("Verifica en segundo plano si existe una versión más reciente en GitHub.")
        desc_2.setFont(font(9, 400))
        desc_2.setStyleSheet(f"color: {C.TEXT_2}; padding-left: 24px;")
        c_layout.addWidget(desc_2)

        sec.addWidget(card)
        self.c_layout.addLayout(sec)

    def _build_info_section(self):
        sec = QVBoxLayout()
        sec.setSpacing(10)

        lbl = QLabel("Acerca de la Aplicación")
        lbl.setFont(font(12, 700))
        sec.addWidget(lbl)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 14px;
            }}
        """)
        c_layout = QHBoxLayout(card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(16)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)

        app_name = QLabel(f"PDF Master Suite v{APP_VERSION}")
        app_name.setFont(font(11, 700))
        app_name.setStyleSheet(f"color: {C.TEXT};")
        info_col.addWidget(app_name)

        desc = QLabel("Aplicación nativa 100% offline. Todos los documentos se procesan en tu propio equipo.")
        desc.setFont(font(9, 400))
        desc.setStyleSheet(f"color: {C.TEXT_2};")
        info_col.addWidget(desc)

        c_layout.addLayout(info_col, 1)

        btn_reset = QPushButton("Restablecer ajustes")
        btn_reset.setObjectName("ghost")
        btn_reset.setFont(font(9.5, 500))
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._on_reset_requested)
        c_layout.addWidget(btn_reset)

        sec.addWidget(card)
        self.c_layout.addLayout(sec)

    def _on_theme_selected(self, key: str):
        set_setting("theme", key)
        apply_theme(theme_key=key)

    def _on_accent_selected(self, key: str):
        set_setting("accent", key)
        apply_theme(accent_key=key)

    def _on_reset_requested(self):
        reset_settings()
        apply_theme(theme_key="dark", accent_key="indigo")
        self.chk_auto_open.setChecked(True)
        self.chk_auto_updates.setChecked(True)
        self.toast_requested.emit("Se han restablecido los ajustes a sus valores por defecto", "Ajustes restablecidos", "info", None)

    def _on_theme_changed(self):
        """Refresca las tarjetas y chips tras un cambio de tema."""
        cur_theme = get_setting("theme", CURRENT_THEME_KEY)
        for k, card in self.theme_cards.items():
            card.set_active(k == cur_theme)
            card.update_style()

        cur_accent = get_setting("accent", CURRENT_ACCENT_KEY)
        for k, chip in self.accent_chips.items():
            chip.set_active(k == cur_accent)
            chip.update_style()

        self._update_icon_card_style()
        self.ic_lbl.setPixmap(pixmap("settings", 24, C.ACCENT))
        self.title_lbl.setStyleSheet(f"color: {C.TEXT};")
        self.sub_lbl.setStyleSheet(f"color: {C.TEXT_2};")

    def closeEvent(self, event):
        remove_theme_listener(self._on_theme_changed)
        super().closeEvent(event)
