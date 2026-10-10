"""
ui/components/update_dialog.py
Ventana modal emergente para notificación, descarga y aplicación de actualizaciones
de PDF Master Suite con diseño oscuro nativo en PySide6.
"""

import html
import os
import re
from typing import Optional

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QScrollArea, QTextBrowser, QVBoxLayout, QWidget
)

from core.updater import (
    ReleaseInfo,
    UpdateDownloadThread,
    apply_update_and_restart,
    set_ignored_version,
)
from core.version import APP_NAME, APP_VERSION
from ui.icons import icon, logo_pixmap, pixmap
from ui.theme import C, font, format_bytes, qcolor, rgba


def _markdown_to_simple_html(md_text: str) -> str:
    """Convierte markdown básico de releases de GitHub a HTML estilizado para QTextBrowser."""
    if not md_text:
        return "<p style='color: #A0A6B5; font-style: italic;'>No hay notas de versión disponibles.</p>"

    # Escapar HTML previo
    lines = md_text.splitlines()
    html_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            html_lines.append("<div style='height: 8px;'></div>")
            continue

        # Encabezados
        if stripped.startswith("#### "):
            title = html.escape(stripped[5:])
            html_lines.append(f"<h4 style='color: #B4AAFF; margin: 10px 0 4px 0; font-size: 13px; font-weight: 600;'>{title}</h4>")
        elif stripped.startswith("### "):
            title = html.escape(stripped[4:])
            html_lines.append(f"<h3 style='color: #E8E9EF; margin: 12px 0 6px 0; font-size: 14px; font-weight: 700;'>{title}</h3>")
        elif stripped.startswith("## "):
            title = html.escape(stripped[3:])
            html_lines.append(f"<h2 style='color: #FFFFFF; margin: 14px 0 8px 0; font-size: 15px; font-weight: 700;'>{title}</h2>")
        elif stripped.startswith("# "):
            title = html.escape(stripped[2:])
            html_lines.append(f"<h1 style='color: #FFFFFF; margin: 16px 0 8px 0; font-size: 16px; font-weight: 700;'>{title}</h1>")
        elif stripped.startswith("---") or stripped.startswith("***"):
            html_lines.append(f"<hr style='border: none; border-top: 1px solid {C.BORDER}; margin: 10px 0;'>")
        elif stripped.startswith("* ") or stripped.startswith("- "):
            item = html.escape(stripped[2:])
            # Negritas en listas
            item = re.sub(r"\*\*(.+?)\*\*", r"<b style='color: #FFFFFF;'>\1</b>", item)
            # Código en listas
            item = re.sub(r"`(.+?)`", r"<code style='background: #232632; color: #B4AAFF; padding: 2px 4px; border-radius: 4px;'>\1</code>", item)
            html_lines.append(f"<li style='color: #CBD0DD; margin-bottom: 4px; line-height: 1.4;'>{item}</li>")
        else:
            text = html.escape(stripped)
            text = re.sub(r"\*\*(.+?)\*\*", r"<b style='color: #FFFFFF;'>\1</b>", text)
            text = re.sub(r"`(.+?)`", r"<code style='background: #232632; color: #B4AAFF; padding: 2px 4px; border-radius: 4px;'>\1</code>", text)
            html_lines.append(f"<p style='color: #A0A6B5; margin: 4px 0; line-height: 1.45;'>{text}</p>")

    content = "\n".join(html_lines)
    return f"""
    <div style='font-family: Segoe UI, sans-serif; font-size: 12.5px; color: #E8E9EF;'>
        {content}
    </div>
    """


