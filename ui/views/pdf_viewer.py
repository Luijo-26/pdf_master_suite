"""
ui/views/pdf_viewer.py
Visor de PDF interactivo de alta fidelidad para PDF Master Suite.
Construido con PySide6.QtPdf y PySide6.QtPdfWidgets (QPdfView y QPdfDocument).
Soporta zoom dinámico, modos de página continua y simple, navegación rápida,
rotación en vivo y previsualización directa de resultados generados.
"""

import os
import shutil
from typing import Optional

from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.recents import open_file, open_folder
from ui.theme import (
    C, add_theme_listener, font, format_bytes, remove_theme_listener, rgba
)


class PdfViewerView(QWidget):
    toast_requested = Signal(str, str, str, object)
    back_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("view")
        self.setAcceptDrops(True)

        self._current_file: Optional[str] = None
        self._source_tool_name: Optional[str] = None
        self._zoom_factor: float = 1.0

        # Documento y Visor QtPdf
        self.doc = QPdfDocument(self)
        self.doc.statusChanged.connect(self._on_doc_status_changed)

        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.doc)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        # Escuchar cambios de página del navegador
        self.nav = self.pdf_view.pageNavigator()
        self.nav.currentPageChanged.connect(self._on_current_page_changed)

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. Barra de Herramientas Superior
        self._build_toolbar()
        main_layout.addWidget(self.toolbar_card)

        # 2. Banner de resultado contextual (inicialmente oculto)
        self._build_result_banner()
        main_layout.addWidget(self.result_banner)

        # 3. Contenedor Apilado (Página Vacía vs Lienzo QPdfView)
        self.stack = QStackedWidget(self)

        # Página Vacía (Empty State)
        self.empty_page = self._build_empty_page()
        self.stack.addWidget(self.empty_page)

        # Página de Visualización Activa
        viewer_container = QFrame()
        viewer_container.setStyleSheet(f"""
            QFrame {{
                background: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)
        self.viewer_container = viewer_container
        vc_layout = QVBoxLayout(viewer_container)
        vc_layout.setContentsMargins(2, 2, 2, 2)
        vc_layout.addWidget(self.pdf_view)
        self.stack.addWidget(viewer_container)

        main_layout.addWidget(self.stack, 1)

        # Atajos de teclado locales del visor
        self._init_shortcuts()

        # Tema dinámico
        add_theme_listener(self._on_theme_changed)

        # Estado inicial vacío
        self.stack.setCurrentIndex(0)
        self._update_controls_state()

    def _build_toolbar(self):
        self.toolbar_card = QFrame()
        self._update_toolbar_style()

        tb_layout = QHBoxLayout(self.toolbar_card)
        tb_layout.setContentsMargins(12, 8, 12, 8)
        tb_layout.setSpacing(10)

        # Botón Volver
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setObjectName("ghost")
        self.btn_back.setIcon(pixmap("chevronleft", 14, C.TEXT_2))
        self.btn_back.setFont(font(9.5, 600))
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self._on_back_clicked)
        tb_layout.addWidget(self.btn_back)

        # Separador 1
        self.sep1 = self._create_separator()
        tb_layout.addWidget(self.sep1)

        # Info del Archivo
        file_info_col = QVBoxLayout()
        file_info_col.setSpacing(1)
        self.file_name_lbl = QLabel("Ningún archivo cargado")
        self.file_name_lbl.setFont(font(10, 700))
        self.file_name_lbl.setStyleSheet(f"color: {C.TEXT};")
        file_info_col.addWidget(self.file_name_lbl)

        self.file_meta_lbl = QLabel("Visor de documentos local")
        self.file_meta_lbl.setFont(font(8.5, 400))
        self.file_meta_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        file_info_col.addWidget(self.file_meta_lbl)
        tb_layout.addLayout(file_info_col)

        tb_layout.addStretch(1)

        # Controles de Navegación de Páginas
        self.btn_prev = QPushButton()
        self.btn_prev.setObjectName("chip")
        self.btn_prev.setIcon(pixmap("chevronleft", 12, C.TEXT))
        self.btn_prev.setFixedSize(30, 30)
        self.btn_prev.setToolTip("Página anterior (← o RePág)")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.clicked.connect(self._prev_page)
        tb_layout.addWidget(self.btn_prev)

        self.page_input = QLineEdit("1")
        self.page_input.setFixedWidth(44)
        self.page_input.setAlignment(Qt.AlignCenter)
        self.page_input.setFont(font(9.5, 600))
        self.page_input.setToolTip("Escribe el número de página y pulsa Enter")
        self.page_input.returnPressed.connect(self._on_page_input_submitted)
        tb_layout.addWidget(self.page_input)

        self.page_total_lbl = QLabel("/ 0")
        self.page_total_lbl.setFont(font(9.5, 500))
        self.page_total_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        tb_layout.addWidget(self.page_total_lbl)

        self.btn_next = QPushButton()
        self.btn_next.setObjectName("chip")
        self.btn_next.setIcon(pixmap("chevronright", 12, C.TEXT))
        self.btn_next.setFixedSize(30, 30)
        self.btn_next.setToolTip("Página siguiente (→ o AvPág)")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_page)
        tb_layout.addWidget(self.btn_next)

        # Separador 2
        self.sep2 = self._create_separator()
        tb_layout.addWidget(self.sep2)

        # Controles de Zoom
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setObjectName("chip")
        self.btn_zoom_out.setIcon(pixmap("zoom_out", 14, C.TEXT))
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.setToolTip("Reducir zoom (Ctrl -)")
        self.btn_zoom_out.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        tb_layout.addWidget(self.btn_zoom_out)

        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setFixedWidth(48)
        self.zoom_lbl.setAlignment(Qt.AlignCenter)
        self.zoom_lbl.setFont(font(9, 600))
        self.zoom_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        tb_layout.addWidget(self.zoom_lbl)

        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setObjectName("chip")
        self.btn_zoom_in.setIcon(pixmap("zoom_in", 14, C.TEXT))
        self.btn_zoom_in.setFixedSize(30, 30)
        self.btn_zoom_in.setToolTip("Aumentar zoom (Ctrl +)")
        self.btn_zoom_in.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        tb_layout.addWidget(self.btn_zoom_in)

        self.btn_fit_width = QPushButton("Ajustar Ancho")
        self.btn_fit_width.setObjectName("chip")
        self.btn_fit_width.setFont(font(8.5, 600))
        self.btn_fit_width.setCursor(Qt.PointingHandCursor)
        self.btn_fit_width.setToolTip("Ajustar al ancho de la ventana")
        self.btn_fit_width.clicked.connect(self._fit_to_width)
        tb_layout.addWidget(self.btn_fit_width)

        self.btn_fit_page = QPushButton("Pág. Entera")
        self.btn_fit_page.setObjectName("chip")
        self.btn_fit_page.setFont(font(8.5, 600))
        self.btn_fit_page.setCursor(Qt.PointingHandCursor)
        self.btn_fit_page.setToolTip("Ajustar página completa en pantalla")
        self.btn_fit_page.clicked.connect(self._fit_to_page)
        tb_layout.addWidget(self.btn_fit_page)

        # Modo continuo vs individual
        self.btn_mode = QPushButton("Continuo")
        self.btn_mode.setObjectName("chip")
        self.btn_mode.setFont(font(8.5, 600))
        self.btn_mode.setCursor(Qt.PointingHandCursor)
        self.btn_mode.setToolTip("Alternar modo de lectura continua o página a página")
        self.btn_mode.clicked.connect(self._toggle_page_mode)
        tb_layout.addWidget(self.btn_mode)

        # Separador 3
        self.sep3 = self._create_separator()
        tb_layout.addWidget(self.sep3)

        # Acciones de Archivo
        self.btn_save_copy = QPushButton(" Guardar copia...")
        self.btn_save_copy.setObjectName("chip")
        self.btn_save_copy.setIcon(pixmap("download", 13, C.ACCENT))
        self.btn_save_copy.setFont(font(9, 600))
        self.btn_save_copy.setCursor(Qt.PointingHandCursor)
        self.btn_save_copy.clicked.connect(self._save_copy)
        tb_layout.addWidget(self.btn_save_copy)

        self.btn_folder = QPushButton()
        self.btn_folder.setObjectName("chip")
        self.btn_folder.setIcon(pixmap("folder", 14, C.TEXT_2))
        self.btn_folder.setFixedSize(30, 30)
        self.btn_folder.setToolTip("Mostrar archivo en el Explorador de Windows")
        self.btn_folder.setCursor(Qt.PointingHandCursor)
        self.btn_folder.clicked.connect(self._open_in_folder)
        tb_layout.addWidget(self.btn_folder)

        self.btn_open_dialog = QPushButton("Abrir otro...")
        self.btn_open_dialog.setObjectName("ghost")
        self.btn_open_dialog.setFont(font(9, 600))
        self.btn_open_dialog.setCursor(Qt.PointingHandCursor)
        self.btn_open_dialog.clicked.connect(self._choose_and_open_pdf)
        tb_layout.addWidget(self.btn_open_dialog)

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"background: {C.BORDER};")
        return sep

    def _update_toolbar_style(self):
        self.toolbar_card.setStyleSheet(f"""
            QFrame {{
                background-color: {C.SURFACE};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)

    def _build_result_banner(self):
        self.result_banner = QFrame()
        self.result_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {rgba(C.SUCCESS, 0.12)};
                border: 1px solid {rgba(C.SUCCESS, 0.35)};
                border-left: 4px solid {C.SUCCESS};
                border-radius: 10px;
            }}
        """)
        rb_layout = QHBoxLayout(self.result_banner)
        rb_layout.setContentsMargins(14, 8, 14, 8)
        rb_layout.setSpacing(10)

        self.rb_icon = QLabel()
        self.rb_icon.setPixmap(pixmap("checkcircle", 18, C.SUCCESS))
        rb_layout.addWidget(self.rb_icon)

        self.rb_text = QLabel("Documento generado con éxito listo para su revisión.")
        self.rb_text.setFont(font(9.5, 600))
        self.rb_text.setStyleSheet(f"color: {C.SUCCESS};")
        rb_layout.addWidget(self.rb_text, 1)

        btn_close_banner = QPushButton()
        btn_close_banner.setObjectName("iconbtn")
        btn_close_banner.setIcon(pixmap("x", 12, C.TEXT_3))
        btn_close_banner.setFixedSize(20, 20)
        btn_close_banner.setCursor(Qt.PointingHandCursor)
        btn_close_banner.clicked.connect(self.result_banner.hide)
        rb_layout.addWidget(btn_close_banner)

        self.result_banner.hide()

    def _build_empty_page(self) -> QWidget:
        empty_card = QFrame()
        empty_card.setStyleSheet(f"""
            QFrame {{
                background-color: {C.SURFACE};
                border: 2px dashed {C.BORDER};
                border-radius: 16px;
            }}
        """)
        layout = QVBoxLayout(empty_card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        ic = QLabel()
        ic.setPixmap(pixmap("filetext", 56, C.ACCENT))
        ic.setAlignment(Qt.AlignCenter)
        layout.addWidget(ic)

        title = QLabel("Visor de Documentos PDF")
        title.setFont(font(16, 700))
        title.setStyleSheet(f"color: {C.TEXT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Arrastra y suelta cualquier archivo PDF aquí para previsualizarlo\no examina tu equipo con el botón a continuación.")
        sub.setFont(font(10, 400))
        sub.setStyleSheet(f"color: {C.TEXT_2};")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        btn_select = QPushButton("+ Abrir archivo PDF...")
        btn_select.setObjectName("primary")
        btn_select.setFont(font(10.5, 600))
        btn_select.setCursor(Qt.PointingHandCursor)
        btn_select.clicked.connect(self._choose_and_open_pdf)
        layout.addWidget(btn_select, 0, Qt.AlignCenter)

        return empty_card

    def _init_shortcuts(self):
        # Flecha izquierda / derecha para pasar páginas
        sc_prev = QShortcut(QKeySequence("Left"), self)
        sc_prev.activated.connect(self._prev_page)
        sc_next = QShortcut(QKeySequence("Right"), self)
        sc_next.activated.connect(self._next_page)

        # Zoom con teclado
        sc_zin = QShortcut(QKeySequence("Ctrl+="), self)
        sc_zin.activated.connect(self._zoom_in)
        sc_zout = QShortcut(QKeySequence("Ctrl+-"), self)
        sc_zout.activated.connect(self._zoom_out)

    def load_pdf(self, file_path: str, source_tool_name: Optional[str] = None):
        """Carga y visualiza un archivo PDF en el visor interactivo."""
        if not file_path or not os.path.exists(file_path):
            self.toast_requested.emit("El archivo PDF indicado no existe o no se puede leer.", "Error al abrir", "error", None)
            return

        self._current_file = os.path.normpath(file_path)
        self._source_tool_name = source_tool_name

        # Cerrar previo y cargar nuevo
        self.doc.close()
        err = self.doc.load(self._current_file)
        if err != QPdfDocument.Error.None_:
            self.toast_requested.emit(f"Error al procesar el archivo PDF: {err}", "Error", "error", None)
            self.stack.setCurrentIndex(0)
            return

        total_pages = self.doc.pageCount()
        file_size = os.path.getsize(self._current_file)
        fname = os.path.basename(self._current_file)

        self.file_name_lbl.setText(fname)
        self.file_meta_lbl.setText(f"{total_pages} página(s)  •  {format_bytes(file_size)}")
        self.page_total_lbl.setText(f"/ {total_pages}")
        self.page_input.setText("1")

        # Configurar modo de visualización inicial
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.zoom_lbl.setText("Ancho")

        # Mostrar u ocultar banner de resultado
        if source_tool_name:
            self.rb_text.setText(f"¡Documento generado con éxito desde '{source_tool_name}'! Listo para tu revisión.")
            self.result_banner.show()
        else:
            self.result_banner.hide()

        self.stack.setCurrentIndex(1)
        self._update_controls_state()

    def _on_doc_status_changed(self, status: QPdfDocument.Status):
        if status == QPdfDocument.Status.Ready:
            self._update_controls_state()

    def _on_current_page_changed(self, page_index: int):
        self.page_input.setText(str(page_index + 1))
        self._update_nav_buttons_state()

    def _update_controls_state(self):
        has_doc = (self._current_file is not None and self.doc.pageCount() > 0)
        self.btn_prev.setEnabled(has_doc)
        self.btn_next.setEnabled(has_doc)
        self.page_input.setEnabled(has_doc)
        self.btn_zoom_in.setEnabled(has_doc)
        self.btn_zoom_out.setEnabled(has_doc)
        self.btn_fit_width.setEnabled(has_doc)
        self.btn_fit_page.setEnabled(has_doc)
        self.btn_mode.setEnabled(has_doc)
        self.btn_save_copy.setEnabled(has_doc)
        self.btn_folder.setEnabled(has_doc)
        if has_doc:
            self._update_nav_buttons_state()

    def _update_nav_buttons_state(self):
        tot = self.doc.pageCount()
        cur = self.nav.currentPage()
        self.btn_prev.setEnabled(cur > 0)
        self.btn_next.setEnabled(cur < tot - 1)

    def _prev_page(self):
        cur = self.nav.currentPage()
        if cur > 0:
            self.nav.jump(cur - 1, QPointF())

    def _next_page(self):
        cur = self.nav.currentPage()
        tot = self.doc.pageCount()
        if cur < tot - 1:
            self.nav.jump(cur + 1, QPointF())

    def _on_page_input_submitted(self):
        txt = self.page_input.text().strip()
        try:
            target = int(txt) - 1
            tot = self.doc.pageCount()
            if 0 <= target < tot:
                self.nav.jump(target, QPointF())
            else:
                self.page_input.setText(str(self.nav.currentPage() + 1))
        except ValueError:
            self.page_input.setText(str(self.nav.currentPage() + 1))

    def _zoom_in(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        cur = self.pdf_view.zoomFactor()
        new_factor = min(4.0, cur * 1.2)
        self.pdf_view.setZoomFactor(new_factor)
        self.zoom_lbl.setText(f"{int(new_factor * 100)}%")

    def _zoom_out(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        cur = self.pdf_view.zoomFactor()
        new_factor = max(0.25, cur / 1.2)
        self.pdf_view.setZoomFactor(new_factor)
        self.zoom_lbl.setText(f"{int(new_factor * 100)}%")

    def _fit_to_width(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.zoom_lbl.setText("Ancho")

    def _fit_to_page(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
        self.zoom_lbl.setText("Página")

    def _toggle_page_mode(self):
        if self.pdf_view.pageMode() == QPdfView.PageMode.MultiPage:
            self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
            self.btn_mode.setText("1 Página")
        else:
            self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
            self.btn_mode.setText("Continuo")

    def _save_copy(self):
        if not self._current_file:
            return
        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar copia del PDF",
            os.path.basename(self._current_file),
            "Archivos PDF (*.pdf)",
        )
        if dest:
            try:
                shutil.copy2(self._current_file, dest)
                self.toast_requested.emit(f"Copia guardada con éxito en:\n{os.path.basename(dest)}", "Copia guardada", "success", dest)
            except Exception as e:
                self.toast_requested.emit(f"No se pudo guardar la copia: {e}", "Error", "error", None)

    def _open_in_folder(self):
        if self._current_file:
            open_folder(self._current_file)

    def _choose_and_open_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar documento PDF",
            "",
            "Archivos PDF (*.pdf)",
        )
        if path:
            self.load_pdf(path)

    def _on_back_clicked(self):
        self.back_requested.emit()

    def _on_theme_changed(self):
        self._update_toolbar_style()
        self.file_name_lbl.setStyleSheet(f"color: {C.TEXT};")
        self.file_meta_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        self.page_total_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self.zoom_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self.sep1.setStyleSheet(f"background: {C.BORDER};")
        self.sep2.setStyleSheet(f"background: {C.BORDER};")
        self.sep3.setStyleSheet(f"background: {C.BORDER};")
        self.viewer_container.setStyleSheet(f"""
            QFrame {{
                background: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)
        self.btn_back.setIcon(pixmap("chevronleft", 14, C.TEXT_2))
        self.btn_prev.setIcon(pixmap("chevronleft", 12, C.TEXT))
        self.btn_next.setIcon(pixmap("chevronright", 12, C.TEXT))
        self.btn_zoom_out.setIcon(pixmap("zoom_out", 14, C.TEXT))
        self.btn_zoom_in.setIcon(pixmap("zoom_in", 14, C.TEXT))
        self.btn_save_copy.setIcon(pixmap("download", 13, C.ACCENT))
        self.btn_folder.setIcon(pixmap("folder", 14, C.TEXT_2))
        self.rb_icon.setPixmap(pixmap("checkcircle", 18, C.SUCCESS))

    # Soporte Drag & Drop directo sobre la vista del visor
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for u in urls:
                if u.isLocalFile() and u.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for u in urls:
            path = u.toLocalFile()
            if path.lower().endswith(".pdf"):
                event.acceptProposedAction()
                self.load_pdf(path)
                return
        event.ignore()

    def closeEvent(self, event):
        remove_theme_listener(self._on_theme_changed)
        super().closeEvent(event)
