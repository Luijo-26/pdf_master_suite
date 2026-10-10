"""
ui/views/crop.py
Herramienta para recortar márgenes de página o ajustar el cuadro de recorte (CropBox)
de un PDF de forma 100% local.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
)

from pdf_tools import crop_pdf_margins, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class CropView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Recortar PDF",
            subtitle="Elimina bordes en blanco sobrantes ajustando los márgenes de página del documento.",
            icon_name="crop",
            accent_color="#EAB308",
            button_text="Recortar y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF que deseas recortar",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#EAB308"))
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

        # 3. Panel de márgenes
        self.options_panel = QFrame()
        self.options_panel.setObjectName("panel")
        op_layout = QVBoxLayout(self.options_panel)
        op_layout.setContentsMargins(20, 16, 20, 16)
        op_layout.setSpacing(14)

        lbl_sec = QLabel("AJUSTE DE MÁRGENES DE RECORTE (MILÍMETROS)")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        op_layout.addWidget(lbl_sec)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Margen Superior
        lbl_top = QLabel("Superior:")
        lbl_top.setFont(font(9.5, 600))
        lbl_top.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_top, 0, 0)

        self.spin_top = QDoubleSpinBox()
        self.spin_top.setRange(0, 100)
        self.spin_top.setValue(10.0)
        self.spin_top.setSuffix(" mm")
        grid.addWidget(self.spin_top, 0, 1)

        # Margen Inferior
        lbl_bottom = QLabel("Inferior:")
        lbl_bottom.setFont(font(9.5, 600))
        lbl_bottom.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_bottom, 0, 2)

        self.spin_bottom = QDoubleSpinBox()
        self.spin_bottom.setRange(0, 100)
        self.spin_bottom.setValue(10.0)
        self.spin_bottom.setSuffix(" mm")
        grid.addWidget(self.spin_bottom, 0, 3)

        # Margen Izquierdo
        lbl_left = QLabel("Izquierdo:")
        lbl_left.setFont(font(9.5, 600))
        lbl_left.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_left, 1, 0)

        self.spin_left = QDoubleSpinBox()
        self.spin_left.setRange(0, 100)
        self.spin_left.setValue(10.0)
        self.spin_left.setSuffix(" mm")
        grid.addWidget(self.spin_left, 1, 1)

        # Margen Derecho
        lbl_right = QLabel("Derecho:")
        lbl_right.setFont(font(9.5, 600))
        lbl_right.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_right, 1, 2)

        self.spin_right = QDoubleSpinBox()
        self.spin_right.setRange(0, 100)
        self.spin_right.setValue(10.0)
        self.spin_right.setSuffix(" mm")
        grid.addWidget(self.spin_right, 1, 3)

        op_layout.addLayout(grid)

        # Botones de preajuste rápido
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)
        lbl_pre = QLabel("Ajustes rápidos:")
        lbl_pre.setFont(font(9, 400))
        lbl_pre.setStyleSheet(f"color: {C.TEXT_3};")
        presets_row.addWidget(lbl_pre)

        for mm in (5, 10, 15, 20):
            btn_p = QPushButton(f"{mm} mm uniforme")
            btn_p.setObjectName("chip")
            btn_p.setCursor(Qt.PointingHandCursor)
            btn_p.clicked.connect(lambda _, val=mm: self._apply_uniform(val))
            presets_row.addWidget(btn_p)

        presets_row.addStretch()
        op_layout.addLayout(presets_row)

        self.options_panel.hide()
        self.content_layout.addWidget(self.options_panel)

        self.content_layout.addStretch()

    def _apply_uniform(self, mm: float):
        self.spin_top.setValue(mm)
        self.spin_bottom.setValue(mm)
        self.spin_left.setValue(mm)
        self.spin_right.setValue(mm)

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
            self.action_bar.set_summary(f"Listo para recortar márgenes en {pages} página(s).")
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

        # 1 mm ≈ 2.83465 pt
        mm_to_pt = 72.0 / 25.4
        l_pt = self.spin_left.value() * mm_to_pt
        r_pt = self.spin_right.value() * mm_to_pt
        t_pt = self.spin_top.value() * mm_to_pt
        b_pt = self.spin_bottom.value() * mm_to_pt

        base, ext = os.path.splitext(self.current_pdf)
        default_out = f"{base}_recortado{ext}"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF recortado como...",
            default_out,
            "Archivos PDF (*.pdf)"
        )
        if not out_path:
            return

        def _task():
            return crop_pdf_margins(
                input_path=self.current_pdf,
                output_path=out_path,
                left_pt=l_pt,
                right_pt=r_pt,
                top_pt=t_pt,
                bottom_pt=b_pt
            )

        def _on_success(pages):
            msg = f"Se recortaron {pages} página(s) exitosamente:\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "PDF guardado", "success", out_path)
            add_recent(out_path, "Recortar PDF", "PDF")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Ajustando cuadro de recorte del PDF..."
        )
