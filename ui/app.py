"""
ui/app.py
Ventana principal de PDF Master Suite.
Integra la barra lateral de navegación, el gestor de vistas apiladas (QStackedWidget),
el sistema de notificaciones flotantes (ToastManager) y atajos de teclado globales.
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget
)

from core.settings import get_setting
from core.updater import ReleaseInfo, UpdateCheckThread
from core.version import APP_VERSION
from ui.components.sidebar import Sidebar
from ui.components.toast import ToastManager
from ui.components.update_dialog import UpdateDialog
from ui.icons import icon, logo_pixmap
from ui.theme import C
from ui.views.compress import CompressView
from ui.views.crop import CropView
from ui.views.excel import ExcelView
from ui.views.home import HomeView
from ui.views.images import ImagesView
from ui.views.merge import MergeView
from ui.views.organize import OrganizeView
from ui.views.page_numbers import PageNumbersView
from ui.views.pdf_to_images import PdfToImagesView
from ui.views.pdf_to_text import PdfToTextView
from ui.views.pdf_to_word import PdfToWordView
from ui.views.pdf_viewer import PdfViewerView
from ui.views.powerpoint import PowerpointView
from ui.views.rotate_bulk import RotateBulkView
from ui.views.security import SecurityView
from ui.views.settings import SettingsView
from ui.views.split import SplitView
from ui.views.watermark import WatermarkView
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
        self.sidebar.check_updates_requested.connect(self.check_for_updates_manual)
        root_layout.addWidget(self.sidebar)

        # 2. Contenedor de vistas apiladas
        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        # 3. Administrador de Toasts
        self.toast_mgr = ToastManager(self)
        self.toast_mgr.preview_requested.connect(self.open_in_viewer)

        # Seguimiento de vistas para navegacion del visor
        self._current_view_key: str = "home"
        self._previous_view_key: str = "home"

        # 4. Hilo de comprobación de actualizaciones
        self._update_checker_thread: Optional[UpdateCheckThread] = None

        # 5. Instanciar vistas
        self.views: Dict[str, QWidget] = {}
        self._init_views()

        # 6. Atajos de teclado globales
        self._init_shortcuts()

        # Vista inicial: Home
        self.navigate_to("home")

        # 7. Verificación silenciosa en segundo plano diferida (2.5 segundos)
        QTimer.singleShot(2500, self.check_for_updates_auto)

    def _init_views(self):
        # Home
        self.home_view = HomeView(self)
        self.home_view.tool_requested.connect(self.navigate_to_with_files)
        self._add_view("home", self.home_view)

        # ORGANIZAR
        self.merge_view = MergeView(self)
        self._add_tool_view("merge", self.merge_view)

        self.split_view = SplitView(self)
        self._add_tool_view("split", self.split_view)

        self.organize_view = OrganizeView(self)
        self._add_tool_view("organize", self.organize_view)

        self.rotate_bulk_view = RotateBulkView(self)
        self._add_tool_view("rotate_bulk", self.rotate_bulk_view)

        self.crop_view = CropView(self)
        self._add_tool_view("crop", self.crop_view)

        # OPTIMIZAR
        self.compress_view = CompressView(self)
        self._add_tool_view("compress", self.compress_view)

        # EDITAR & ESTILO
        self.watermark_view = WatermarkView(self)
        self._add_tool_view("watermark", self.watermark_view)

        self.page_numbers_view = PageNumbersView(self)
        self._add_tool_view("page_numbers", self.page_numbers_view)

        # CONVERTIR A PDF
        self.images_view = ImagesView(self)
        self._add_tool_view("images", self.images_view)

        self.word_view = WordView(self)
        self._add_tool_view("word", self.word_view)

        self.excel_view = ExcelView(self)
        self._add_tool_view("excel", self.excel_view)

        self.powerpoint_view = PowerpointView(self)
        self._add_tool_view("powerpoint", self.powerpoint_view)

        # CONVERTIR DESDE PDF
        self.pdf_to_images_view = PdfToImagesView(self)
        self._add_tool_view("pdf_to_images", self.pdf_to_images_view)

        self.pdf_to_word_view = PdfToWordView(self)
        self._add_tool_view("pdf_to_word", self.pdf_to_word_view)

        self.pdf_to_text_view = PdfToTextView(self)
        self._add_tool_view("pdf_to_text", self.pdf_to_text_view)

        # SEGURIDAD
        self.security_view = SecurityView(self)
        self._add_tool_view("security", self.security_view)

        # CONFIGURACIÓN
        self.settings_view = SettingsView(self)
        self._add_tool_view("settings", self.settings_view)

        # VISOR DE PDF
        self.home_view.preview_requested.connect(self.open_in_viewer)
        self.pdf_viewer_view = PdfViewerView(self)
        self.pdf_viewer_view.back_requested.connect(self._on_viewer_back)
        self._add_tool_view("viewer", self.pdf_viewer_view)

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
        # Apertura automática en el visor integrado si el usuario lo tiene habilitado
        if toast_type == "success" and file_path and file_path.lower().endswith(".pdf"):
            if get_setting("auto_open_viewer", True):
                current_widget = self.stack.currentWidget()
                tool_title = getattr(current_widget, "tool_title", "Herramienta")
                self.open_in_viewer(file_path, source_tool_name=tool_title)

    def _init_shortcuts(self):
        shortcuts_map = {
            "Ctrl+H": "home",
            "Ctrl+0": "viewer",
            "Ctrl+,": "settings",
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

        if self._current_view_key != "viewer":
            self._previous_view_key = self._current_view_key
        self._current_view_key = key

        target_widget = self.views[key]
        self.stack.setCurrentWidget(target_widget)
        self.sidebar.set_current(key)

        if key == "home":
            self.home_view.refresh_recents()

    def open_in_viewer(self, file_path: str, source_tool_name: Optional[str] = None):
        """Carga un documento en el visor de PDF integrado y cambia a la vista."""
        if self._current_view_key != "viewer":
            self._previous_view_key = self._current_view_key
        self.pdf_viewer_view.load_pdf(file_path, source_tool_name=source_tool_name)
        self.navigate_to("viewer")

    def _on_viewer_back(self):
        """Regresa a la vista desde donde se invocó el visor."""
        target = self._previous_view_key if self._previous_view_key and self._previous_view_key != "viewer" else "home"
        self.navigate_to(target)

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
        elif first.endswith((".xlsx", ".xls")):
            self.navigate_to_with_files("excel", files)
        elif first.endswith((".pptx", ".ppt")):
            self.navigate_to_with_files("powerpoint", files)
        elif first.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp")):
            self.navigate_to_with_files("images", files)
        elif first.endswith(".pdf"):
            if len(files) > 1:
                self.navigate_to_with_files("merge", files)
            else:
                self.navigate_to_with_files("organize", files)
        else:
            self.navigate_to_with_files("merge", files)

    # =========================================================================
    # SISTEMA DE ACTUALIZACIÓN
    # =========================================================================
    def check_for_updates_auto(self):
        """Verificación silenciosa en segundo plano al arrancar la app."""
        if not get_setting("check_updates_startup", True):
            return

        if self._update_checker_thread and self._update_checker_thread.isRunning():
            return

        self._update_checker_thread = UpdateCheckThread(force_check=False, parent=self)
        self._update_checker_thread.check_finished.connect(self._on_update_check_auto_finished)
        self._update_checker_thread.start()

    def _on_update_check_auto_finished(self, release_info: Optional[ReleaseInfo], has_update: bool):
        if has_update and release_info:
            dialog = UpdateDialog(release_info, parent=self)
            dialog.exec()

    def check_for_updates_manual(self):
        """Verificación manual accionada por el usuario desde el menú lateral."""
        if self._update_checker_thread and self._update_checker_thread.isRunning():
            self.toast_mgr.show_toast(
                message="Verificando servidores de GitHub...",
                title="Comprobando actualizaciones",
                toast_type="info",
            )
            return

        self.toast_mgr.show_toast(
            message="Conectando con el servidor de versiones...",
            title="Buscando actualizaciones",
            toast_type="info",
            duration_ms=3000,
        )

        self._update_checker_thread = UpdateCheckThread(force_check=True, parent=self)
        self._update_checker_thread.check_finished.connect(self._on_update_check_manual_finished)
        self._update_checker_thread.check_failed.connect(self._on_update_check_manual_failed)
        self._update_checker_thread.start()

    def _on_update_check_manual_finished(self, release_info: Optional[ReleaseInfo], has_update: bool):
        if has_update and release_info:
            dialog = UpdateDialog(release_info, parent=self)
            dialog.exec()
        elif release_info:
            self.toast_mgr.show_toast(
                message=f"Tienes instalada la versión más reciente (v{APP_VERSION}).",
                title="PDF Master Suite está al día",
                toast_type="success",
                duration_ms=4500,
            )
        else:
            self.toast_mgr.show_toast(
                message="No se pudo obtener información del servidor. Revisa tu conexión.",
                title="Sin conexión de red",
                toast_type="warning",
                duration_ms=4500,
            )

    def _on_update_check_manual_failed(self, error_msg: str):
        self.toast_mgr.show_toast(
            message="Ocurrió un error al contactar con GitHub Releases.",
            title="Error de comprobación",
            toast_type="error",
            duration_ms=4500,
        )

    def closeEvent(self, event):
        if self._update_checker_thread and self._update_checker_thread.isRunning():
            self._update_checker_thread.quit()
            self._update_checker_thread.wait(1000)
        super().closeEvent(event)

