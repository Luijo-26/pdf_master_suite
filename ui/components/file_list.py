"""
ui/components/file_list.py
Lista de archivos interactiva, reordenable y fluida para herramientas por lotes
(Unir PDFs, Imágenes a PDF, Word a PDF).
Permite reordenar con un clic mediante botones en línea, arrastrar archivos para añadir más,
y visualizar tamaño, páginas y ruta de cada documento.
"""

import os
from typing import Callable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.theme import C, font, format_bytes, rgba


class FileItemRow(QFrame):
    """Fila individual que representa un archivo dentro de la lista."""

    def __init__(
        self,
        index: int,
        file_path: str,
        on_move_up: Callable,
        on_move_down: Callable,
        on_delete: Callable,
        extra_info: str = "",
        is_first: bool = False,
        is_last: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("fileRow")
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(10)

        # 1. Indicador de posición
        self.idx_lbl = QLabel(f"#{index + 1}")
        self.idx_lbl.setFont(font(9.5, 600))
        self.idx_lbl.setStyleSheet(f"color: {C.ACCENT_SOFT}; min-width: 24px;")
        layout.addWidget(self.idx_lbl)

        # 2. Icono de tipo documento
        icon_name = "image" if file_path.lower().endswith((".jpg", ".png", ".jpeg", ".webp", ".bmp")) else (
            "filetext" if file_path.lower().endswith((".docx", ".doc")) else "file"
        )
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pixmap(icon_name, 18, C.ACCENT))
        icon_lbl.setFixedSize(20, 20)
        layout.addWidget(icon_lbl)

        # 3. Datos del archivo
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        info_col.setAlignment(Qt.AlignVCenter)

        name_lbl = QLabel(os.path.basename(file_path))
        name_lbl.setFont(font(10, 600))
        name_lbl.setStyleSheet("color: white;")
        info_col.addWidget(name_lbl)

        # Subtítulo: tamaño + ruta
        sz_text = ""
        if os.path.exists(file_path):
            sz_text = format_bytes(os.path.getsize(file_path))

        sub_parts = []
        if extra_info:
            sub_parts.append(extra_info)
        if sz_text:
            sub_parts.append(sz_text)
        sub_parts.append(os.path.dirname(file_path))

        sub_lbl = QLabel("  •  ".join(sub_parts))
        sub_lbl.setFont(font(8.5, 400))
        sub_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        info_col.addWidget(sub_lbl)

        layout.addLayout(info_col, 1)

        # 4. Botones rápidos en línea
        btn_up = QPushButton()
        btn_up.setObjectName("iconbtn")
        btn_up.setIcon(pixmap("up", 14, C.TEXT_2))
        btn_up.setToolTip("Subir posición")
        btn_up.setFixedSize(28, 28)
        btn_up.setCursor(Qt.PointingHandCursor)
        btn_up.setEnabled(not is_first)
        btn_up.clicked.connect(on_move_up)
        layout.addWidget(btn_up)

        btn_down = QPushButton()
        btn_down.setObjectName("iconbtn")
        btn_down.setIcon(pixmap("down", 14, C.TEXT_2))
        btn_down.setToolTip("Bajar posición")
        btn_down.setFixedSize(28, 28)
        btn_down.setCursor(Qt.PointingHandCursor)
        btn_down.setEnabled(not is_last)
        btn_down.clicked.connect(on_move_down)
        layout.addWidget(btn_down)

        btn_del = QPushButton()
        btn_del.setObjectName("iconbtn")
        btn_del.setIcon(pixmap("trash", 14, C.DANGER))
        btn_del.setToolTip("Eliminar de la lista")
        btn_del.setFixedSize(28, 28)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(on_delete)
        layout.addWidget(btn_del)

        self.setStyleSheet(f"""
            QFrame#fileRow {{
                background-color: {C.CARD};
                border: 1px solid {C.BORDER};
                border-radius: 10px;
            }}
            QFrame#fileRow:hover {{
                background-color: {C.CARD_HOVER};
                border-color: {C.BORDER_STRONG};
            }}
        """)


