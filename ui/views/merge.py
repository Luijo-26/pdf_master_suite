"""
ui/views/merge.py
Herramienta para combinar múltiples archivos PDF en un único documento.
"""

import os
from typing import List, Optional

from PySide6.QtWidgets import QFileDialog, QWidget

from pdf_tools import get_pdf_page_count, merge_pdfs
from ui.components.drop_zone import DropZone
from ui.components.file_list import FileList
from ui.views.base_tool import BaseToolView


class MergeView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Unir PDFs",
            subtitle="Combina dos o más documentos PDF en un solo archivo en el orden que decidas.",
            icon_name="merge",
            accent_color="#7C6CFF",
            button_text="Unir PDFs y guardar como...",
            parent=parent,
        )
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltar compacta
        self.drop_zone = DropZone(
            title="Arrastra archivos PDF aquí",
            subtitle="o agrégalos para combinarlos en orden de arriba a abajo",
            button_text="+ Agregar PDFs...",
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            allow_multiple=True,
            compact=True,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_files_added)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Lista interactiva
        self.file_list = FileList(
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            add_button_text="+ Agregar PDFs",
            extra_info_provider=self._get_pdf_info,
            parent=self,
        )
        self.file_list.files_changed.connect(self._on_list_changed)
        self.content_layout.addWidget(self.file_list, 1)

    def _get_pdf_info(self, path: str) -> str:
        try:
            pages = get_pdf_page_count(path)
            return f"{pages} pág(s)"
        except Exception:
            return ""

    def add_initial_files(self, files: List[str]):
        """Añade archivos pasados desde el inicio u otra vista."""
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self.file_list.add_files(pdf_files)

    def _on_files_added(self, files: List[str]):
        self.file_list.add_files(files)

    def _on_list_changed(self, files: List[str]):
        total = len(files)
        if total == 0:
            self.action_bar.set_summary("Agrega al menos 2 archivos PDF para unirlos")
            self.action_bar.set_enabled(False)
        elif total == 1:
            self.action_bar.set_summary("1 archivo en la lista (se necesitan al menos 2)", is_warning=True)
            self.action_bar.set_enabled(False)
        else:
            self.action_bar.set_summary(f"{total} archivos listos para combinar")
            self.action_bar.set_enabled(True)

    def on_action_execute(self):
        files = self.file_list.get_files()
        if len(files) < 2:
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF combinado como",
            os.path.join(os.path.dirname(files[0]), "documento_unido.pdf"),
            "Archivos PDF (*.pdf)",
        )
        if not out_path:
            return

        def task():
            merge_pdfs(files, out_path)
            return out_path

        def on_done(saved_file):
            self.notify_success(
                f"PDF combinado guardado con éxito:\n{os.path.basename(saved_file)}",
                file_path=saved_file,
                tool_name="Unir PDFs",
            )

        self.run_task(task, on_success=on_done, initial_msg="Combinando documentos PDF...")
