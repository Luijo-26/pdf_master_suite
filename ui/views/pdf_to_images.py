"""
ui/views/pdf_to_images.py
Herramienta para convertir y extraer las páginas de un documento PDF como
imágenes individuales JPG o PNG en alta resolución de forma 100% local (PySide6.QtPdf).
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton,
    QVBoxLayout, QWidget
)

from pdf_tools import get_pdf_page_count, parse_page_ranges, pdf_to_images
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class PdfToImagesView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="PDF a Imágenes",
            subtitle="Extrae cada página de tu documento como una imagen independiente JPG o PNG en alta definición.",
            icon_name="pdf_image",
            accent_color="#06B6D4",
            button_text="Convertir y elegir carpeta de destino...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self.total_pages: int = 0
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF que deseas convertir a imágenes",
            subtitle="o elígelo desde el explorador de archivos",
            button_text="Seleccionar archivo PDF...",
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            allow_multiple=False,
            compact=False,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_file_selected)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Tarjeta con datos del archivo cargado
        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        fc_layout = QHBoxLayout(self.file_card)
        fc_layout.setContentsMargins(16, 12, 16, 12)
        fc_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 24, "#06B6D4"))
        fc_layout.addWidget(icon_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self.fname_lbl = QLabel()
        self.fname_lbl.setFont(font(10.5, 600))
        self.fname_lbl.setStyleSheet("color: white;")
        info_col.addWidget(self.fname_lbl)

        self.fmeta_lbl = QLabel()
        self.fmeta_lbl.setFont(font(9, 400))
        self.fmeta_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        info_col.addWidget(self.fmeta_lbl)
        fc_layout.addLayout(info_col, 1)

        btn_change = QPushButton("Cambiar archivo")
        btn_change.setObjectName("ghost")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.clicked.connect(self._reset_file)
        fc_layout.addWidget(btn_change)

        self.file_card.hide()
        self.content_layout.addWidget(self.file_card)

        # 3. Opciones de exportación
        self.options_card = QFrame()
        self.options_card.setObjectName("panel")
        oc_layout = QVBoxLayout(self.options_card)
        oc_layout.setContentsMargins(20, 16, 20, 16)
        oc_layout.setSpacing(14)

        lbl_sec = QLabel("CONFIGURACIÓN DE IMÁGENES")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        oc_layout.addWidget(lbl_sec)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Formato (PNG / JPG)
        lbl_fmt = QLabel("Formato de salida:")
        lbl_fmt.setFont(font(9.5, 600))
        lbl_fmt.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_fmt, 0, 0)

        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(16)
        self.rad_png = QRadioButton("PNG (Sin pérdidas, máxima calidad)")
        self.rad_png.setChecked(True)
        self.rad_jpg = QRadioButton("JPG (Comprimido, menor peso)")
        self.fmt_group = QButtonGroup(self)
        self.fmt_group.addButton(self.rad_png)
        self.fmt_group.addButton(self.rad_jpg)
        fmt_row.addWidget(self.rad_png)
        fmt_row.addWidget(self.rad_jpg)
        fmt_row.addStretch()
        grid.addLayout(fmt_row, 0, 1)

        # Resolución DPI
        lbl_dpi = QLabel("Resolución / Calidad:")
        lbl_dpi.setFont(font(9.5, 600))
        lbl_dpi.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_dpi, 1, 0)

        self.combo_dpi = QComboBox()
        self.combo_dpi.addItem("150 DPI — Recomendado (Equilibrio pantalla y peso)", 150)
        self.combo_dpi.addItem("300 DPI — Alta definición (Impresión y detalle máximo)", 300)
        self.combo_dpi.addItem("100 DPI — Compacto (Carga web y miniaturas)", 100)
        grid.addWidget(self.combo_dpi, 1, 1)

        # Rango de páginas
        lbl_range = QLabel("Páginas a extraer:")
        lbl_range.setFont(font(9.5, 600))
        lbl_range.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_range, 2, 0)

        range_col = QVBoxLayout()
        range_col.setSpacing(6)

        self.rad_all_pages = QRadioButton("Todas las páginas")
        self.rad_all_pages.setChecked(True)
        self.rad_custom_pages = QRadioButton("Rango específico:")
        self.range_group = QButtonGroup(self)
        self.range_group.addButton(self.rad_all_pages)
        self.range_group.addButton(self.rad_custom_pages)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Ejemplo: 1-3, 5, 8-10")
        self.range_input.setEnabled(False)

        self.rad_custom_pages.toggled.connect(self.range_input.setEnabled)

        r_sub = QHBoxLayout()
        r_sub.addWidget(self.rad_custom_pages)
        r_sub.addWidget(self.range_input, 1)

        range_col.addWidget(self.rad_all_pages)
        range_col.addLayout(r_sub)
        grid.addLayout(range_col, 2, 1)

        oc_layout.addLayout(grid)
        self.options_card.hide()
        self.content_layout.addWidget(self.options_card)

        self.content_layout.addStretch()

    def _on_file_selected(self, files: List[str]):
        if not files:
            return
        path = files[0]
        try:
            pages = get_pdf_page_count(path)
            size = os.path.getsize(path)
            self.current_pdf = path
            self.total_pages = pages

            self.fname_lbl.setText(os.path.basename(path))
            self.fmeta_lbl.setText(f"{pages} página(s)  •  {format_bytes(size)}")

            self.drop_zone.hide()
            self.file_card.show()
            self.options_card.show()

            self.action_bar.set_button_enabled(True)
            self.action_bar.set_summary(f"Listo para convertir {pages} página(s) a imágenes.")
        except Exception as e:
            self.toast_requested.emit(str(e), "Error al leer PDF", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.total_pages = 0
        self.file_card.hide()
        self.options_card.hide()
        self.drop_zone.show()
        self.action_bar.set_button_enabled(False)
        self.action_bar.set_summary("Selecciona o arrastra un archivo PDF para comenzar")

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            self.toast_requested.emit("Por favor selecciona un archivo PDF primero.", "Archivo requerido", "warning", None)
            return

        fmt = "png" if self.rad_png.isChecked() else "jpg"
        dpi = self.combo_dpi.currentData() or 150

        # Rango
        selected_indices = None
        if self.rad_custom_pages.isChecked():
            range_text = self.range_input.text().strip()
            if not range_text:
                self.toast_requested.emit("Indica el rango de páginas (ej. 1-3, 5).", "Rango vacío", "warning", None)
                return
            try:
                selected_indices = parse_page_ranges(range_text, self.total_pages)
            except Exception as e:
                self.toast_requested.emit(str(e), "Rango inválido", "error", None)
                return

        # Elegir carpeta de destino
        init_dir = os.path.dirname(self.current_pdf)
        dest_folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino para las imágenes",
            init_dir
        )
        if not dest_folder:
            return

        def _task(progress_cb):
            return pdf_to_images(
                pdf_path=self.current_pdf,
                output_folder=dest_folder,
                fmt=fmt,
                dpi=dpi,
                pages_range=selected_indices,
                progress_callback=progress_cb
            )

        def _on_success(generated_files):
            count = len(generated_files)
            msg = f"Se exportaron {count} imagen(es) con éxito en la carpeta seleccionada."
            self.toast_requested.emit(msg, "Conversión completada", "success", dest_folder)
            add_recent(dest_folder, "PDF a Imágenes", "Carpeta")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Renderizando páginas a imágenes en alta definición...",
            with_progress=True,
        )
