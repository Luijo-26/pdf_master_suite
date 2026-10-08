"""
ui/components/file_list.py
Lista de archivos interactiva, reordenable mediante arrastrar y soltar (drag & drop),
fluida y con soporte nativo de miniaturas para imágenes y documentos.
Permite reordenar arrastrando cualquier fila, botones en línea (▲ ▼),
y ordenar rápidamente (A-Z, Z-A, Invertir).
"""

import os
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QByteArray, QPoint, QRectF, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QColor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent,
    QDropEvent, QImageReader, QPainter, QPainterPath, QPen, QPixmap
)
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.theme import C, font, format_bytes, rgba

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_THUMB_CACHE: Dict[str, QPixmap] = {}


def _get_thumbnail(file_path: str, size: int = 34) -> Optional[QPixmap]:
    """Genera y cachea una miniatura cuadrada con esquinas redondeadas para archivos de imagen."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in _IMAGE_EXTS or not os.path.exists(file_path):
        return None

    try:
        mtime = os.path.getmtime(file_path)
        cache_key = f"{file_path}_{mtime}_{size}"
        if cache_key in _THUMB_CACHE:
            return _THUMB_CACHE[cache_key]

        reader = QImageReader(file_path)
        reader.setAutoTransform(True)
        orig = reader.size()
        if not orig.isValid():
            return None

        # Escalar de forma eficiente durante la decodificación
        orig.scale(QSize(size * 2, size * 2), Qt.KeepAspectRatio)
        reader.setScaledSize(orig)
        img = reader.read()
        if img.isNull():
            return None

        raw_pm = QPixmap.fromImage(img)
        out_pm = QPixmap(size, size)
        out_pm.fill(Qt.transparent)

        p = QPainter(out_pm)
        p.setRenderHint(QPainter.Antialiasing)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, size, size), 6, 6)
        p.setClipPath(clip_path)

        scaled = raw_pm.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (size - scaled.width()) // 2
        y = (size - scaled.height()) // 2
        p.drawPixmap(x, y, scaled)
        p.end()

        if len(_THUMB_CACHE) > 200:
            _THUMB_CACHE.pop(next(iter(_THUMB_CACHE)))
        _THUMB_CACHE[cache_key] = out_pm
        return out_pm
    except Exception:
        return None


class FileItemRow(QFrame):
    """
    Fila individual que representa un archivo dentro de la lista.
    Soporta arrastre nativo para reordenar, indicador visual de soltado,
    miniatura previa si es imagen, y botones directos de acción.
    """
    reorder_requested = Signal(int, int)       # (src_idx, target_idx)
    insert_files_requested = Signal(int, list) # (target_idx, files)
    live_drag_started = Signal(object, QPoint)  # (row, offset de agarre)
    live_drag_moved = Signal(object, QPoint)    # (row, posición global)
    live_drag_finished = Signal(object)         # (row)

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
        self.index = index
        self.file_path = file_path
        self._drag_start_pos: Optional[QPoint] = None
        self._drop_indicator: Optional[str] = None  # "top" o "bottom"

        self.setObjectName("fileRow")
        self.setFixedHeight(54)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(10)

        # 1. Icono de agarre (Grip) para indicar arrastre
        self.grip_lbl = QLabel()
        self.grip_lbl.setPixmap(pixmap("grip", 15, C.TEXT_3))
        self.grip_lbl.setFixedSize(16, 24)
        self.grip_lbl.setToolTip("Arrastra para cambiar el orden")
        self.grip_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.grip_lbl)

        # 2. Indicador numérico de posición
        self.idx_lbl = QLabel(f"#{index + 1}")
        self.idx_lbl.setFont(font(9.5, 600))
        self.idx_lbl.setStyleSheet(f"color: {C.ACCENT_SOFT}; min-width: 24px;")
        self.idx_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.idx_lbl)

        # 3. Miniatura de imagen o icono de tipo documento
        thumb_pm = _get_thumbnail(file_path, 36)
        if thumb_pm:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(thumb_pm)
            icon_lbl.setFixedSize(36, 36)
            icon_lbl.setStyleSheet(f"border: 1px solid {C.BORDER}; border-radius: 6px;")
        else:
            is_img = file_path.lower().endswith(tuple(_IMAGE_EXTS))
            is_word = file_path.lower().endswith((".docx", ".doc"))
            icon_name = "image" if is_img else ("filetext" if is_word else "file")
            icon_color = "#EC4899" if is_img else ("#3B82F6" if is_word else C.ACCENT)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(pixmap(icon_name, 20, icon_color))
            icon_lbl.setFixedSize(24, 24)

        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(icon_lbl)

        # 4. Datos del archivo
        info_col = QVBoxLayout()
        info_col.setSpacing(1)
        info_col.setAlignment(Qt.AlignVCenter)

        name_lbl = QLabel(os.path.basename(file_path))
        name_lbl.setFont(font(10, 600))
        name_lbl.setStyleSheet("color: white;")
        name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        info_col.addWidget(name_lbl)

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
        sub_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        info_col.addWidget(sub_lbl)

        layout.addLayout(info_col, 1)

        # 5. Botones de acción rápida
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

    # --- Arrastre en vivo: mantener presionado y mover ---
    def set_index(self, idx: int):
        self.index = idx
        self.idx_lbl.setText(f"#{idx + 1}")

    def set_placeholder(self, active: bool):
        """Atenúa la fila original mientras su 'fantasma' sigue al cursor."""
        if active:
            eff = QGraphicsOpacityEffect(self)
            eff.setOpacity(0.25)
            self.setGraphicsEffect(eff)
        else:
            self.setGraphicsEffect(None)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self._live_dragging = False
            event.accept()  # imprescindible para recibir mouseMoveEvent
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start_pos is None or not (event.buttons() & Qt.LeftButton):
            super().mouseMoveEvent(event)
            return
        if not getattr(self, "_live_dragging", False):
            dist = (event.position().toPoint() - self._drag_start_pos).manhattanLength()
            if dist < QApplication.startDragDistance():
                return
            self._live_dragging = True
            self.setCursor(Qt.ClosedHandCursor)
            self.live_drag_started.emit(self, self._drag_start_pos)
        self.live_drag_moved.emit(self, event.globalPosition().toPoint())
        event.accept()

    def mouseReleaseEvent(self, event):
        was_dragging = getattr(self, "_live_dragging", False)
        self._drag_start_pos = None
        self._live_dragging = False
        if was_dragging:
            self.setCursor(Qt.OpenHandCursor)
            self.live_drag_finished.emit(self)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # --- Lógica de recepción de soltado (Drop) ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            y = event.position().y()
            indicator = "bottom" if y > self.height() / 2 else "top"
            if self._drop_indicator != indicator:
                self._drop_indicator = indicator
                self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        if self._drop_indicator is not None:
            self._drop_indicator = None
            self.update()

    def dropEvent(self, event: QDropEvent):
        insert_after = event.position().y() > self.height() / 2
        target_idx = self.index + 1 if insert_after else self.index
        self._drop_indicator = None
        self.update()

        if event.mimeData().hasFormat("application/x-file-row-index"):
            src_idx = int(bytes(event.mimeData().data("application/x-file-row-index")).decode("utf-8"))
            event.acceptProposedAction()
            self.reorder_requested.emit(src_idx, target_idx)
        elif event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if files:
                event.acceptProposedAction()
                self.insert_files_requested.emit(target_idx, files)
            else:
                event.ignore()
        else:
            event.ignore()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Línea indicadora de inserción durante el arrastre
        if self._drop_indicator:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            y = self.height() - 2 if self._drop_indicator == "bottom" else 2
            pen = QPen(QColor(C.ACCENT), 3.0)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(10, y, self.width() - 10, y)

            p.setBrush(QColor(C.ACCENT))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(10, y), 3, 3)
            p.drawEllipse(QPoint(self.width() - 10, y), 3, 3)


class FileDropScrollArea(QScrollArea):
    """Área con scroll que delega eventos de arrastre a su lista contenedora."""
    files_dropped_at_bottom = Signal(list)
    reorder_dropped_at_bottom = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        if self.viewport():
            self.viewport().setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat("application/x-file-row-index"):
            src_idx = int(bytes(event.mimeData().data("application/x-file-row-index")).decode("utf-8"))
            event.acceptProposedAction()
            self.reorder_dropped_at_bottom.emit(src_idx)
        elif event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if files:
                event.acceptProposedAction()
                self.files_dropped_at_bottom.emit(files)
            else:
                event.ignore()
        else:
            event.ignore()


class FileList(QFrame):
    """
    Contenedor completo de lista de archivos interactiva con barra de herramientas,
    arrastrar y soltar para reordenar, botones rápidos e inserción intuitiva.
    """
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
        self._rows: List[FileItemRow] = []
        self._drag_row: Optional[FileItemRow] = None
        self._drag_ghost: Optional[QLabel] = None
        self._grab_offset = QPoint()
        self._last_global = QPoint()
        self._auto_scroll = QTimer(self)
        self._auto_scroll.setInterval(25)
        self._auto_scroll.timeout.connect(self._on_auto_scroll)

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

        # Pista sutil de arrastre para el usuario
        self.hint_lbl = QLabel("Arrastra las filas para ajustar el orden")
        self.hint_lbl.setFont(font(8.5, 400))
        self.hint_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        toolbar.addWidget(self.hint_lbl)

        self.count_lbl = QLabel("0 archivos")
        self.count_lbl.setFont(font(9.5, 600))
        self.count_lbl.setStyleSheet(f"color: {C.ACCENT_SOFT};")
        toolbar.addWidget(self.count_lbl)

        main_layout.addLayout(toolbar)

        # 2. Área con scroll para la lista de elementos
        self.scroll = FileDropScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {C.SURFACE};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)
        self.scroll.files_dropped_at_bottom.connect(lambda fs: self._insert_files(len(self.files), fs))
        self.scroll.reorder_dropped_at_bottom.connect(lambda s: self._reorder_item(s, len(self.files)))

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
        """Añade archivos al final de la lista evitando duplicados."""
        self._insert_files(len(self.files), new_paths)

    def _insert_files(self, target_idx: int, new_paths: List[str]):
        """Inserta archivos en una posición concreta respetando extensiones permitidas."""
        valid_files = []
        for p in new_paths:
            norm = os.path.normpath(p)
            if self.allowed_extensions:
                ext = "." + norm.split(".")[-1].lower() if "." in norm else ""
                if ext not in self.allowed_extensions:
                    continue
            if norm not in self.files and os.path.exists(norm):
                valid_files.append(norm)

        if not valid_files:
            return

        pos = max(0, min(len(self.files), target_idx))
        for offset, vf in enumerate(valid_files):
            self.files.insert(pos + offset, vf)

        self._render_list()
        self.files_changed.emit(list(self.files))

    def _reorder_item(self, src: int, target: int):
        """Mueve un elemento de la posición `src` a la posición `target`."""
        if src == target or not (0 <= src < len(self.files)):
            return

        item = self.files.pop(src)
        dest = target - 1 if src < target else target
        dest = max(0, min(len(self.files), dest))
        self.files.insert(dest, item)

        self._render_list()
        self.files_changed.emit(list(self.files))

    # ------------------------------------------------------------------
    # Arrastre en vivo (mantener presionado y mover)
    # ------------------------------------------------------------------
    def _on_live_drag_started(self, row: "FileItemRow", grab_offset: QPoint):
        self._drag_row = row
        self._grab_offset = grab_offset
        vp = self.scroll.viewport()

        ghost = QLabel(vp)
        ghost.setPixmap(row.grab())
        ghost.resize(row.size())
        ghost.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        shadow = QGraphicsDropShadowEffect(ghost)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        ghost.setGraphicsEffect(shadow)
        ghost.move(row.mapTo(vp, QPoint(0, 0)))
        ghost.show()
        ghost.raise_()
        self._drag_ghost = ghost

        row.set_placeholder(True)
        self._auto_scroll.start()

    def _on_live_drag_moved(self, row: "FileItemRow", global_pos: QPoint):
        if self._drag_row is not row or self._drag_ghost is None:
            return
        self._last_global = global_pos
        vp = self.scroll.viewport()

        # 1. El fantasma sigue al cursor (solo en vertical)
        local = vp.mapFromGlobal(global_pos)
        x = row.mapTo(vp, QPoint(0, 0)).x()
        y = local.y() - self._grab_offset.y()
        y = max(-row.height() // 2, min(vp.height() - row.height() // 2, y))
        self._drag_ghost.move(x, y)

        # 2. Calcular la posición destino según las coordenadas del contenedor
        container_y = self.container.mapFromGlobal(global_pos).y()
        cur = self._rows.index(row)
        target = min(
            range(len(self._rows)),
            key=lambda i: abs(self._rows[i].geometry().center().y() - container_y),
        )
        if target != cur:
            self._rows.pop(cur)
            self._rows.insert(target, row)
            self.list_layout.removeWidget(row)
            self.list_layout.insertWidget(target, row)
            self.list_layout.activate()
            for i, r in enumerate(self._rows):
                r.set_index(i)

    def _on_auto_scroll(self):
        if self._drag_row is None:
            self._auto_scroll.stop()
            return
        vp = self.scroll.viewport()
        y = vp.mapFromGlobal(self._last_global).y()
        bar = self.scroll.verticalScrollBar()
        margin = 40
        step = 0
        if y < margin:
            step = -max(4, (margin - y) // 2)
        elif y > vp.height() - margin:
            step = max(4, (y - (vp.height() - margin)) // 2)
        if step:
            old = bar.value()
            bar.setValue(old + step)
            if bar.value() != old:
                self._on_live_drag_moved(self._drag_row, self._last_global)

    def _on_live_drag_finished(self, row: "FileItemRow"):
        self._auto_scroll.stop()
        if self._drag_ghost is not None:
            self._drag_ghost.deleteLater()
            self._drag_ghost = None
        row.set_placeholder(False)
        self._drag_row = None

        new_order = [r.file_path for r in self._rows]
        changed = (new_order != self.files)
        self.files = new_order
        self._render_list()
        if changed:
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
        self._rows = []
        # Limpiar widgets previos
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total = len(self.files)
        self.count_lbl.setText(f"{total} archivo(s)")

        has_files = total > 0
        self.btn_sort_az.setEnabled(total > 1)
        self.btn_sort_za.setEnabled(total > 1)
        self.btn_reverse.setEnabled(total > 1)
        self.btn_clear.setEnabled(has_files)
        self.hint_lbl.setVisible(total > 1)

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
                on_move_up=lambda i=idx: self._move_item_by_step(i, -1),
                on_move_down=lambda i=idx: self._move_item_by_step(i, 1),
                on_delete=lambda i=idx: self._delete_item(i),
                extra_info=extra,
                is_first=(idx == 0),
                is_last=(idx == total - 1),
                parent=self.container,
            )
            row.reorder_requested.connect(self._reorder_item)
            row.insert_files_requested.connect(self._insert_files)
            row.live_drag_started.connect(self._on_live_drag_started)
            row.live_drag_moved.connect(self._on_live_drag_moved)
            row.live_drag_finished.connect(self._on_live_drag_finished)
            self._rows.append(row)
            self.list_layout.addWidget(row)

    def _move_item_by_step(self, idx: int, delta: int):
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

    # Arrastrar y soltar archivos externos sobre el marco general
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-file-row-index") or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat("application/x-file-row-index"):
            src_idx = int(bytes(event.mimeData().data("application/x-file-row-index")).decode("utf-8"))
            event.acceptProposedAction()
            self._reorder_item(src_idx, len(self.files))
        elif event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if files:
                event.acceptProposedAction()
                self.add_files(files)
            else:
                event.ignore()
        else:
            event.ignore()
