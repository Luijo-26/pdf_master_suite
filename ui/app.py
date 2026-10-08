"""
ui/app.py
Ventana principal de PDF Master Suite.
Integra la barra lateral de navegación, el gestor de vistas apiladas (QStackedWidget),
el sistema de notificaciones flotantes (ToastManager) y atajos de teclado globales.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
)

from ui.components.sidebar import Sidebar
from ui.components.toast import ToastManager
from ui.icons import icon, logo_pixmap
from ui.theme import C
from ui.views.compress import CompressView
from ui.views.home import HomeView
from ui.views.images import ImagesView
from ui.views.merge import MergeView
from ui.views.organize import OrganizeView
from ui.views.security import SecurityView
from ui.views.split import SplitView
from ui.views.word import WordView


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Master Suite — Gestor Integral de Documentos")
        self.resize(1120, 780)
        self.setMinimumSize(960, 680)
        self.setAcceptDrops(True)

        # Icono de la ventana
        self.setWindowIcon(QIcon(logo_pixmap(64)))

        # Widget central
        root_widget = QWidget()
        root_widget.setObjectName("root")
        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root_widget)

        # 1. Menú lateral (Sidebar)
        self.sidebar = Sidebar(self)
        self.sidebar.navigate_requested.connect(self.navigate_to)
        root_layout.addWidget(self.sidebar)

        # 2. Contenedor de vistas apiladas
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        # 3. Administrador de Toasts
        self.toast_mgr = ToastManager(self)

        # 4. Instanciar vistas
        self.views: Dict[str, QWidget] = {}
        self._init_views()

        # 5. Atajos de teclado globales
        self._init_shortcuts()

        # Vista inicial: Home
        self.navigate_to("home")

    def _init_views(self):
        # Home
        self.home_view = HomeView(self)
        self.home_view.tool_requested.connect(self.navigate_to_with_files)
        self._add_view("home", self.home_view)

        # 1. Unir
        self.merge_view = MergeView(self)
        self._add_tool_view("merge", self.merge_view)

        # 2. Dividir
        self.split_view = SplitView(self)
        self._add_tool_view("split", self.split_view)

        # 3. Organizar
        self.organize_view = OrganizeView(self)
        self._add_tool_view("organize", self.organize_view)

        # 4. Comprimir
        self.compress_view = CompressView(self)
        self._add_tool_view("compress", self.compress_view)

        # 5. Imágenes
        self.images_view = ImagesView(self)
        self._add_tool_view("images", self.images_view)

        # 6. Word
        self.word_view = WordView(self)
        self._add_tool_view("word", self.word_view)

        # 7. Seguridad
        self.security_view = SecurityView(self)
        self._add_tool_view("security", self.security_view)

    def _add_view(self, key: str, widget: QWidget):
        self.views[key] = widget
        self.stack.addWidget(widget)

    def _add_tool_view(self, key: str, widget: QWidget):
        if hasattr(widget, "toast_requested"):
            widget.toast_requested.connect(self._on_toast_requested)
        self._add_view(key, widget)

    def _on_toast_requested(self, msg: str, title: str, toast_type: str, file_path: Optional[str]):
        self.toast_mgr.show_toast(
            message=msg,
            title=title,
            toast_type=toast_type,
            file_path=file_path,
        )

    def _init_shortcuts(self):
        shortcuts_map = {
            "Ctrl+H": "home",
            "Ctrl+1": "merge",
            "Ctrl+2": "split",
            "Ctrl+3": "organize",
            "Ctrl+4": "compress",
            "Ctrl+5": "images",
            "Ctrl+6": "word",
            "Ctrl+7": "security",
        }
        for seq, tool_key in shortcuts_map.items():
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(lambda k=tool_key: self.navigate_to(k))

    def navigate_to(self, key: str):
        """Cambia a la vista indicada y actualiza el menú lateral."""
        if key not in self.views:
            return

        target_widget = self.views[key]
        self.stack.setCurrentWidget(target_widget)
        self.sidebar.set_current(key)

        if key == "home":
            self.home_view.refresh_recents()

    def navigate_to_with_files(self, key: str, files: List[str]):
        """Navega a una herramienta y le carga archivos iniciales."""
        self.navigate_to(key)
        view = self.views.get(key)
        if view and hasattr(view, "add_initial_files") and files:
            view.add_initial_files(files)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast_mgr.reposition_toasts()

    # Arrastrar y soltar general sobre la ventana
    def dragEnterEvent(self, event: QDragEnterEvent):
        # Ignorar arrastre interno de reordenación de filas o páginas
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasFormat("application/x-pdf-page-card"):
            event.ignore()
            return

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if not files:
            event.ignore()
            return

        event.acceptProposedAction()
        first = files[0].lower()

        # Si ya estamos en una vista compatible con el archivo, enviárselo directamente
        current_view = self.stack.currentWidget()
        if hasattr(current_view, "add_initial_files"):
            current_view.add_initial_files(files)
            return

        # De lo contrario, redirigir inteligentemente
        if first.endswith((".docx", ".doc")):
            self.navigate_to_with_files("word", files)
        elif first.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
            self.navigate_to_with_files("images", files)
        elif first.endswith(".pdf"):
            if len(files) > 1:
                self.navigate_to_with_files("merge", files)
            else:
                self.navigate_to_with_files("organize", files)
        else:
            self.navigate_to_with_files("merge", files)
