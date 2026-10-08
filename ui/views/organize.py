"""
ui/views/organize.py
Herramienta para organizar, rotar (+90°, -90°, 180°) y eliminar páginas de un PDF
con vista previa visual en miniaturas reales mediante QPdfDocument.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget
)

from pdf_tools import reorganize_pdf
from ui.components.drop_zone import DropZone
from ui.components.page_grid import PageGrid
from ui.icons import pixmap
from ui.theme import C, font, format_bytes
from ui.views.base_tool import BaseToolView


class OrganizeView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Organizar y Rotar páginas",
            subtitle="Gira, reordena o elimina páginas individuales con vista previa interactiva en miniatura.",
            icon_name="grid",
            accent_color="#F59E0B",
            button_text="Guardar PDF organizado como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltar PDF inicial
        self.drop_zone = DropZone(
            title="Arrastra el PDF para organizar sus páginas",
            subtitle="o haz clic para examinarlo en tu equipo",
            button_text="Cargar archivo PDF...",
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            allow_multiple=False,
            compact=False,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_file_selected)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Barra de archivo cargado
        self.file_bar = QFrame()
        self.file_bar.setObjectName("card")
        fb_layout = QHBoxLayout(self.file_bar)
        fb_layout.setContentsMargins(14, 8, 14, 8)
        fb_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 20, "#F59E0B"))
        fb_layout.addWidget(icon_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        self.fname_lbl = QLabel()
        self.fname_lbl.setFont(font(10, 600))
        self.fname_lbl.setStyleSheet("color: white;")
        info_col.addWidget(self.fname_lbl)

        self.fmeta_lbl = QLabel()
        self.fmeta_lbl.setFont(font(8.5, 400))
        self.fmeta_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        info_col.addWidget(self.fmeta_lbl)
        fb_layout.addLayout(info_col, 1)

        btn_change = QPushButton("Cambiar PDF")
        btn_change.setObjectName("ghost")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.clicked.connect(self._reset_file)
        fb_layout.addWidget(btn_change)

        self.file_bar.hide()
        self.content_layout.addWidget(self.file_bar)

        # 3. Cuadrícula de páginas
        self.page_grid = PageGrid(self)
        self.page_grid.pages_changed.connect(self._on_pages_changed)
        self.page_grid.hide()
        self.content_layout.addWidget(self.page_grid, 1)

    def add_initial_files(self, files: List[str]):
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self._on_file_selected([pdf_files[0]])

    def _on_file_selected(self, files: List[str]):
        if not files:
            return
        path = os.path.normpath(files[0])
        self.current_pdf = path

        self.fname_lbl.setText(os.path.basename(path))
        sz = format_bytes(os.path.getsize(path)) if os.path.exists(path) else ""
        self.fmeta_lbl.setText(f"{sz}  •  {os.path.dirname(path)}")

        self.drop_zone.hide()
        self.file_bar.show()
        self.page_grid.show()

        self.page_grid.load_pdf(path)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_bar.hide()
        self.page_grid.hide()
        self.drop_zone.show()
        self.action_bar.set_summary("Carga un documento PDF para organizar sus páginas")
        self.action_bar.set_enabled(False)

    def _on_pages_changed(self):
        count = self.page_grid.count()
        if count == 0:
            self.action_bar.set_summary("No quedan páginas en el documento", is_warning=True)
            self.action_bar.set_enabled(False)
        else:
            self.action_bar.set_summary(f"{count} páginas listas para exportar")
            self.action_bar.set_enabled(True)

    def on_action_execute(self):
        if not self.current_pdf or self.page_grid.count() == 0:
            return

        base_name = os.path.splitext(os.path.basename(self.current_pdf))[0]
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF organizado como",
            os.path.join(os.path.dirname(self.current_pdf), f"{base_name}_organizado.pdf"),
            "Archivos PDF (*.pdf)",
        )
        if not out_path:
            return

        config = self.page_grid.get_export_config()
        src_file = self.current_pdf

        def task():
            return reorganize_pdf(src_file, config, out_path)

        def on_done(count):
            self.notify_success(
                f"PDF reorganizado guardado con éxito ({count} páginas):\n{os.path.basename(out_path)}",
                file_path=out_path,
                tool_name="Organizar páginas",
            )

        self.run_task(task, on_success=on_done, initial_msg="Generando nuevo documento organizado...")
