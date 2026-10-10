"""
ui/views/watermark.py
Herramienta para añadir marcas de agua personalizadas (texto o logotipo/imagen)
a documentos PDF de forma 100% local con ReportLab y pypdf.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton,
    QSlider, QSpinBox, QVBoxLayout, QWidget
)

from pdf_tools import add_watermark, get_pdf_page_count
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.recents import add_recent
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class WatermarkView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Marca de Agua",
            subtitle="Inserta sellos de texto (ej. Confidencial, Copia) o logotipos con opacidad y rotación regulables.",
            icon_name="stamp",
            accent_color="#F43F5E",
            button_text="Aplicar marca de agua y guardar...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self.current_image_path: str = ""
        self._init_content()

    def _init_content(self):
        # 1. Zona de soltado
        self.drop_zone = DropZone(
            title="Arrastra el PDF al que deseas añadir marca de agua",
            subtitle="o elígelo desde tus carpetas",
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
        icon_lbl.setPixmap(pixmap("file", 24, "#F43F5E"))
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

        lbl_sec = QLabel("CONFIGURACIÓN DE LA MARCA DE AGUA")
        lbl_sec.setProperty("role", "section")
        lbl_sec.setFont(font(8.5, 700))
        cp_layout.addWidget(lbl_sec)

        # Selector de tipo (Texto / Imagen)
        type_row = QHBoxLayout()
        type_row.setSpacing(16)
        self.rad_type_text = QRadioButton("Texto personalizado")
        self.rad_type_text.setChecked(True)
        self.rad_type_img = QRadioButton("Imagen o Logotipo (PNG / JPG)")
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.rad_type_text)
        self.type_group.addButton(self.rad_type_img)
        type_row.addWidget(self.rad_type_text)
        type_row.addWidget(self.rad_type_img)
        type_row.addStretch()
        cp_layout.addLayout(type_row)

        self.rad_type_text.toggled.connect(self._toggle_watermark_type)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Controles de texto
        self.lbl_text = QLabel("Texto de la marca:")
        self.lbl_text.setFont(font(9.5, 600))
        self.lbl_text.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(self.lbl_text, 0, 0)

        self.input_text = QLineEdit("CONFIDENCIAL")
        self.input_text.setFont(font(10, 500))
        grid.addWidget(self.input_text, 0, 1)

        # Controles de imagen (ocultos inicialmente)
        self.lbl_img = QLabel("Archivo de imagen:")
        self.lbl_img.setFont(font(9.5, 600))
        self.lbl_img.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(self.lbl_img, 1, 0)

        img_box = QHBoxLayout()
        self.btn_pick_img = QPushButton("Seleccionar imagen...")
        self.btn_pick_img.setObjectName("ghost")
        self.btn_pick_img.setCursor(Qt.PointingHandCursor)
        self.btn_pick_img.clicked.connect(self._pick_watermark_image)
        img_box.addWidget(self.btn_pick_img)

        self.img_name_lbl = QLabel("Ninguna imagen seleccionada")
        self.img_name_lbl.setFont(font(9, 400))
        self.img_name_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        img_box.addWidget(self.img_name_lbl, 1)
        grid.addLayout(img_box, 1, 1)

        self.lbl_img.hide()
        self.btn_pick_img.hide()
        self.img_name_lbl.hide()

        # Posición
        lbl_pos = QLabel("Posición en la página:")
        lbl_pos.setFont(font(9.5, 600))
        lbl_pos.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_pos, 2, 0)

        self.combo_pos = QComboBox()
        self.combo_pos.addItem("Centro del documento", "center")
        self.combo_pos.addItem("Superior Izquierda", "top_left")
        self.combo_pos.addItem("Superior Centro", "top_center")
        self.combo_pos.addItem("Superior Derecha", "top_right")
        self.combo_pos.addItem("Inferior Izquierda", "bottom_left")
        self.combo_pos.addItem("Inferior Centro", "bottom_center")
        self.combo_pos.addItem("Inferior Derecha", "bottom_right")
        grid.addWidget(self.combo_pos, 2, 1)

        # Rotación
        lbl_ang = QLabel("Inclinación / Ángulo:")
        lbl_ang.setFont(font(9.5, 600))
        lbl_ang.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_ang, 3, 0)

        self.combo_angle = QComboBox()
        self.combo_angle.addItem("Diagonal estándar (45°)", 45.0)
        self.combo_angle.addItem("Diagonal invertida (-45°)", -45.0)
        self.combo_angle.addItem("Horizontal recta (0°)", 0.0)
        self.combo_angle.addItem("Vertical (90°)", 90.0)
        grid.addWidget(self.combo_angle, 3, 1)

        # Opacidad
        lbl_op = QLabel("Opacidad y transparencia:")
        lbl_op.setFont(font(9.5, 600))
        lbl_op.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(lbl_op, 4, 0)

        op_row = QHBoxLayout()
        self.slider_op = QSlider(Qt.Horizontal)
        self.slider_op.setRange(10, 100)
        self.slider_op.setValue(30)
        self.lbl_op_val = QLabel("30%")
        self.lbl_op_val.setFont(font(9.5, 600))
        self.lbl_op_val.setStyleSheet(f"color: {C.ACCENT_SOFT};")
        self.slider_op.valueChanged.connect(lambda v: self.lbl_op_val.setText(f"{v}%"))
        op_row.addWidget(self.slider_op, 1)
        op_row.addWidget(self.lbl_op_val)
        grid.addLayout(op_row, 4, 1)

        # Tamaño de fuente (Texto)
        self.lbl_fs = QLabel("Tamaño de texto (pt):")
        self.lbl_fs.setFont(font(9.5, 600))
        self.lbl_fs.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(self.lbl_fs, 5, 0)

        self.spin_fs = QSpinBox()
        self.spin_fs.setRange(14, 120)
        self.spin_fs.setValue(44)
        grid.addWidget(self.spin_fs, 5, 1)

        # Color de texto (Texto)
        self.lbl_color = QLabel("Color del texto:")
        self.lbl_color.setFont(font(9.5, 600))
        self.lbl_color.setStyleSheet(f"color: {C.TEXT_2};")
        grid.addWidget(self.lbl_color, 6, 0)

        self.combo_color = QComboBox()
        self.combo_color.addItem("Gris tenue (#888888)", "#888888")
        self.combo_color.addItem("Rojo alerta (#EF4444)", "#EF4444")
        self.combo_color.addItem("Azul corporativo (#3B82F6)", "#3B82F6")
        self.combo_color.addItem("Negro sobrio (#111111)", "#111111")
        grid.addWidget(self.combo_color, 6, 1)

        cp_layout.addLayout(grid)
        self.config_panel.hide()
        self.content_layout.addWidget(self.config_panel)

        self.content_layout.addStretch()

    def _toggle_watermark_type(self, is_text: bool):
        self.lbl_text.setVisible(is_text)
        self.input_text.setVisible(is_text)
        self.lbl_fs.setVisible(is_text)
        self.spin_fs.setVisible(is_text)
        self.lbl_color.setVisible(is_text)
        self.combo_color.setVisible(is_text)

        self.lbl_img.setVisible(not is_text)
        self.btn_pick_img.setVisible(not is_text)
        self.img_name_lbl.setVisible(not is_text)

    def _pick_watermark_image(self):
        img_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen para marca de agua",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if img_path:
            self.current_image_path = img_path
            self.img_name_lbl.setText(os.path.basename(img_path))
            self.img_name_lbl.setStyleSheet("color: white;")

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
            self.action_bar.set_summary("Configura los parámetros y pulsa el botón para estampar la marca.")
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

        is_text = self.rad_type_text.isChecked()
        watermark_type = "text" if is_text else "image"
        text_val = self.input_text.text().strip()

        if is_text and not text_val:
            self.toast_requested.emit("El texto de la marca de agua no puede estar vacío.", "Texto requerido", "warning", None)
            return

        if not is_text and (not self.current_image_path or not os.path.exists(self.current_image_path)):
            self.toast_requested.emit("Por favor selecciona una imagen para usar como marca de agua.", "Imagen requerida", "warning", None)
            return

        opacity_val = self.slider_op.value() / 100.0
        angle_val = float(self.combo_angle.currentData())
        pos_val = self.combo_pos.currentData()
        fs_val = self.spin_fs.value()
        color_val = self.combo_color.currentData() or "#888888"

        base, ext = os.path.splitext(self.current_pdf)
        default_out = f"{base}_marca_de_agua{ext}"

        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF con marca de agua como...",
            default_out,
            "Archivos PDF (*.pdf)"
        )
        if not out_path:
            return

        def _task():
            add_watermark(
                input_path=self.current_pdf,
                output_path=out_path,
                watermark_type=watermark_type,
                text=text_val,
                image_path=self.current_image_path,
                opacity=opacity_val,
                angle=angle_val,
                font_size=fs_val,
                color_hex=color_val,
                position=pos_val,
                scale=0.5
            )

        def _on_success(_):
            msg = f"Se aplicó la marca de agua con éxito:\n{os.path.basename(out_path)}"
            self.toast_requested.emit(msg, "PDF guardado", "success", out_path)
            add_recent(out_path, "Marca de Agua", "PDF")

        self.run_task(
            task_func=_task,
            on_success=_on_success,
            initial_msg="Estampando marca de agua en cada página..."
        )
