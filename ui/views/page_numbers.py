"""
ui/views/page_numbers.py
Herramienta para insertar numeración de páginas en documentos PDF con
formato, posición, márgenes y tipografía personalizables de forma 100% local.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget
)

from pdf_tools import add_page_numbers, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class PageNumbersView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Numerar Páginas",
            subtitle="Añade números de página con formato 'Página X de Y', ubicación precisa y opción de omitir portada.",
            icon_name="hash",
            accent_color="#EC4899",
            button_text="Numerar páginas y guardar...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF que deseas numerar",
            subtitle="o elígelo desde el explorador de archivos",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#EC4899"))
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

        # 3. Panel de configuración
        self.config_panel = QFrame()
        self.config_panel.setObjectName("panel")
        cp_layout = QVBoxLayout(self.config_panel)
        cp_layout.setContentsMargins(20, 16, 20, 16)
        cp_layout.setSpacing(14)

        lbl_sec = QLabel("PARÁMETROS DE NUMERACIÓN")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        cp_layout.addWidget(lbl_sec)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Formato de texto
        lbl_fmt = QLabel("Formato de numeración:")
        lbl_fmt.setFont(font(9.5, 600))
        lbl_fmt.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_fmt, 0, 0)

        self.combo_format = QComboBox()
        self.combo_format.addItem("Página {n} de {total}", "Página {n} de {total}")
        self.combo_format.addItem("Pág. {n} / {total}", "Pág. {n} / {total}")
        self.combo_format.addItem("Solo número: {n}", "{n}")
        self.combo_format.addItem("Página {n}", "Página {n}")
        grid.addWidget(self.combo_format, 0, 1)

        # Posición
        lbl_pos = QLabel("Posición en la hoja:")
        lbl_pos.setFont(font(9.5, 600))
        lbl_pos.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_pos, 1, 0)

        self.combo_pos = QComboBox()
        self.combo_pos.addItem("Inferior Centro (Estándar)", "bottom_center")
        self.combo_pos.addItem("Inferior Derecha", "bottom_right")
        self.combo_pos.addItem("Inferior Izquierda", "bottom_left")
        self.combo_pos.addItem("Superior Centro", "top_center")
        self.combo_pos.addItem("Superior Derecha", "top_right")
        self.combo_pos.addItem("Superior Izquierda", "top_left")
        grid.addWidget(self.combo_pos, 1, 1)

        # Omitir portada
        self.check_cover = QCheckBox("Omitir la primera página (no numerar portada)")
        self.check_cover.setChecked(True)
        grid.addWidget(self.check_cover, 2, 0, 1, 2)

        # Número inicial
        lbl_start = QLabel("Comenzar a contar desde:")
        lbl_start.setFont(font(9.5, 600))
        lbl_start.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_start, 3, 0)

        self.spin_start = QSpinBox()
        self.spin_start.setRange(1, 1000)
        self.spin_start.setValue(1)
        grid.addWidget(self.spin_start, 3, 1)

        # Tamaño de texto
        lbl_size = QLabel("Tamaño de fuente (pt):")
        lbl_size.setFont(font(9.5, 600))
        lbl_size.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_size, 4, 0)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(7, 24)
        self.spin_size.setValue(10)
        grid.addWidget(self.spin_size, 4, 1)

        cp_layout.addLayout(grid)
        self.config_panel.hide()
        self.content_layout.addWidget(self.config_panel)

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
            self.config_panel.show()

            self.action_bar.set_button_enabled(True)
            self.action_bar.set_summary(f"Listo para añadir números a {pages} página(s).")
        except Exception as e:
            self.toast_requested.emit(str(e), "Error al leer PDF", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_card.hide()
        self.config_panel.hide()
        self.drop_zone.show()
        self.action_bar.set_button_enabled(False)
        self.action_bar.set_summary("Selecciona o arrastra los archivos para comenzar")

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            self.toast_requested.emit("Por favor selecciona un archivo PDF primero.", "Archivo requerido", "warning", None)
            return

        fmt_str = self.combo_format.currentData()
        pos_val = self.combo_pos.currentData()
        skip_first = 1 if self.check_cover.isChecked() else 0
        start_num = self.spin_start.value()
        f_size = self.spin_size.value()

        base, ext = os.path.splitext(self.current_pdf)
        default_out = f"{base}_numerado{ext}"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF numerado como...",
            default_out,
            "Archivos PDF (*.pdf)"
        )
        if not out_path:
            return

        def _task():
            add_page_numbers(
                input_path=self.current_pdf,
                output_path=out_path,
                format_str=fmt_str,
                position=pos_val,
                font_size=f_size,
                start_page_num=start_num,
                skip_first_pages=skip_first,
                margin_pt=34.0,
            )

        def _on_success(_):
            msg = f"Numeración aplicada con éxito:\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "PDF guardado", "success", out_path)
            add_recent(out_path, "Numerar Páginas", "PDF")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Generando e insertando números de página..."
        )
