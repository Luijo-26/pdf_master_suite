"""
ui/views/excel.py
Herramienta para convertir hojas de cálculo de Microsoft Excel (.xlsx, .xls) a PDF
por lotes o de forma individual de forma 100% local en Windows.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QVBoxLayout, QWidget
)

from pdf_tools import convert_excel_batch
from ui.components.drop_zone import DropZone
from ui.components.file_list import FileList
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, rgba
from ui.views.base_tool import BaseToolView

EXCEL_EXTS = [".xlsx", ".xls"]
EXCEL_FILTER = "Libros de Excel (*.xlsx *.xls)"


class ExcelView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Excel a PDF",
            subtitle="Convierte hojas de cálculo y libros .xlsx/.xls a PDF preservando formato de celdas mediante la API de Office.",
            icon_name="excel",
            accent_color="#10B981",
            button_text="Iniciar conversión a PDF...",
            parent=parent,
        )
        self.custom_output_dir: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltar
        self.drop_zone = DropZone(
            title="Arrastra libros de Excel (.xlsx, .xls) aquí",
            subtitle="Soporta conversión individual o por lotes de múltiples hojas de cálculo",
            button_text="+ Agregar archivos Excel...",
            allowed_extensions=EXCEL_EXTS,
            file_filter=EXCEL_FILTER,
            allow_multiple=True,
            compact=True,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_files_added)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Lista de documentos
        self.file_list = FileList(
            allowed_extensions=EXCEL_EXTS,
            file_filter=EXCEL_FILTER,
            add_button_text="+ Agregar archivos Excel",
            parent=self,
        )
        self.file_list.files_changed.connect(self._on_list_changed)
        self.content_layout.addWidget(self.file_list, 1)

        # 3. Opciones de destino
        self.dest_card = QFrame()
        self.dest_card.setObjectName("panel")
        dc_layout = QVBoxLayout(self.dest_card)
        dc_layout.setContentsMargins(18, 12, 18, 12)
        dc_layout.setSpacing(8)

        lbl_dest = QLabel("DESTINO DE LOS ARCHIVOS PDF GENERADOS")
        lbl_dest.setProperty("role", "section")
        lbl_dest.setFont(font(8.5, 700))
        dc_layout.addWidget(lbl_dest)

        self.radio_same = QRadioButton("Guardar en la misma carpeta que cada archivo Excel original")
        self.radio_same.setFont(font(9.5, 500))
        self.radio_same.setChecked(True)
        self.radio_same.toggled.connect(self._on_dest_mode_changed)
        dc_layout.addWidget(self.radio_same)

        row_custom = QHBoxLayout()
        row_custom.setSpacing(8)
        self.radio_custom = QRadioButton("Guardar todos en una carpeta específica:")
        self.radio_custom.setFont(font(9.5, 500))
        self.radio_custom.toggled.connect(self._on_dest_mode_changed)
        row_custom.addWidget(self.radio_custom)

        self.dir_entry = QLineEdit()
        self.dir_entry.setPlaceholderText("Selecciona una carpeta destino...")
        self.dir_entry.setEnabled(False)
        row_custom.addWidget(self.dir_entry, 1)

        self.btn_browse_dir = QPushButton("Examinar...")
        self.btn_browse_dir.setIcon(pixmap("folder", 13, C.TEXT))
        self.btn_browse_dir.setCursor(Qt.PointingHandCursor)
        self.btn_browse_dir.setEnabled(False)
        self.btn_browse_dir.clicked.connect(self._on_browse_dest_dir)
        row_custom.addWidget(self.btn_browse_dir)

        dc_layout.addLayout(row_custom)
        self.content_layout.addWidget(self.dest_card)

        self._update_state()

    def _on_dest_mode_changed(self):
        is_custom = self.radio_custom.isChecked()
        self.dir_entry.setEnabled(is_custom)
        self.btn_browse_dir.setEnabled(is_custom)

    def _on_browse_dest_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino para los PDFs")
        if folder:
            self.custom_output_dir = folder
            self.dir_entry.setText(folder)

    def _on_files_added(self, files: List[str]):
        self.file_list.add_files(files)

    def _on_list_changed(self, files: List[str]):
        self._update_state()

    def _update_state(self):
        count = self.file_list.count()
        has_files = count > 0

        self.drop_zone.setVisible(not has_files)
        self.file_list.setVisible(has_files)
        self.dest_card.setVisible(has_files)
        self.action_bar.set_button_enabled(has_files)

        if count == 0:
            self.action_bar.set_summary("Selecciona o arrastra libros de Excel para comenzar")
        elif count == 1:
            self.action_bar.set_summary("1 archivo Excel listo para convertir a PDF")
        else:
            self.action_bar.set_summary(f"{count} archivos Excel listos para convertir en lote")

    def on_action_execute(self):
        files = self.file_list.get_files()
        if not files:
            self.toast_requested.emit("Agrega al menos un archivo Excel para convertir.", "Lista vacía", "warning", None)
            return

        out_dir: Optional[str] = None
        if self.radio_custom.isChecked():
            if not self.custom_output_dir or not os.path.exists(self.custom_output_dir):
                self.toast_requested.emit("Por favor selecciona una carpeta de destino válida.", "Carpeta requerida", "warning", None)
                return
            out_dir = self.custom_output_dir

        total_files = len(files)

        def _task(progress_cb):
            return convert_excel_batch(
                excel_paths=files,
                output_dir=out_dir,
                progress_callback=progress_cb
            )

        def _on_success(converted_list):
            msg = f"Se convirtieron {len(converted_list)} archivo(s) Excel a PDF exitosamente."
            last_file = converted_list[-1] if converted_list else None
            self.toast_requested.emit(msg, "Conversión completada", "success", last_file)
            for f in converted_list:
                add_recent(f, "Excel a PDF", "PDF")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg=f"Iniciando conversión de {total_files} libro(s) de Excel...",
            with_progress=True,
            with_items=True,
        )
