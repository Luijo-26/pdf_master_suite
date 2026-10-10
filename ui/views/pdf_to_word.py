"""
ui/views/pdf_to_word.py
Herramienta para convertir documentos PDF a Microsoft Word (.docx) editable
de forma 100% local con pypdf y python-docx.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget
)

from pdf_tools import convert_pdf_to_word, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class PdfToWordView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="PDF a Word (.docx)",
            subtitle="Convierte el contenido y texto de un PDF en un documento Word editable preservando estructura y saltos de página.",
            icon_name="filetext",
            accent_color="#2563EB",
            button_text="Convertir a Word y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF que deseas convertir a Word",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#2563EB"))
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

        # 3. Panel informativo
        self.info_panel = QFrame()
        self.info_panel.setObjectName("panel")
        ip_layout = QVBoxLayout(self.info_panel)
        ip_layout.setContentsMargins(20, 16, 20, 16)
        ip_layout.setSpacing(10)

        lbl_sec = QLabel("INFORMACIÓN DE CONVERSIÓN")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        ip_layout.addWidget(lbl_sec)

        info_lbl = QLabel(
            "El proceso analiza el flujo de texto de cada página del PDF y genera un documento\n"
            "Microsoft Word (.docx) nativo con párrafos editables y saltos de página correspondientes.\n"
            "Todo el proceso se realiza 100% de forma local en tu computadora sin enviar información a la nube."
        )
        info_lbl.setFont(font(9.5, 400))
        info_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        info_lbl.setWordWrap(True)
        ip_layout.addWidget(info_lbl)

        self.info_panel.hide()
        self.content_layout.addWidget(self.info_panel)

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
            self.info_panel.show()

            self.action_bar.set_button_enabled(True)
            self.action_bar.set_summary(f"Listo para convertir {pages} página(s) a Word (.docx).")
        except Exception as e:
            self.toast_requested.emit(str(e), "Error al leer PDF", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_card.hide()
        self.info_panel.hide()
        self.drop_zone.show()
        self.action_bar.set_button_enabled(False)
        self.action_bar.set_summary("Selecciona o arrastra los archivos para comenzar")

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            self.toast_requested.emit("Por favor selecciona un archivo PDF primero.", "Archivo requerido", "warning", None)
            return

        base, _ = os.path.splitext(self.current_pdf)
        default_out = f"{base}.docx"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar documento Word como...",
            default_out,
            "Documentos de Word (*.docx)"
        )
        if not out_path:
            return

        def _task():
            return convert_pdf_to_word(self.current_pdf, out_path)

        def _on_success(pages):
            msg = f"Se convirtió a Word ({pages} páginas) exitosamente:\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "Conversión completada", "success", out_path)
            add_recent(out_path, "PDF a Word", "Word")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Extrayendo texto y estructurando documento Word..."
        )
