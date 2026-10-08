"""
ui/views/images.py
Herramienta para convertir y compilar imágenes (JPG, PNG, WEBP, BMP)
en un único documento PDF con orden personalizable y corrección de orientación EXIF.
"""

import os
from typing import List, Optional

from PySide6.QtWidgets import QFileDialog, QWidget

from pdf_tools import images_to_pdf
from ui.components.drop_zone import DropZone
from ui.components.file_list import FileList
from ui.views.base_tool import BaseToolView

IMG_EXTS = [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
IMG_FILTER = "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp)"


class ImagesView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Imágenes a PDF",
            subtitle="Compila una o múltiples imágenes (JPG, PNG, WEBP, BMP) en páginas de un documento PDF.",
            icon_name="image",
            accent_color="#EC4899",
            button_text="Compilar imágenes y guardar como...",
            parent=parent,
        )
        self._init_content()

    def _init_content(self):
        self.drop_zone = DropZone(
            title="Arrastra tus imágenes aquí",
            subtitle="Soporta JPG, PNG, WEBP y BMP. Cada imagen será una página del PDF.",
            button_text="+ Agregar imágenes...",
            allowed_extensions=IMG_EXTS,
            file_filter=IMG_FILTER,
            allow_multiple=True,
            compact=True,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_files_added)
        self.content_layout.addWidget(self.drop_zone)

        self.file_list = FileList(
            allowed_extensions=IMG_EXTS,
            file_filter=IMG_FILTER,
            add_button_text="+ Agregar imágenes",
            parent=self,
        )
        self.file_list.files_changed.connect(self._on_list_changed)
        self.content_layout.addWidget(self.file_list, 1)

    def add_initial_files(self, files: List[str]):
        img_files = [f for f in files if any(f.lower().endswith(ext) for ext in IMG_EXTS)]
        if img_files:
            self.file_list.add_files(img_files)

    def _on_files_added(self, files: List[str]):
        self.file_list.add_files(files)

    def _on_list_changed(self, files: List[str]):
        total = len(files)
        if total == 0:
            self.action_bar.set_summary("Agrega al menos una imagen para crear el PDF")
            self.action_bar.set_enabled(False)
        else:
            self.action_bar.set_summary(f"{total} imagen(es) listas para compilar")
            self.action_bar.set_enabled(True)

    def on_action_execute(self):
        files = self.file_list.get_files()
        if not files:
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF compilado como",
            os.path.join(os.path.dirname(files[0]), "imagenes_compiladas.pdf"),
            "Archivos PDF (*.pdf)",
        )
        if not out_path:
            return

        def task():
            return images_to_pdf(files, out_path)

        def on_done(count):
            self.notify_success(
                f"PDF generado con éxito ({count} páginas):\n{os.path.basename(out_path)}",
                file_path=out_path,
                tool_name="Imágenes a PDF",
            )

        self.run_task(task, on_success=on_done, initial_msg="Compilando imágenes a documento PDF...")
