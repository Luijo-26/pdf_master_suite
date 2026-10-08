"""
ui/views/split.py
Herramienta para dividir documentos PDF por rangos o extraer todas las páginas individualmente.
Incluye validación en tiempo real del rango de páginas con feedback inmediato.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QVBoxLayout, QWidget
)

from pdf_tools import (
    get_pdf_page_count, parse_page_ranges, split_pdf_all,
    split_pdf_ranges
)
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class SplitView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Dividir PDF",
            subtitle="Extrae páginas específicas por rangos o genera un archivo PDF individual por cada página.",
            icon_name="scissors",
            accent_color="#14B8A6",
            button_text="Dividir y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self.total_pages: int = 0
        self._init_content()

    def _init_content(self):
        # 1. Zona de selección de archivo
        self.drop_zone = DropZone(
            title="Arrastra el PDF que deseas dividir",
            subtitle="o haz clic en el botón para seleccionarlo",
            button_text="Seleccionar archivo PDF...",
            allowed_extensions=[".pdf"],
            file_filter="Archivos PDF (*.pdf)",
            allow_multiple=False,
            compact=False,
            parent=self,
        )
        self.drop_zone.files_dropped.connect(self._on_file_selected)
        self.content_layout.addWidget(self.drop_zone)

        # 2. Tarjeta con datos del archivo cargado (oculta hasta que haya archivo)
        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        fc_layout = QHBoxLayout(self.file_card)
        fc_layout.setContentsMargins(16, 12, 16, 12)
        fc_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 24, "#14B8A6"))
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

        # 3. Opciones de división
        self.options_panel = QFrame()
        self.options_panel.setObjectName("panel")
        op_layout = QVBoxLayout(self.options_panel)
        op_layout.setContentsMargins(20, 16, 20, 16)
        op_layout.setSpacing(14)

        lbl_opt_title = QLabel("MODALIDAD DE DIVISIÓN")
        lbl_opt_title.setProperty("role", "section")
        lbl_opt_title.setFont(font(8.5, 700))
        op_layout.addWidget(lbl_opt_title)

        # Opción 1: Rangos
        self.radio_ranges = QRadioButton("Extraer páginas seleccionadas o rangos en un nuevo PDF")
        self.radio_ranges.setFont(font(10, 500))
        self.radio_ranges.setChecked(True)
        self.radio_ranges.toggled.connect(self._on_mode_toggled)
        op_layout.addWidget(self.radio_ranges)

        self.range_box = QFrame()
        rb_layout = QVBoxLayout(self.range_box)
        rb_layout.setContentsMargins(28, 2, 0, 8)
        rb_layout.setSpacing(6)

        r_input_row = QHBoxLayout()
        r_input_row.setSpacing(10)
        lbl_r = QLabel("Páginas a extraer:")
        lbl_r.setFont(font(9.5, 500))
        lbl_r.setStyleSheet(f"color: {C.TEXT_2};")
        r_input_row.addWidget(lbl_r)

        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Ej: 1-3, 5, 8-10")
        self.range_input.textChanged.connect(self._validate_ranges)
        r_input_row.addWidget(self.range_input, 1)
        rb_layout.addLayout(r_input_row)

        self.validation_lbl = QLabel("Escribe los números o rangos basados en 1, separados por comas.")
        self.validation_lbl.setFont(font(8.5, 400))
        self.validation_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        rb_layout.addWidget(self.validation_lbl)
        op_layout.addWidget(self.range_box)

        # Opción 2: Todas las páginas
        self.radio_all = QRadioButton("Extraer todas las páginas individualmente (1 archivo por página)")
        self.radio_all.setFont(font(10, 500))
        self.radio_all.toggled.connect(self._on_mode_toggled)
        op_layout.addWidget(self.radio_all)

        self.options_panel.hide()
        self.content_layout.addWidget(self.options_panel)
        self.content_layout.addStretch()

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
            self.total_pages = pages

            self.fname_lbl.setText(os.path.basename(path))
            sz = format_bytes(os.path.getsize(path))
            self.fmeta_lbl.setText(f"{pages} páginas detectadas  •  {sz}  •  {os.path.dirname(path)}")

            self.drop_zone.hide()
            self.file_card.show()
            self.options_panel.show()

            self._validate_ranges()
        except Exception as exc:
            self.toast_requested.emit(f"No se pudo cargar el PDF: {str(exc)}", "Error", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.total_pages = 0
        self.file_card.hide()
        self.options_panel.hide()
        self.drop_zone.show()
        self.action_bar.set_summary("Selecciona un archivo PDF para comenzar")
        self.action_bar.set_enabled(False)

    def _on_mode_toggled(self):
        is_ranges = self.radio_ranges.isChecked()
        self.range_box.setEnabled(is_ranges)
        if is_ranges:
            self.action_bar.set_button_text("Extraer páginas y guardar como...")
            self._validate_ranges()
        else:
            self.action_bar.set_button_text("Guardar páginas en carpeta...")
            self.action_bar.set_summary(f"Se generarán {self.total_pages} archivos individuales en la carpeta destino")
            self.action_bar.set_enabled(True)

    def _validate_ranges(self):
        if not self.radio_ranges.isChecked():
            return
        if not self.current_pdf or self.total_pages == 0:
            self.action_bar.set_enabled(False)
            return

        text = self.range_input.text().strip()
        if not text:
            self.validation_lbl.setText(f"Introduce los rangos a extraer (el documento tiene {self.total_pages} páginas).")
            self.validation_lbl.setStyleSheet(f"color: {C.TEXT_3};")
            self.action_bar.set_summary("Introduce un rango de páginas válido")
            self.action_bar.set_enabled(False)
            return

        try:
            indices = parse_page_ranges(text, self.total_pages)
            count = len(indices)
            self.validation_lbl.setText(f"✓ Rango válido: se extraerán {count} página(s) al nuevo documento.")
            self.validation_lbl.setStyleSheet(f"color: {C.SUCCESS};")
            self.action_bar.set_summary(f"Listo para extraer {count} páginas")
            self.action_bar.set_enabled(True)
        except Exception as exc:
            self.validation_lbl.setText(f"✗ {str(exc)}")
            self.validation_lbl.setStyleSheet(f"color: {C.DANGER};")
            self.action_bar.set_summary("Corrige el rango de páginas", is_warning=True)
            self.action_bar.set_enabled(False)

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            return

        is_ranges = self.radio_ranges.isChecked()
        base_name = os.path.splitext(os.path.basename(self.current_pdf))[0]

        if is_ranges:
            range_str = self.range_input.text().strip()
            out_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar páginas extraídas como",
                os.path.join(os.path.dirname(self.current_pdf), f"{base_name}_extraido.pdf"),
                "Archivos PDF (*.pdf)",
            )
            if not out_path:
                return

            def task():
                return split_pdf_ranges(self.current_pdf, range_str, out_path)

            def on_done(count):
                self.notify_success(
                    f"Se extrajeron {count} páginas en:\n{os.path.basename(out_path)}",
                    file_path=out_path,
                    tool_name="Dividir PDF",
                )

            self.run_task(task, on_success=on_done, initial_msg="Extrayendo páginas del PDF...")

        else:
            out_folder = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta de destino para las páginas",
                os.path.dirname(self.current_pdf),
            )
            if not out_folder:
                return

            def task():
                return split_pdf_all(self.current_pdf, out_folder)

            def on_done(created_files):
                first_file = created_files[0] if created_files else None
                self.notify_success(
                    f"Se generaron {len(created_files)} archivos individuales en:\n{out_folder}",
                    file_path=first_file,
                    tool_name="Dividir PDF",
                )

            self.run_task(task, on_success=on_done, initial_msg="Extrayendo todas las páginas...")
