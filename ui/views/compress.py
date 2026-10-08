"""
ui/views/compress.py
Herramienta para optimizar y reducir el tamaño de documentos PDF
eliminando redundancias y recomprimiendo flujos de contenido con pypdf.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget
)

from pdf_tools import compress_pdf, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class CompressView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Comprimir PDF",
            subtitle="Reduce el peso del archivo optimizando flujos de contenido y eliminando objetos duplicados.",
            icon_name="shrink",
            accent_color="#10B981",
            button_text="Comprimir y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltar PDF
        self.drop_zone = DropZone(
            title="Arrastra el PDF que deseas comprimir",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#10B981"))
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

        # 3. Panel de comparativa / resultados
        self.result_card = QFrame()
        self.result_card.setObjectName("panel")
        rc_layout = QVBoxLayout(self.result_card)
        rc_layout.setContentsMargins(20, 18, 20, 18)
        rc_layout.setSpacing(12)

        lbl_sec = QLabel("ESTADÍSTICAS DE COMPRESIÓN")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        rc_layout.addWidget(lbl_sec)

        self.result_lbl = QLabel(
            "Haz clic en el botón inferior para elegir dónde guardar el PDF optimizado.\n"
            "El proceso analiza y recomprime los flujos de contenido sin perder calidad de lectura."
        )
        self.result_lbl.setFont(font(9.5, 400))
        self.result_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self.result_lbl.setWordWrap(True)
        rc_layout.addWidget(self.result_lbl)

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(16)

        # Tarjetas de métrica
        self.orig_box = self._create_stat_box("Tamaño original", "-")
        self.comp_box = self._create_stat_box("Tamaño final", "-")
        self.save_box = self._create_stat_box("Reducción obtenida", "-", is_accent=True)

        self.stats_row.addWidget(self.orig_box)
        self.stats_row.addWidget(self.comp_box)
        self.stats_row.addWidget(self.save_box)
        rc_layout.addLayout(self.stats_row)

        self.result_card.hide()
        self.content_layout.addWidget(self.result_card)
        self.content_layout.addStretch()

    def _create_stat_box(self, title: str, value: str, is_accent: bool = False) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"""
            background: {C.INPUT};
            border: 1px solid {C.BORDER};
            border-radius: 10px;
            padding: 10px;
        """)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)

        t_lbl = QLabel(title)
        t_lbl.setFont(font(8.5, 500))
        t_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        lay.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setObjectName("val")
        v_lbl.setFont(font(13, 700))
        v_lbl.setStyleSheet(f"color: {C.SUCCESS if is_accent else 'white'};")
        lay.addWidget(v_lbl)
        return box

    def _set_box_value(self, box: QFrame, value: str):
        lbl = box.findChild(QLabel, "val")
        if lbl:
            lbl.setText(value)

    def add_initial_files(self, files: List[str]):
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self._on_file_selected([pdf_files[0]])

    def _on_file_selected(self, files: List[str]):
        if not files:
            return
        path = os.path.normpath(files[0])
        try:
            pages = get_pdf_page_count(path)
            self.current_pdf = path
            sz = os.path.getsize(path)

            self.fname_lbl.setText(os.path.basename(path))
            self.fmeta_lbl.setText(f"{format_bytes(sz)}  •  {pages} páginas  •  {os.path.dirname(path)}")

            self._set_box_value(self.orig_box, format_bytes(sz))
            self._set_box_value(self.comp_box, "-")
            self._set_box_value(self.save_box, "-")

            self.drop_zone.hide()
            self.file_card.show()
            self.result_card.show()

            self.action_bar.set_summary(f"Listo para optimizar ({format_bytes(sz)})")
            self.action_bar.set_enabled(True)
        except Exception as exc:
            self.toast_requested.emit(f"No se pudo cargar el archivo: {str(exc)}", "Error", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_card.hide()
        self.result_card.hide()
        self.drop_zone.show()
        self.action_bar.set_summary("Selecciona un PDF para comprimir")
        self.action_bar.set_enabled(False)

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            return

        base_name = os.path.splitext(os.path.basename(self.current_pdf))[0]
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF comprimido como",
            os.path.join(os.path.dirname(self.current_pdf), f"{base_name}_comprimido.pdf"),
            "Archivos PDF (*.pdf)",
        )
        if not out_path:
            return

        src_file = self.current_pdf

        def task():
            return compress_pdf(src_file, out_path)

        def on_done(stats: dict):
            orig_str = format_bytes(stats["original_size"])
            new_str = format_bytes(stats["compressed_size"])
            pct = stats["reduction_percent"]
            saved_str = format_bytes(stats["saved_bytes"])

            self._set_box_value(self.orig_box, orig_str)
            self._set_box_value(self.comp_box, new_str)
            self._set_box_value(self.save_box, f"-{pct}% ({saved_str})")

            self.result_lbl.setText(
                f"✓ Compresión finalizada con éxito. Se redujo el archivo en un {pct}%, "
                f"ahorrando {saved_str} de espacio en disco."
            )
            self.result_lbl.setStyleSheet(f"color: {C.SUCCESS};")

            self.notify_success(
                f"PDF comprimido (-{pct}%):\n{os.path.basename(out_path)}",
                file_path=out_path,
                tool_name="Comprimir PDF",
            )

        self.run_task(task, on_success=on_done, initial_msg="Optimizando y recomprimiendo PDF...")
