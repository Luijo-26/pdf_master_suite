"""
ui/views/rotate_bulk.py
Herramienta para girar todas las páginas, solo pares o solo impares
de un documento PDF en bloque de forma 100% local.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QVBoxLayout, QWidget
)

from pdf_tools import get_pdf_page_count, rotate_pdf_bulk
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class RotateBulkView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Rotar PDF en Bloque",
            subtitle="Gira todas las páginas, solo páginas pares o solo impares a 90° o 180° de un solo clic.",
            icon_name="rotate_bulk",
            accent_color="#8B5CF6",
            button_text="Rotar y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF que deseas rotar en bloque",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#8B5CF6"))
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

        # 3. Opciones de rotación
        self.options_panel = QFrame()
        self.options_panel.setObjectName("panel")
        op_layout = QVBoxLayout(self.options_panel)
        op_layout.setContentsMargins(20, 16, 20, 16)
        op_layout.setSpacing(14)

        lbl_sec = QLabel("PARÁMETROS DE ROTACIÓN")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        op_layout.addWidget(lbl_sec)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Ángulo
        lbl_ang = QLabel("Ángulo de giro:")
        lbl_ang.setFont(font(9.5, 600))
        lbl_ang.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_ang, 0, 0)

        ang_row = QHBoxLayout()
        ang_row.setSpacing(16)
        self.rad_90 = QRadioButton("+90° (Giro a la derecha / Horario)")
        self.rad_90.setChecked(True)
        self.rad_minus_90 = QRadioButton("-90° (Giro a la izquierda)")
        self.rad_180 = QRadioButton("180° (Invertir orientación)")
        self.ang_group = QButtonGroup(self)
        self.ang_group.addButton(self.rad_90)
        self.ang_group.addButton(self.rad_minus_90)
        self.ang_group.addButton(self.rad_180)
        ang_row.addWidget(self.rad_90)
        ang_row.addWidget(self.rad_minus_90)
        ang_row.addWidget(self.rad_180)
        ang_row.addStretch()
        grid.addLayout(ang_row, 0, 1)

        # Filtro de páginas
        lbl_fil = QLabel("Páginas a rotar:")
        lbl_fil.setFont(font(9.5, 600))
        lbl_fil.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_fil, 1, 0)

        fil_row = QHBoxLayout()
        fil_row.setSpacing(16)
        self.rad_all = QRadioButton("Todas las páginas")
        self.rad_all.setChecked(True)
        self.rad_odd = QRadioButton("Solo páginas impares (1, 3, 5...)")
        self.rad_even = QRadioButton("Solo páginas pares (2, 4, 6...)")
        self.fil_group = QButtonGroup(self)
        self.fil_group.addButton(self.rad_all)
        self.fil_group.addButton(self.rad_odd)
        self.fil_group.addButton(self.rad_even)
        fil_row.addWidget(self.rad_all)
        fil_row.addWidget(self.rad_odd)
        fil_row.addWidget(self.rad_even)
        fil_row.addStretch()
        grid.addLayout(fil_row, 1, 1)

        op_layout.addLayout(grid)
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
            self.action_bar.set_summary(f"Listo para rotar {pages} página(s).")
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

        if self.rad_90.isChecked():
            angle = 90
        elif self.rad_minus_90.isChecked():
            angle = 270
        else:
            angle = 180

        if self.rad_odd.isChecked():
            p_filter = "odd"
        elif self.rad_even.isChecked():
            p_filter = "even"
        else:
            p_filter = "all"

        base, ext = os.path.splitext(self.current_pdf)
        default_out = f"{base}_rotado{ext}"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF rotado como...",
            default_out,
            "Archivos PDF (*.pdf)"
        )
        if not out_path:
            return

        def _task():
            return rotate_pdf_bulk(
                input_path=self.current_pdf,
                output_path=out_path,
                rotation=angle,
                page_filter=p_filter
            )

        def _on_success(rotated_count):
            msg = f"Se rotaron {rotated_count} página(s) exitosamente:\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "PDF guardado", "success", out_path)
            add_recent(out_path, "Rotar en Bloque", "PDF")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Aplicando rotación a las páginas seleccionadas..."
        )
