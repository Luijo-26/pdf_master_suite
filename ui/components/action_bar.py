"""
ui/components/action_bar.py
Barra de acción inferior fija para todas las herramientas.
Proporciona el resumen del estado actual, barra de progreso para tareas en segundo plano,
y el botón principal de ejecución ("Guardar como...") con atajo Ctrl+Enter.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.theme import C, font, rgba


class ActionBar(QFrame):
    action_triggered = Signal()

    def __init__(
        self,
        button_text: str = "Guardar como...",
        icon_name: str = "check",
        initial_summary: str = "Esperando archivos...",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("actionbar")
        self.setFixedHeight(68)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(16)

        # 1. Columna izquierda: Resumen y estado
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        left_col.setAlignment(Qt.AlignVCenter)

        self.summary_lbl = QLabel(initial_summary)
        self.summary_lbl.setFont(font(10, 500))
        self.summary_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        left_col.addWidget(self.summary_lbl)

        # Barra de progreso integrada (oculta por defecto)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {C.INPUT};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {C.ACCENT};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.hide()
        left_col.addWidget(self.progress_bar)

        layout.addLayout(left_col, 1)

        # 2. Botón de acción principal
        self.action_btn = QPushButton(button_text)
        self.action_btn.setObjectName("primary")
        self.action_btn.setIcon(pixmap(icon_name, 16, "white"))
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setFixedHeight(44)
        self.action_btn.setEnabled(False)
        self.action_btn.clicked.connect(self.action_triggered.emit)
        layout.addWidget(self.action_btn)

        # Atajo Ctrl+Enter para activar la acción
        self.shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut.activated.connect(self._on_shortcut_activated)

    def set_summary(self, text: str, is_warning: bool = False):
        self.summary_lbl.setText(text)
        color = C.WARNING if is_warning else C.TEXT_2
        self.summary_lbl.setStyleSheet(f"color: {color};")

    def set_enabled(self, enabled: bool):
        self.action_btn.setEnabled(enabled)

    def set_button_enabled(self, enabled: bool):
        self.action_btn.setEnabled(enabled)

    def set_button_text(self, text: str, icon_name: str = "check"):
        self.action_btn.setText(text)
        self.action_btn.setIcon(pixmap(icon_name, 16, "white"))

    def start_processing(self, message: str = "Procesando documento..."):
        self.action_btn.setEnabled(False)
        self.summary_lbl.setText(message)
        self.summary_lbl.setStyleSheet(f"color: {C.INFO};")
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.progress_bar.show()

    def set_progress(self, current: int, total: int, message: str = ""):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        if message:
            self.summary_lbl.setText(message)
            self.summary_lbl.setStyleSheet(f"color: {C.INFO};")

    def stop_processing(self, final_message: str = "Listo", is_success: bool = True):
        self.progress_bar.hide()
        self.summary_lbl.setText(final_message)
        color = C.SUCCESS if is_success else C.DANGER
        self.summary_lbl.setStyleSheet(f"color: {color};")
        self.action_btn.setEnabled(True)

    def _on_shortcut_activated(self):
        if self.action_btn.isEnabled():
            self.action_triggered.emit()