class UpdateDialog(QDialog):
    """
    Diálogo modal premium que informa de una nueva versión disponible,
    permite consultar las notas de parche y actualizar directamente.
    """

    def __init__(self, release_info: ReleaseInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.release_info = release_info
        self.download_thread: Optional[UpdateDownloadThread] = None
        self._drag_position: Optional[QPoint] = None

        self.setWindowTitle(f"Actualización disponible — {APP_NAME}")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(560, 580)
        self.setMinimumSize(500, 520)

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)

        # Contenedor principal con sombra y bordes redondeados
        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        self.container.setStyleSheet(f"""
            QFrame#dialogContainer {{
                background: {C.SURFACE};
                border: 1px solid {C.BORDER_STRONG};
                border-radius: 18px;
            }}
        """)

        # Sombra difuminada
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(qcolor("#000000", 160))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(24, 20, 24, 22)
        container_layout.setSpacing(16)

        # -------------------------------------------------------------
        # 1. Cabecera con soporte para arrastrar ventana
        # -------------------------------------------------------------
        header = QHBoxLayout()
        header.setSpacing(12)

        # Icono / Badge con brillo
        icon_frame = QFrame()
        icon_frame.setFixedSize(46, 46)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C.ACCENT}, stop:1 {C.ACCENT_2});
                border-radius: 14px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap("sparkles", 24, "#FFFFFF"))
        icon_layout.addWidget(icon_lbl)
        header.addWidget(icon_frame)

        # Título y subtítulo
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_lbl = QLabel("¡Nueva versión disponible!")
        title_lbl.setFont(font(13.5, 700))
        title_lbl.setStyleSheet("color: #FFFFFF;")
        title_box.addWidget(title_lbl)

        sub_lbl = QLabel(f"Se ha publicado una actualización de {APP_NAME}")
        sub_lbl.setFont(font(9, 400))
        sub_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        title_box.addWidget(sub_lbl)

        header.addLayout(title_box, 1)

        # Botón de cerrar (✕)
        btn_close = QPushButton()
        btn_close.setFixedSize(30, 30)
        btn_close.setIcon(QIcon(pixmap("x", 16, C.TEXT_2)))
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
            }}
        """)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)

        container_layout.addLayout(header)

        # -------------------------------------------------------------
        # 2. Píldoras de Versión y Tamaño
        # -------------------------------------------------------------
        version_row = QHBoxLayout()
        version_row.setSpacing(10)

        # Tarjeta comparativa de versión
        ver_badge = QFrame()
        ver_badge.setStyleSheet(f"""
            QFrame {{
                background: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 10px;
                padding: 6px 12px;
            }}
        """)
        vb_layout = QHBoxLayout(ver_badge)
        vb_layout.setContentsMargins(10, 6, 10, 6)
        vb_layout.setSpacing(8)

        cur_v = QLabel(f"v{APP_VERSION}")
        cur_v.setFont(font(9.5, 500))
        cur_v.setStyleSheet(f"color: {C.TEXT_3};")
        vb_layout.addWidget(cur_v)

        arrow_lbl = QLabel()
        arrow_lbl.setPixmap(pixmap("arrowright", 13, C.ACCENT))
        vb_layout.addWidget(arrow_lbl)

        new_v = QLabel(f"{self.release_info.tag_name}")
        new_v.setFont(font(10.5, 700))
        new_v.setStyleSheet(f"color: {C.ACCENT_SOFT};")
        vb_layout.addWidget(new_v)

        version_row.addWidget(ver_badge)

        # Píldora de peso del archivo
        if self.release_info.asset_size > 0:
            size_badge = QFrame()
            size_badge.setStyleSheet(f"""
                QFrame {{
                    background: {C.CARD};
                    border: 1px solid {C.BORDER};
                    border-radius: 10px;
                    padding: 6px 12px;
                }}
            """)
            sb_layout = QHBoxLayout(size_badge)
            sb_layout.setContentsMargins(10, 6, 10, 6)
            sb_layout.setSpacing(6)

            dl_icon = QLabel()
            dl_icon.setPixmap(pixmap("download", 13, C.TEXT_2))
            sb_layout.addWidget(dl_icon)

            size_lbl = QLabel(f"Tamaño: {format_bytes(self.release_info.asset_size)}")
            size_lbl.setFont(font(9, 500))
            size_lbl.setStyleSheet(f"color: {C.TEXT_2};")
            sb_layout.addWidget(size_lbl)

            version_row.addWidget(size_badge)

        version_row.addStretch()
        container_layout.addLayout(version_row)

        # -------------------------------------------------------------
        # 3. Visor de Changelog (Notas de la versión)
        # -------------------------------------------------------------
        changelog_frame = QFrame()
        changelog_frame.setStyleSheet(f"""
            QFrame {{
                background: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)
        cf_layout = QVBoxLayout(changelog_frame)
        cf_layout.setContentsMargins(12, 10, 12, 10)
        cf_layout.setSpacing(6)

        ch_header = QLabel("NOVEDADES Y CAMBIOS")
        ch_header.setFont(font(8.5, 700))
        ch_header.setStyleSheet(f"color: {C.TEXT_3}; letter-spacing: 0.5px;")
        cf_layout.addWidget(ch_header)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet(f"""
            QTextBrowser {{
                background: transparent;
                border: none;
                color: {C.TEXT};
            }}
        """)
        self.text_browser.setHtml(_markdown_to_simple_html(self.release_info.body))
        cf_layout.addWidget(self.text_browser, 1)

        container_layout.addWidget(changelog_frame, 1)

        # -------------------------------------------------------------
        # 4. Zona Interactiva de Progreso de Descarga (Oculta al inicio)
        # -------------------------------------------------------------
        self.progress_container = QFrame()
        self.progress_container.setStyleSheet(f"""
            QFrame {{
                background: {C.CARD};
                border: 1px solid {rgba(C.ACCENT, 0.35)};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        pc_layout = QVBoxLayout(self.progress_container)
        pc_layout.setContentsMargins(12, 10, 12, 10)
        pc_layout.setSpacing(8)

        self.progress_title = QLabel("Descargando actualización...")
        self.progress_title.setFont(font(9.5, 600))
        self.progress_title.setStyleSheet("color: #FFFFFF;")
        pc_layout.addWidget(self.progress_title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #12131A;
                border: 1px solid {C.BORDER};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C.ACCENT}, stop:1 {C.ACCENT_2});
                border-radius: 4px;
            }}
        """)
        pc_layout.addWidget(self.progress_bar)

        self.progress_stats = QLabel("Conectando con el servidor...")
        self.progress_stats.setFont(font(8.5, 400))
        self.progress_stats.setStyleSheet(f"color: {C.TEXT_2};")
        pc_layout.addWidget(self.progress_stats)

        self.progress_container.hide()
        container_layout.addWidget(self.progress_container)

        # -------------------------------------------------------------
        # 5. Botones de Acción Inferiores
        # -------------------------------------------------------------
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)

        # Botón Omitir esta versión
        self.btn_skip = QPushButton("Omitir esta versión")
        self.btn_skip.setObjectName("link")
        self.btn_skip.setCursor(Qt.PointingHandCursor)
        self.btn_skip.clicked.connect(self._on_skip_clicked)
        self.actions_layout.addWidget(self.btn_skip)

        self.actions_layout.addStretch()

        # Botón Más tarde
        self.btn_later = QPushButton("Más tarde")
        self.btn_later.setCursor(Qt.PointingHandCursor)
        self.btn_later.setFixedWidth(110)
        self.btn_later.clicked.connect(self.reject)
        self.actions_layout.addWidget(self.btn_later)

        # Botón Actualizar Ahora
        self.btn_update = QPushButton("Actualizar ahora")
        self.btn_update.setObjectName("primary")
        self.btn_update.setCursor(Qt.PointingHandCursor)
        self.btn_update.setIcon(QIcon(pixmap("download", 16, "#FFFFFF")))
        self.btn_update.clicked.connect(self._start_download)
        self.actions_layout.addWidget(self.btn_update)

        # Botón Cancelar descarga (inicialmente oculto)
        self.btn_cancel_dl = QPushButton("Cancelar descarga")
        self.btn_cancel_dl.setCursor(Qt.PointingHandCursor)
        self.btn_cancel_dl.hide()
        self.btn_cancel_dl.clicked.connect(self._cancel_download)
        self.actions_layout.addWidget(self.btn_cancel_dl)

        container_layout.addLayout(self.actions_layout)

        root_layout.addWidget(self.container)

    # -----------------------------------------------------------------
    # Mover ventana sin marco mediante clic sostenido en la cabecera
    # -----------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None

    # -----------------------------------------------------------------
    # Acciones
    # -----------------------------------------------------------------
    def _on_skip_clicked(self):
        """Omite la versión actual para no volver a notificarla."""
        set_ignored_version(self.release_info.version)
        self.reject()

    def _start_download(self):
        """Inicia el proceso de descarga del archivo .exe."""
        if not self.release_info.download_url:
            QDesktopServices.openUrl(QUrl(self.release_info.html_url))
            self.accept()
            return

        # Si el asset no es un binario directo sino la página HTML
        if not self.release_info.download_url.lower().endswith(".exe"):
            QDesktopServices.openUrl(QUrl(self.release_info.html_url))
            self.accept()
            return

        # Cambiar interfaz a modo descarga
        self.btn_update.hide()
        self.btn_later.hide()
        self.btn_skip.hide()
        self.btn_cancel_dl.show()
        self.progress_container.show()

        self.progress_title.setText(f"Descargando {self.release_info.asset_name or 'actualización'}...")
        self.progress_bar.setValue(0)
        self.progress_stats.setText("Iniciando conexión con GitHub...")

        # Iniciar hilo de descarga
        self.download_thread = UpdateDownloadThread(
            download_url=self.release_info.download_url,
            file_name=self.release_info.asset_name,
            parent=self,
        )
        self.download_thread.progress.connect(self._on_download_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.cancelled.connect(self._on_download_cancelled)
        self.download_thread.start()

    def _cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.progress_title.setText("Cancelando descarga...")
            self.download_thread.cancel()

    def _on_download_progress(self, downloaded: int, total: int, percent: float, speed_kbps: float):
        self.progress_bar.setValue(int(percent))
        speed_str = f"{speed_kbps / 1024.0:.1f} MB/s" if speed_kbps > 1024 else f"{speed_kbps:.0f} KB/s"
        total_str = format_bytes(total) if total > 0 else "desconocido"
        self.progress_stats.setText(
            f"{format_bytes(downloaded)} / {total_str} ({percent:.1f}%) • {speed_str}"
        )

    def _on_download_finished(self, temp_filepath: str):
        self.progress_bar.setValue(100)
        self.progress_title.setText("¡Descarga completada!")
        self.progress_stats.setText("Preparando instalación y reinicio...")
        self.btn_cancel_dl.hide()

        # Intentar aplicar actualización
        success, reason = apply_update_and_restart(temp_filepath, self.release_info.asset_name)
        if not success:
            if reason == "dev_mode":
                self.progress_stats.setText(
                    f"Modo de desarrollo detectado. Archivo descargado en:\n{temp_filepath}\n"
                    "Ejecuta 'git pull' o compila con build.bat para actualizar."
                )
                self.btn_cancel_dl.setText("Cerrar")
                self.btn_cancel_dl.show()
            else:
                self.progress_title.setText("Error en la instalación")
                self.progress_stats.setText(f"{reason}")
                self.btn_cancel_dl.setText("Cerrar")
                self.btn_cancel_dl.show()

    def _on_download_error(self, error_msg: str):
        self.progress_title.setText("Error al descargar")
        self.progress_stats.setText(f"No se pudo completar la descarga: {error_msg}")
        self.btn_cancel_dl.setText("Volver")
        self.btn_cancel_dl.clicked.disconnect()
        self.btn_cancel_dl.clicked.connect(self._reset_to_action_state)

    def _on_download_cancelled(self):
        self._reset_to_action_state()

    def _reset_to_action_state(self):
        self.progress_container.hide()
        self.btn_cancel_dl.hide()
        self.btn_cancel_dl.setText("Cancelar descarga")
        self.btn_cancel_dl.clicked.disconnect()
        self.btn_cancel_dl.clicked.connect(self._cancel_download)
        self.btn_update.show()
        self.btn_later.show()
        self.btn_skip.show()

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait(2000)
        super().closeEvent(event)
