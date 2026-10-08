"""
ui/views/word.py
Herramienta para convertir documentos Microsoft Word (.docx, .doc) a PDF
por lotes o de forma individual, preservando formatos y fuentes nativas.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QVBoxLayout, QWidget
)

from pdf_tools import convert_docx_batch, convert_docx_to_pdf
from ui.components.drop_zone import DropZone
from ui.components.file_list import FileList
from ui.icons import pixmap
from ui.theme import C, font, rgba
from ui.views.base_tool import BaseToolView

WORD_EXTS = [".docx", ".doc"]
WORD_FILTER = "Documentos de Word (*.docx *.doc)"


class WordView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Word a PDF",
            subtitle="Convierte documentos .docx y .doc a PDF preservando tipografías y tablas mediante la API de Office.",
            icon_name="filetext",
            accent_color="#3B82F6",
            button_text="Iniciar conversión a PDF...",
            parent=parent,
        )
        self.custom_output_dir: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltar
        self.drop_zone = DropZone(
            title="Arrastra archivos de Word (.docx) aquí",
            subtitle="Soporta conversión individual o por lotes de varios documentos a la vez",
            button_text="+ Agregar documentos Word...",
            allowed_extensions=WORD_EXTS,
            file_filter=WORD_FILTER,
            allow_multiple=True,
            compact=True,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_files_added)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Lista de documentos
        self.file_list = FileList(
            allowed_extensions=WORD_EXTS,
            file_filter=WORD_FILTER,
            add_button_text="+ Agregar documentos Word",
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

        self.radio_same = QRadioButton("Guardar en la misma carpeta que cada archivo Word original")
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

    def add_initial_files(self, files: List[str]):
        w_files = [f for f in files if any(f.lower().endswith(ext) for ext in WORD_EXTS)]
        if w_files:
            self.file_list.add_files(w_files)

    def _on_files_added(self, files: List[str]):
        self.file_list.add_files(files)

    def _on_list_changed(self, files: List[str]):
        total = len(files)
        if total == 0:
            self.action_bar.set_summary("Agrega documentos de Word para convertirlos a PDF")
            self.action_bar.set_enabled(False)
        elif total == 1:
            self.action_bar.set_summary("1 documento Word listo para convertir")
            self.action_bar.set_button_text("Guardar PDF como...")
            self.action_bar.set_enabled(True)
        else:
            self.action_bar.set_summary(f"{total} documentos Word listos para convertir en lote")
            self.action_bar.set_button_text(f"Convertir {total} documentos...")
            self.action_bar.set_enabled(True)

    def _on_dest_mode_changed(self):
        is_custom = self.radio_custom.isChecked()
        self.dir_entry.setEnabled(is_custom)
        self.btn_browse_dir.setEnabled(is_custom)

    def _on_browse_dest_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta destino para los PDFs")
        if folder:
            self.custom_output_dir = os.path.normpath(folder)
            self.dir_entry.setText(self.custom_output_dir)

    def on_action_execute(self):
        files = self.file_list.get_files()
        if not files:
            return

        # Si es un solo archivo y el usuario desea guardarlo con nombre personalizado:
        if len(files) == 1 and self.radio_same.isChecked():
            src_file = files[0]
            base_name = os.path.splitext(os.path.basename(src_file))[0]
            out_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar documento PDF convertido como",
                os.path.join(os.path.dirname(src_file), f"{base_name}.pdf"),
                "Archivos PDF (*.pdf)",
            )
            if not out_path:
                return

            def single_task():
                convert_docx_to_pdf(src_file, out_path)
                return [out_path]

            def on_done(results):
                self.notify_success(
                    f"Documento convertido a PDF:\n{os.path.basename(out_path)}",
                    file_path=out_path,
                    tool_name="Word a PDF",
                )

            self.run_task(single_task, on_success=on_done, initial_msg="Convirtiendo con Microsoft Word...")
            return

        # Lote de archivos o carpeta específica
        target_dir = None
        if self.radio_custom.isChecked():
            target_dir = self.dir_entry.text().strip()
            if not target_dir or not os.path.exists(target_dir):
                target_dir = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta destino para los PDFs")
                if not target_dir:
                    return
                self.dir_entry.setText(target_dir)

        docs = list(files)

        def batch_task(progress_callback=None):
            def _prog(cur, tot, path):
                if progress_callback:
                    progress_callback(cur, tot, f"Convirtiendo [{cur}/{tot}]: {os.path.basename(path)}")
            return convert_docx_batch(docs, output_dir=target_dir, progress_callback=_prog)

        def on_batch_done(results):
            first = results[0] if results else None
            self.notify_success(
                f"Conversión finalizada con éxito: {len(results)} archivo(s) convertidos a PDF.",
                file_path=first,
                tool_name="Word a PDF",
            )

        self.run_task(
            batch_task,
            on_success=on_batch_done,
            initial_msg="Iniciando conversión en segundo plano...",
            with_progress=True,
        )
