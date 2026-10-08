"""
ui/components/drop_zone.py
Zona de arrastrar y soltar con soporte nativo de archivos desde el Explorador de Windows.
Ofrece feedback visual reactivo durante el arrastre y botón para seleccionar archivos manualmente.
"""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.theme import C, font, rgba


class DropZone(QFrame):
    """
    Componente para soltar o examinar archivos.
    Emite `files_dropped(List[str])` tanto al soltar como al elegir desde el explorador.
    """
    files_dropped = Signal(list)

    def __init__(
        self,
        title: str = "Arrastra tus archivos aquí",
        subtitle: str = "o haz clic en el botón para buscarlos en tu equipo",
        button_text: str = "Examinar archivos...",
        allowed_extensions: Optional[List[str]] = None,
        file_filter: str = "Todos los archivos (*.*)",
        allow_multiple: bool = True,
        compact: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.title_text = title
        self.subtitle_text = subtitle
        self.button_text = button_text
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        self.file_filter = file_filter
        self.allow_multiple = allow_multiple
        self.compact = compact
        self._drag_hover = False

        self.setAcceptDrops(True)
        self.setObjectName("dropZone")

        if compact:
            self._init_compact_ui()
        else:
            self._init_full_ui()

        self._update_style()

    def _init_full_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        # Icono central
        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(pixmap("upload", 38, C.ACCENT))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_lbl)

        # Textos
        self.title_lbl = QLabel(self.title_text)
        self.title_lbl.setFont(font(12, 600))
        self.title_lbl.setStyleSheet("color: white;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(self.subtitle_text)
        self.sub_lbl.setFont(font(9.5, 400))
        self.sub_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_lbl)

        # Botón
        self.browse_btn = QPushButton(self.button_text)
        self.browse_btn.setObjectName("accent")
        self.browse_btn.setIcon(pixmap("folder", 16, "white"))
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(38)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn, 0, Qt.AlignCenter)

    def _init_compact_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setPixmap(pixmap("upload", 22, C.ACCENT))
        layout.addWidget(self.icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_lbl = QLabel(self.title_text)
        self.title_lbl.setFont(font(10.5, 600))
        self.title_lbl.setStyleSheet("color: white;")
        text_col.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(self.subtitle_text)
        self.sub_lbl.setFont(font(9, 400))
        self.sub_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        text_col.addWidget(self.sub_lbl)
        layout.addLayout(text_col, 1)

        self.browse_btn = QPushButton(self.button_text)
        self.browse_btn.setIcon(pixmap("folder", 14, C.TEXT))
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(34)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)

    def _update_style(self):
        if self._drag_hover:
            self.setStyleSheet(f"""
                QFrame#dropZone {{
                    background-color: {rgba(C.ACCENT, 0.12)};
                    border: 2px dashed {C.ACCENT};
                    border-radius: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#dropZone {{
                    background-color: {rgba(C.SURFACE, 0.8)};
                    border: 2px dashed {C.BORDER_STRONG};
                    border-radius: 14px;
                }}
                QFrame#dropZone:hover {{
                    background-color: {rgba(C.CARD_HOVER, 0.5)};
                    border-color: {rgba(C.ACCENT, 0.6)};
                }}
            """)

    def _on_browse_clicked(self):
        if self.allow_multiple:
            files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos", "", self.file_filter)
        else:
            file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", self.file_filter)
            files = [file_name] if file_name else []

        if files:
            filtered = self._filter_extensions(files)
            if filtered:
                self.files_dropped.emit(filtered)

    def _filter_extensions(self, file_paths: List[str]) -> List[str]:
        if not self.allowed_extensions:
            return file_paths
        valid = []
        for p in file_paths:
            ext = "." + p.split(".")[-1].lower() if "." in p else ""
            if ext in self.allowed_extensions:
                valid.append(p)
        return valid

    # Eventos nativos de arrastrar y soltar
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_hover = True
            self._update_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._drag_hover = False
        self._update_style()

    def dropEvent(self, event: QDropEvent):
        self._drag_hover = False
        self._update_style()

        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        filtered = self._filter_extensions(files)

        if filtered:
            event.acceptProposedAction()
            self.files_dropped.emit(filtered)
        else:
            event.ignore()
