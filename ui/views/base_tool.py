"""
ui/views/base_tool.py
Clase base para todas las herramientas de la suite.
Estructura uniforme en 3 pasos: Encabezado claro -> Contenido principal -> Barra de acción fija.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget
)

from ui.components.action_bar import ActionBar
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, rgba
from ui.worker import Worker, start as start_worker


class BaseToolView(QWidget):
    """
    Vista base para herramientas.
    Proporciona cabecera uniforme, layout principal, barra de acción inferior y
    método estandarizado de ejecución en segundo plano.
    """
    toast_requested = Signal(str, str, str, object)  # msg, title, type, file_path

    def __init__(
        self,
        title: str,
        subtitle: str,
        icon_name: str,
        accent_color: str,
        button_text: str = "Guardar como...",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.tool_title = title
        self.tool_subtitle = subtitle
        self.icon_name = icon_name
        self.accent_color = accent_color
        self._is_busy = False

        # Layout vertical principal
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 24, 28, 0)
        root_layout.setSpacing(16)

        # 1. Cabecera de la herramienta
        header = QHBoxLayout()
        header.setSpacing(14)

        icon_card = QFrame()
        icon_card.setFixedSize(46, 46)
        icon_card.setStyleSheet(f"""
            background: {rgba(accent_color, 0.16)};
            border: 1px solid {rgba(accent_color, 0.40)};
            border-radius: 12px;
        """)
        ic_layout = QVBoxLayout(icon_card)
        ic_layout.setContentsMargins(0, 0, 0, 0)
        ic_layout.setAlignment(Qt.AlignCenter)
        ic_lbl = QLabel()
        ic_lbl.setPixmap(pixmap(icon_name, 24, accent_color))
        ic_lbl.setAlignment(Qt.AlignCenter)
        ic_layout.addWidget(ic_lbl)
        header.addWidget(icon_card)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setProperty("role", "title")
        title_lbl.setFont(font(16, 700))
        text_col.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setProperty("role", "subtitle")
        sub_lbl.setFont(font(9.5, 400))
        text_col.addWidget(sub_lbl)
        header.addLayout(text_col, 1)

        root_layout.addLayout(header)

        # 2. Contenedor de contenido de la herramienta (implementado por subclases)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 8)
        self.content_layout.setSpacing(12)
        root_layout.addWidget(self.content_widget, 1)

        # 3. Barra de acción inferior fija
        self.action_bar = ActionBar(
            button_text=button_text,
            icon_name="check",
            initial_summary="Selecciona o arrastra los archivos para comenzar",
            parent=self,
        )
        self.action_bar.action_triggered.connect(self.on_action_execute)
        root_layout.addWidget(self.action_bar)

    def on_action_execute(self):
        """Método abstracto a implementar por cada herramienta."""
        pass

    def run_task(
        self,
        task_func: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        initial_msg: str = "Procesando documento...",
        with_progress: bool = False,
        with_items: bool = False,
    ):
        """Ejecuta una función en segundo plano con estados reactivos en la ActionBar."""
        if self._is_busy:
            return

        self._is_busy = True
        self.action_bar.start_processing(initial_msg)

        def _success_wrapper(result):
            self._is_busy = False
            self.action_bar.stop_processing("Listo", is_success=True)
            if on_success:
                on_success(result)

        def _error_wrapper(err_msg: str):
            self._is_busy = False
            self.action_bar.stop_processing(f"Error: {err_msg}", is_success=False)
            self.toast_requested.emit(err_msg, "Error", "error", None)
            if on_error:
                on_error(err_msg)

        w = Worker(task_func, with_progress=with_progress, with_items=with_items)
        if with_progress:
            def _prog(cur, tot, txt):
                self.action_bar.set_progress(cur, tot, txt)
            start_worker(w, on_done=_success_wrapper, on_error=_error_wrapper, on_progress=_prog)
        else:
            start_worker(w, on_done=_success_wrapper, on_error=_error_wrapper)

    def notify_success(self, message: str, file_path: Optional[str] = None, tool_name: str = ""):
        """Emite notificación exitosa y registra en recientes."""
        if file_path:
            add_recent(file_path, tool_name or self.tool_title)
        self.toast_requested.emit(message, "Completado con éxito", "success", file_path)

    def add_initial_files(self, files: List[str]):
        """Carga automáticamente archivos en la herramienta activa."""
        if not files:
            return
        if hasattr(self, "_on_file_selected"):
            self._on_file_selected(files)
        elif hasattr(self, "_on_files_added"):
            self._on_files_added(files)
        elif hasattr(self, "file_list"):
            self.file_list.add_files(files)

