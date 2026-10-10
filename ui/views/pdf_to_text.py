"""
ui/views/pdf_to_text.py
Herramienta para extraer todo el texto plano legible de un PDF a un archivo .txt de forma 100% local.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget
)

from pdf_tools import extract_text_from_pdf, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class PdfToTextView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="PDF a Texto (.txt)",
            subtitle="Extrae todo el contenido textual legible de tu documento en un archivo de texto plano limpio.",
            icon_name="text",
            accent_color="#64748B",
            button_text="Extraer texto y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF del cual deseas extraer el texto",
            subtitle="o selecciónalo desde tu computadora",
            button_text="Seleccionar archivo PDF...",
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            allow_multiple=False,
            compact=False,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_file_selected)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Tarjeta con datos del archivo
        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        fc_layout = QHBoxLayout(self.file_card)
        fc_layout.setContentsMargins(16, 12, 16, 12)
        fc_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 24, "#64748B"))
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

        # 3. Opciones
        self.options_panel = QFrame()
        self.options_panel.setObjectName("panel")
        op_layout = QVBoxLayout(self.options_panel)
        op_layout.setContentsMargins(20, 16, 20, 16)
        op_layout.setSpacing(12)

        lbl_sec = QLabel("OPCIONES DE EXTRACCIÓN")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        op_layout.addWidget(lbl_sec)

        self.check_delimiters = QCheckBox("Insertar separadores de página (ej. '--- PÁGINA 1 DE N ---')")
        self.check_delimiters.setChecked(True)
        op_layout.addWidget(self.check_delimiters)

        desc_lbl = QLabel(
            "El archivo resultante contendrá todo el texto extraído en codificación UTF-8 estándar,\n"
            "ideal para procesadores de texto, editores de código o análisis de datos."
        )
        desc_lbl.setFont(font(9, 400))
        desc_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        op_layout.addWidget(desc_lbl)

        self.options_panel.hide()
        self.content_layout.addWidget(self.options_panel)

        self.content_layout.addStretch()

    def _on_file_selected(self, files: List[str]):
        if not files:
            return
        path = files[0]
        try:
            pages = get_pdf_page_count(path)
            size = os.path.getsize(path)
            self.current_pdf = path

            self.fname_lbl.setText(os.path.basename(path))
            self.fmeta_lbl.setText(f"{pages} página(s)  •  {format_bytes(size)}")

            self.drop_zone.hide()
            self.file_card.show()
            self.options_panel.show()

            self.action_bar.set_button_enabled(True)
            self.action_bar.set_summary(f"Listo para extraer texto de {pages} página(s).")
        except Exception as e:
            self.toast_requested.emit(str(e), "Error al leer PDF", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_card.hide()
        self.options_panel.hide()
        self.drop_zone.show()
        self.action_bar.set_button_enabled(False)
        self.action_bar.set_summary("Selecciona o arrastra los archivos para comenzar")

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            self.toast_requested.emit("Por favor selecciona un archivo PDF primero.", "Archivo requerido", "warning", None)
            return

        base, _ = os.path.splitext(self.current_pdf)
        default_out = f"{base}_texto.txt"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar texto extraído como...",
            default_out,
            "Archivos de texto (*.txt)"
        )
        if not out_path:
            return

        sep = self.check_delimiters.isChecked()

        def _task():
            return extract_text_from_pdf(
                input_path=self.current_pdf,
                output_path=out_path,
                add_page_separator=sep
            )

        def _on_success(res):
            chars = res.get("character_count", 0)
            words = res.get("word_count", 0)
            msg = f"Se extrajeron {words} palabras ({chars} caracteres):\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "Texto exportado", "success", out_path)
            add_recent(out_path, "PDF a Texto", "Texto")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Extrayendo texto del documento..."
        )
