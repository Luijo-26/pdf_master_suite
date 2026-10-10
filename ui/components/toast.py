"""
ui/components/toast.py
Notificaciones no bloqueantes superpuestas en la ventana principal.
Aparecen en la esquina inferior derecha con animación suave, ofrecen accesos rápidos
a "Ver resultado" (visor interno), "Abrir archivo" y "Mostrar en carpeta", y se desvanecen automáticamente.
"""

from typing import Optional
import os

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer, Signal
)
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.recents import open_file, open_folder
from ui.theme import C, font, qcolor, rgba


class Toast(QFrame):
    closed = Signal()
    preview_requested = Signal(str)

    def __init__(
        self,
        parent: QWidget,
        message: str,
        title: str = "Operación completada",
        toast_type: str = "success",
        file_path: Optional[str] = None,
        duration_ms: int = 6500,
    ):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("toastCard")
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFixedWidth(400)

        # Configuración por tipo
        palette_map = {
            "success": (C.SUCCESS, "checkcircle", "Éxito"),
            "error": (C.DANGER, "alert", "Error"),
            "warning": (C.WARNING, "alert", "Advertencia"),
            "info": (C.INFO, "info", "Información"),
        }
        color_hex, icon_name, default_title = palette_map.get(toast_type, palette_map["info"])
        actual_title = title or default_title

        # Efecto de opacidad para animación
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        # Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(8)

        # Fila superior: Icono + Título + Botón Cerrar
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap(icon_name, 20, color_hex))
        icon_lbl.setFixedSize(22, 22)
        top_row.addWidget(icon_lbl)

        title_lbl = QLabel(actual_title)
        title_lbl.setFont(font(11, 600))
        title_lbl.setStyleSheet(f"color: {color_hex};")
        top_row.addWidget(title_lbl, 1)

        close_btn = QPushButton()
        close_btn.setObjectName("iconbtn")
        close_btn.setIcon(pixmap("x", 14, C.TEXT_3))
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.dismiss)
        top_row.addWidget(close_btn)
        main_layout.addLayout(top_row)

        # Mensaje descriptivo
        msg_lbl = QLabel(message)
        msg_lbl.setFont(font(9.5, 400))
        msg_lbl.setStyleSheet(f"color: {C.TEXT};")
        msg_lbl.setWordWrap(True)
        main_layout.addWidget(msg_lbl)

        # Acciones contextuales si hay archivo resultante
        if file_path and os.path.exists(file_path):
            action_row = QHBoxLayout()
            action_row.setSpacing(8)

            # Botón destacado: Ver resultado en el visor integrado (si es PDF)
            if file_path.lower().endswith(".pdf"):
                btn_preview = QPushButton(" Ver resultado")
                btn_preview.setObjectName("chip")
                btn_preview.setIcon(pixmap("eye", 13, C.ACCENT))
                btn_preview.setStyleSheet(f"font-weight: 700; color: {C.ACCENT}; border-color: {rgba(C.ACCENT, 0.45)};")
                btn_preview.setCursor(Qt.PointingHandCursor)
                btn_preview.clicked.connect(lambda: [self.preview_requested.emit(file_path), self.dismiss()])
                action_row.addWidget(btn_preview)

            btn_open = QPushButton("Abrir")
            btn_open.setObjectName("chip")
            btn_open.setIcon(pixmap("external", 13, C.ACCENT_SOFT))
            btn_open.setCursor(Qt.PointingHandCursor)
            btn_open.clicked.connect(lambda: open_file(file_path))
            action_row.addWidget(btn_open)

            btn_folder = QPushButton("Carpeta")
            btn_folder.setObjectName("chip")
            btn_folder.setIcon(pixmap("folder", 13, C.TEXT_2))
            btn_folder.setCursor(Qt.PointingHandCursor)
            btn_folder.clicked.connect(lambda: open_folder(file_path))
            action_row.addWidget(btn_folder)

            action_row.addStretch()
            main_layout.addLayout(action_row)

        # Estilo de tarjeta flotante adaptado al tema activo
        self.setStyleSheet(f"""
            QFrame#toastCard {{
                background-color: {C.SURFACE};
                border: 1px solid {rgba(color_hex, 0.45)};
                border-left: 4px solid {color_hex};
                border-radius: 12px;
            }}
        """)

        # Temporizador para auto-ocultar
        if duration_ms > 0:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.dismiss)
            self.timer.start(duration_ms)

        # Animación de entrada
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(220)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def show_animated(self):
        self.show()
        self.fade_anim.start()

    def dismiss(self):
        if hasattr(self, "_dismissing") and self._dismissing:
            return
        self._dismissing = True
        self.fade_anim.stop()
        self.fade_anim.setDuration(180)
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self._on_dismiss_finished)
        self.fade_anim.start()

    def _on_dismiss_finished(self):
        self.closed.emit()
        self.close()


class ToastManager(QWidget):
    """Administrador que posiciona los toasts en cascada sobre la ventana padre."""
    preview_requested = Signal(str)

    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.toasts = []
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def show_toast(
        self,
        message: str,
        title: str = "",
        toast_type: str = "success",
        file_path: Optional[str] = None,
        duration_ms: int = 6500,
    ) -> Toast:
        toast = Toast(
            self.parent_window,
            message=message,
            title=title,
            toast_type=toast_type,
            file_path=file_path,
            duration_ms=duration_ms,
        )
        toast.closed.connect(lambda: self._remove_toast(toast))
        toast.preview_requested.connect(self.preview_requested.emit)
        self.toasts.append(toast)
        self.reposition_toasts()
        toast.show_animated()
        return toast

    def _remove_toast(self, toast: Toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
            self.reposition_toasts()

    def reposition_toasts(self):
        margin_x = 24
        margin_y = 24
        spacing = 10
        p_geom = self.parent_window.rect()

        current_y = p_geom.bottom() - margin_y
        for toast in reversed(self.toasts):
            t_size = toast.sizeHint()
            w = toast.width()
            h = t_size.height()
            x = p_geom.right() - w - margin_x
            y = current_y - h
            toast.setGeometry(x, y, w, h)
            current_y = y - spacing