class FileList(QFrame):
    """Contenedor completo de lista de archivos con barra de herramientas superior."""
    files_changed = Signal(list)

    def __init__(
        self,
        allowed_extensions: Optional[List[str]] = None,
        file_filter: str = "Todos los archivos (*.*)",
        add_button_text: str = "+ Agregar archivos",
        extra_info_provider: Optional[Callable[[str], str]] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else None
        self.file_filter = file_filter
        self.add_button_text = add_button_text
        self.extra_info_provider = extra_info_provider
        self.files: List[str] = []

        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # 1. Barra de herramientas superior
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.btn_add = QPushButton(self.add_button_text)
        self.btn_add.setObjectName("accent")
        self.btn_add.setIcon(pixmap("plus", 14, "white"))
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self._on_add_clicked)
        toolbar.addWidget(self.btn_add)

        self.btn_sort_az = QPushButton("A-Z")
        self.btn_sort_az.setObjectName("ghost")
        self.btn_sort_az.setIcon(pixmap("sortaz", 14, C.TEXT_2))
        self.btn_sort_az.setToolTip("Ordenar por nombre (A-Z)")
        self.btn_sort_az.setCursor(Qt.PointingHandCursor)
        self.btn_sort_az.clicked.connect(self._sort_az)
        toolbar.addWidget(self.btn_sort_az)

        self.btn_sort_za = QPushButton("Z-A")
        self.btn_sort_za.setObjectName("ghost")
        self.btn_sort_za.setIcon(pixmap("sortza", 14, C.TEXT_2))
        self.btn_sort_za.setToolTip("Ordenar por nombre (Z-A)")
        self.btn_sort_za.setCursor(Qt.PointingHandCursor)
        self.btn_sort_za.clicked.connect(self._sort_za)
        toolbar.addWidget(self.btn_sort_za)

        self.btn_reverse = QPushButton("Invertir")
        self.btn_reverse.setObjectName("ghost")
        self.btn_reverse.setIcon(pixmap("reverse", 14, C.TEXT_2))
        self.btn_reverse.setToolTip("Invertir el orden actual")
        self.btn_reverse.setCursor(Qt.PointingHandCursor)
        self.btn_reverse.clicked.connect(self._reverse_order)
        toolbar.addWidget(self.btn_reverse)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setObjectName("danger")
        self.btn_clear.setIcon(pixmap("trash", 14, C.DANGER))
        self.btn_clear.setToolTip("Vaciar la lista")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        self.count_lbl = QLabel("0 archivos")
        self.count_lbl.setFont(font(9.5, 600))
        self.count_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        toolbar.addWidget(self.count_lbl)

        main_layout.addLayout(toolbar)

        # 2. Área con scroll para la lista de elementos
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {C.SURFACE};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)

        self.container = QWidget()
        self.container.setObjectName("scrollContent")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(6)
        self.list_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll, 1)

        self._render_list()

    def add_files(self, new_paths: List[str]):
        """Añade archivos a la lista evitando duplicados."""
        changed = False
        for p in new_paths:
            norm = os.path.normpath(p)
            if self.allowed_extensions:
                ext = "." + norm.split(".")[-1].lower() if "." in norm else ""
                if ext not in self.allowed_extensions:
                    continue
            if norm not in self.files and os.path.exists(norm):
                self.files.append(norm)
                changed = True
        if changed:
            self._render_list()
            self.files_changed.emit(list(self.files))

    def get_files(self) -> List[str]:
        return list(self.files)

    def count(self) -> int:
        return len(self.files)

    def clear(self):
        if self.files:
            self.files.clear()
            self._render_list()
            self.files_changed.emit([])

    def _render_list(self):
        # Limpiar widgets previos
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total = len(self.files)
        self.count_lbl.setText(f"{total} archivo(s)")

        # Controles habilitados/deshabilitados
        has_files = total > 0
        self.btn_sort_az.setEnabled(total > 1)
        self.btn_sort_za.setEnabled(total > 1)
        self.btn_reverse.setEnabled(total > 1)
        self.btn_clear.setEnabled(has_files)

        if not self.files:
            empty_box = QFrame()
            e_layout = QVBoxLayout(empty_box)
            e_layout.setContentsMargins(20, 40, 20, 40)
            e_layout.setAlignment(Qt.AlignCenter)
            e_layout.setSpacing(8)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(pixmap("file", 32, C.TEXT_3))
            icon_lbl.setAlignment(Qt.AlignCenter)
            e_layout.addWidget(icon_lbl)

            lbl = QLabel("No hay archivos en la lista.\nArrastra archivos aquí o haz clic en '+ Agregar archivos'.")
            lbl.setFont(font(10, 400))
            lbl.setStyleSheet(f"color: {C.TEXT_3};")
            lbl.setAlignment(Qt.AlignCenter)
            e_layout.addWidget(lbl)

            self.list_layout.addWidget(empty_box)
            return

        for idx, path in enumerate(self.files):
            extra = self.extra_info_provider(path) if self.extra_info_provider else ""
            row = FileItemRow(
                index=idx,
                file_path=path,
                on_move_up=lambda i=idx: self._move_item(i, -1),
                on_move_down=lambda i=idx: self._move_item(i, 1),
                on_delete=lambda i=idx: self._delete_item(i),
                extra_info=extra,
                is_first=(idx == 0),
                is_last=(idx == total - 1),
                parent=self.container,
            )
            self.list_layout.addWidget(row)

    def _move_item(self, idx: int, delta: int):
        target = idx + delta
        if 0 <= target < len(self.files):
            self.files[idx], self.files[target] = self.files[target], self.files[idx]
            self._render_list()
            self.files_changed.emit(list(self.files))

    def _delete_item(self, idx: int):
        if 0 <= idx < len(self.files):
            self.files.pop(idx)
            self._render_list()
            self.files_changed.emit(list(self.files))

    def _sort_az(self):
        self.files.sort(key=lambda p: os.path.basename(p).lower())
        self._render_list()
        self.files_changed.emit(list(self.files))

    def _sort_za(self):
        self.files.sort(key=lambda p: os.path.basename(p).lower(), reverse=True)
        self._render_list()
        self.files_changed.emit(list(self.files))

    def _reverse_order(self):
        self.files.reverse()
        self._render_list()
        self.files_changed.emit(list(self.files))

    def _on_add_clicked(self):
        chosen, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos", "", self.file_filter)
        if chosen:
            self.add_files(chosen)

    # Arrastrar y soltar archivos directamente sobre la lista
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if files:
            event.acceptProposedAction()
            self.add_files(files)
        else:
            event.ignore()
