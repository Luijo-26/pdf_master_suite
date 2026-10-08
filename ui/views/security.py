"""
ui/views/security.py
Herramienta para proteger documentos PDF con cifrado de estándar bancario (AES-256 / AES-128)
o desbloquear y remover contraseñas de archivos protegidos.
"""

import os
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QRadioButton, QVBoxLayout, QWidget
)

from pdf_tools import decrypt_pdf, encrypt_pdf, is_pdf_encrypted
from ui.components.drop_zone import DropZone
from ui.icons import pixmap
from ui.theme import C, font, format_bytes, rgba
from ui.views.base_tool import BaseToolView


class SecurityView(BaseToolView):

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            title="Seguridad de PDF",
            subtitle="Protege tus archivos con contraseña bajo cifrado robusto AES o remueve la clave de apertura.",
            icon_name="shield",
            accent_color="#F0506E",
            button_text="Proteger PDF y guardar como...",
            parent=parent,
        )
        self.current_pdf: str = ""
        self._pwd_visible = False
        self._init_content()

    def _init_content(self):
        # 1. Selector de modo (Proteger vs Desbloquear)
        mode_card = QFrame()
        mode_card.setObjectName("card")
        mc_layout = QHBoxLayout(mode_card)
        mc_layout.setContentsMargins(16, 10, 16, 10)
        mc_layout.setSpacing(24)

        self.radio_encrypt = QRadioButton("🔒 Proteger PDF con Contraseña")
        self.radio_encrypt.setFont(font(10, 600))
        self.radio_encrypt.setChecked(True)
        self.radio_encrypt.toggled.connect(self._on_mode_changed)
        mc_layout.addWidget(self.radio_encrypt)

        self.radio_decrypt = QRadioButton("🔓 Desproteger / Remover Contraseña")
        self.radio_decrypt.setFont(font(10, 600))
        self.radio_decrypt.toggled.connect(self._on_mode_changed)
        mc_layout.addWidget(self.radio_decrypt)

        mc_layout.addStretch()
        self.content_layout.addWidget(mode_card)

        # 2. Zona de soltar PDF
        self.drop_zone = DropZone(
            title="Arrastra el documento PDF aquí",
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

        # 3. Tarjeta de archivo seleccionado
        self.file_card = QFrame()
        self.file_card.setObjectName("card")
        fc_layout = QHBoxLayout(self.file_card)
        fc_layout.setContentsMargins(16, 12, 16, 12)
        fc_layout.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("file", 24, "#F0506E"))
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

        self.status_badge = QLabel()
        self.status_badge.setFont(font(8.5, 600))
        fc_layout.addWidget(self.status_badge)

        btn_change = QPushButton("Cambiar archivo")
        btn_change.setObjectName("ghost")
        btn_change.setCursor(Qt.PointingHandCursor)
        btn_change.clicked.connect(self._reset_file)
        fc_layout.addWidget(btn_change)

        self.file_card.hide()
        self.content_layout.addWidget(self.file_card)

        # 4. Formulario de contraseña y algoritmo
        self.form_panel = QFrame()
        self.form_panel.setObjectName("panel")
        fp_layout = QVBoxLayout(self.form_panel)
        fp_layout.setContentsMargins(20, 16, 20, 16)
        fp_layout.setSpacing(14)

        # Contraseña
        lbl_pwd = QLabel("CONTRASEÑA DEL DOCUMENTO")
        lbl_pwd.setProperty("role", "section")
        lbl_pwd.setFont(font(8.5, 700))
        fp_layout.addWidget(lbl_pwd)

        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(8)

        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        self.pwd_entry.setPlaceholderText("Introduce la contraseña...")
        self.pwd_entry.textChanged.connect(self._on_pwd_changed)
        pwd_row.addWidget(self.pwd_entry, 1)

        self.btn_eye = QPushButton()
        self.btn_eye.setObjectName("iconbtn")
        self.btn_eye.setIcon(pixmap("eye", 16, C.TEXT_2))
        self.btn_eye.setToolTip("Mostrar/Ocultar contraseña")
        self.btn_eye.setFixedSize(36, 36)
        self.btn_eye.setCursor(Qt.PointingHandCursor)
        self.btn_eye.clicked.connect(self._toggle_pwd_visibility)
        pwd_row.addWidget(self.btn_eye)
        fp_layout.addLayout(pwd_row)

        # Medidor de fortaleza (solo para modo encriptar)
        self.strength_box = QFrame()
        sb_layout = QVBoxLayout(self.strength_box)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(4)

        self.strength_bar = QProgressBar()
        self.strength_bar.setFixedHeight(4)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{ background: {C.INPUT}; border: none; border-radius: 2px; }}
            QProgressBar::chunk {{ background: {C.DANGER}; border-radius: 2px; }}
        """)
        sb_layout.addWidget(self.strength_bar)

        self.strength_lbl = QLabel("Seguridad: introduce al menos 6 caracteres")
        self.strength_lbl.setFont(font(8.5, 400))
        self.strength_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        sb_layout.addWidget(self.strength_lbl)
        fp_layout.addWidget(self.strength_box)

        # Selector de Algoritmo (solo para encriptar)
        self.algo_box = QFrame()
        ab_layout = QVBoxLayout(self.algo_box)
        ab_layout.setContentsMargins(0, 6, 0, 0)
        ab_layout.setSpacing(6)

        lbl_algo = QLabel("ALGORITMO DE CIFRADO")
        lbl_algo.setProperty("role", "section")
        lbl_algo.setFont(font(8.5, 700))
        ab_layout.addWidget(lbl_algo)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(18)
        self.radio_aes256 = QRadioButton("AES-256 (Máxima seguridad bancaria recomendada)")
        self.radio_aes256.setFont(font(9.5, 500))
        self.radio_aes256.setChecked(True)
        radio_row.addWidget(self.radio_aes256)

        self.radio_aes128 = QRadioButton("AES-128 (Compatibilidad con lectores antiguos)")
        self.radio_aes128.setFont(font(9.5, 500))
        radio_row.addWidget(self.radio_aes128)
        radio_row.addStretch()
        ab_layout.addLayout(radio_row)
        fp_layout.addWidget(self.algo_box)

        self.form_panel.hide()
        self.content_layout.addWidget(self.form_panel)
        self.content_layout.addStretch()

    def add_initial_files(self, files: List[str]):
        pdf_files = [f for f in files if f.lower().endswith(".pdf")]
        if pdf_files:
            self._on_file_selected([pdf_files[0]])

    def _toggle_pwd_visibility(self):
        self._pwd_visible = not self._pwd_visible
        if self._pwd_visible:
            self.pwd_entry.setEchoMode(QLineEdit.Normal)
            self.btn_eye.setIcon(pixmap("eyeoff", 16, C.ACCENT))
        else:
            self.pwd_entry.setEchoMode(QLineEdit.Password)
            self.btn_eye.setIcon(pixmap("eye", 16, C.TEXT_2))

    def _on_mode_changed(self):
        is_encrypt = self.radio_encrypt.isChecked()
        self.strength_box.setVisible(is_encrypt)
        self.algo_box.setVisible(is_encrypt)

        if is_encrypt:
            self.action_bar.set_button_text("Proteger PDF y guardar como...")
            self.pwd_entry.setPlaceholderText("Introduce una nueva contraseña de protección...")
        else:
            self.action_bar.set_button_text("Desproteger PDF y guardar como...")
            self.pwd_entry.setPlaceholderText("Introduce la contraseña actual para desbloquear...")

        self._check_ready()

    def _on_file_selected(self, files: List[str]):
        if not files:
            return
        path = os.path.normpath(files[0])
        try:
            encrypted = is_pdf_encrypted(path)
            self.current_pdf = path
            sz = os.path.getsize(path)

            self.fname_lbl.setText(os.path.basename(path))
            self.fmeta_lbl.setText(f"{format_bytes(sz)}  •  {os.path.dirname(path)}")

            if encrypted:
                self.status_badge.setText("🔒 Protegido con clave")
                self.status_badge.setStyleSheet(f"""
                    background: {rgba(C.WARNING, 0.20)};
                    color: {C.WARNING};
                    border: 1px solid {rgba(C.WARNING, 0.40)};
                    border-radius: 4px; padding: 2px 6px;
                """)
                # Auto-sugerir modo desproteger
                if self.radio_encrypt.isChecked():
                    self.radio_decrypt.setChecked(True)
            else:
                self.status_badge.setText("🔓 Sin contraseña")
                self.status_badge.setStyleSheet(f"""
                    background: {rgba(C.SUCCESS, 0.20)};
                    color: {C.SUCCESS};
                    border: 1px solid {rgba(C.SUCCESS, 0.40)};
                    border-radius: 4px; padding: 2px 6px;
                """)
                if self.radio_decrypt.isChecked():
                    self.radio_encrypt.setChecked(True)

            self.drop_zone.hide()
            self.file_card.show()
            self.form_panel.show()

            self._check_ready()
        except Exception as exc:
            self.toast_requested.emit(f"No se pudo leer el archivo: {str(exc)}", "Error", "error", None)

    def _reset_file(self):
        self.current_pdf = ""
        self.file_card.hide()
        self.form_panel.hide()
        self.drop_zone.show()
        self.action_bar.set_summary("Selecciona un PDF para continuar")
        self.action_bar.set_enabled(False)

    def _on_pwd_changed(self, text: str):
        pwd = text.strip()
        length = len(pwd)

        if self.radio_encrypt.isChecked():
            # Evaluar fortaleza simple
            if length == 0:
                self.strength_bar.setValue(0)
                self.strength_lbl.setText("Seguridad: introduce al menos 6 caracteres")
                self.strength_lbl.setStyleSheet(f"color: {C.TEXT_3};")
            elif length < 6:
                self.strength_bar.setValue(30)
                self.strength_bar.setStyleSheet(f"""
                    QProgressBar {{ background: {C.INPUT}; border: none; border-radius: 2px; }}
                    QProgressBar::chunk {{ background: {C.DANGER}; border-radius: 2px; }}
                """)
                self.strength_lbl.setText("Seguridad: Débil (añade más caracteres)")
                self.strength_lbl.setStyleSheet(f"color: {C.DANGER};")
            elif length < 10:
                self.strength_bar.setValue(65)
                self.strength_bar.setStyleSheet(f"""
                    QProgressBar {{ background: {C.INPUT}; border: none; border-radius: 2px; }}
                    QProgressBar::chunk {{ background: {C.WARNING}; border-radius: 2px; }}
                """)
                self.strength_lbl.setText("Seguridad: Aceptable")
                self.strength_lbl.setStyleSheet(f"color: {C.WARNING};")
            else:
                self.strength_bar.setValue(100)
                self.strength_bar.setStyleSheet(f"""
                    QProgressBar {{ background: {C.INPUT}; border: none; border-radius: 2px; }}
                    QProgressBar::chunk {{ background: {C.SUCCESS}; border-radius: 2px; }}
                """)
                self.strength_lbl.setText("Seguridad: Robusta y segura")
                self.strength_lbl.setStyleSheet(f"color: {C.SUCCESS};")

        self._check_ready()

    def _check_ready(self):
        has_file = bool(self.current_pdf and os.path.exists(self.current_pdf))
        has_pwd = bool(self.pwd_entry.text().strip())

        if not has_file:
            self.action_bar.set_summary("Carga un documento PDF primero")
            self.action_bar.set_enabled(False)
        elif not has_pwd:
            self.action_bar.set_summary("Ingresa la contraseña para continuar", is_warning=True)
            self.action_bar.set_enabled(False)
        else:
            mode_text = "proteger con contraseña" if self.radio_encrypt.isChecked() else "desbloquear"
            self.action_bar.set_summary(f"Listo para {mode_text}")
            self.action_bar.set_enabled(True)

    def on_action_execute(self):
        if not self.current_pdf or not os.path.exists(self.current_pdf):
            return

        pwd = self.pwd_entry.text().strip()
        if not pwd:
            return

        is_encrypt = self.radio_encrypt.isChecked()
        base_name = os.path.splitext(os.path.basename(self.current_pdf))[0]
        src_file = self.current_pdf

        if is_encrypt:
            algo = "AES-256" if self.radio_aes256.isChecked() else "AES-128"
            out_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF protegido como",
                os.path.join(os.path.dirname(src_file), f"protegido_{base_name}.pdf"),
                "Archivos PDF (*.pdf)",
            )
            if not out_path:
                return

            def task():
                encrypt_pdf(src_file, out_path, password=pwd, algorithm=algo)
                return out_path

            def on_done(res):
                self.notify_success(
                    f"PDF protegido exitosamente con cifrado {algo}:\n{os.path.basename(res)}",
                    file_path=res,
                    tool_name="Seguridad de PDF",
                )

            self.run_task(task, on_success=on_done, initial_msg=f"Cifrando documento con {algo}...")

        else:
            out_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar PDF desbloqueado como",
                os.path.join(os.path.dirname(src_file), f"desprotegido_{base_name}.pdf"),
                "Archivos PDF (*.pdf)",
            )
            if not out_path:
                return

            def task():
                decrypt_pdf(src_file, out_path, password=pwd)
                return out_path

            def on_done(res):
                self.notify_success(
                    f"Contraseña removida exitosamente:\n{os.path.basename(res)}",
                    file_path=res,
                    tool_name="Seguridad de PDF",
                )

            self.run_task(task, on_success=on_done, initial_msg="Desbloqueando documento PDF...")
