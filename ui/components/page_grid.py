"""
ui/components/page_grid.py
Cuadrícula visual interactiva de miniaturas de páginas PDF.
Utiliza PySide6.QtPdf para renderizar las páginas en miniatura con alta nitidez,
permite rotación visual instantánea (+90°, -90°, 180°), eliminación y selección múltiple.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap, QTransform
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout, QWidget
)

from ui.icons import pixmap
from ui.theme import C, font, rgba


@dataclass
class PageItemData:
    original_index: int
    rotation: int = 0  # 0, 90, 180, 270
    selected: bool = False


class PageThumbnailCard(QFrame):
    """Tarjeta individual que muestra una miniatura de página con sus controles."""
    rotate_requested = Signal(int, int)  # current_pos, degrees
    delete_requested = Signal(int)       # current_pos
    selection_toggled = Signal(int, bool) # current_pos, is_selected

    def __init__(
        self,
        current_pos: int,
        item_data: PageItemData,
        base_pixmap: Optional[QPixmap] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.current_pos = current_pos
        self.data = item_data
        self.base_pixmap = base_pixmap
        self.setObjectName("pageCard")
        self.setFixedSize(160, 225)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Cabecera de la tarjeta: Checkbox + Número de página + Badge de rotación
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.check = QCheckBox()
        self.check.setChecked(self.data.selected)
        self.check.setCursor(Qt.PointingHandCursor)
        self.check.toggled.connect(lambda checked: self.selection_toggled.emit(self.current_pos, checked))
        top_row.addWidget(self.check)

        self.num_lbl = QLabel(f"Pág. {self.current_pos + 1}")
        self.num_lbl.setFont(font(9.5, 600))
        self.num_lbl.setStyleSheet("color: white;")
        top_row.addWidget(self.num_lbl, 1)

        self.rot_badge = QLabel()
        self.rot_badge.setFont(font(8, 600))
        self.rot_badge.setStyleSheet(f"""
            background: {rgba(C.WARNING, 0.20)};
            color: {C.WARNING};
            border: 1px solid {rgba(C.WARNING, 0.40)};
            border-radius: 4px;
            padding: 1px 4px;
        """)
        top_row.addWidget(self.rot_badge)
        layout.addLayout(top_row)

        # 2. Área de miniatura
        self.thumb_lbl = QLabel()
        self.thumb_lbl.setAlignment(Qt.AlignCenter)
        self.thumb_lbl.setStyleSheet(f"""
            background: #111218;
            border: 1px solid {C.BORDER};
            border-radius: 6px;
        """)
        layout.addWidget(self.thumb_lbl, 1)

        # 3. Barra de acciones rápidas sobre la página
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_row.setAlignment(Qt.AlignCenter)

        btn_ccw = QPushButton()
        btn_ccw.setObjectName("iconbtn")
        btn_ccw.setIcon(pixmap("rotccw", 13, C.TEXT_2))
        btn_ccw.setToolTip("Girar -90° (antihorario)")
        btn_ccw.setFixedSize(26, 26)
        btn_ccw.setCursor(Qt.PointingHandCursor)
        btn_ccw.clicked.connect(lambda: self.rotate_requested.emit(self.current_pos, -90))
        btn_row.addWidget(btn_ccw)

        btn_cw = QPushButton()
        btn_cw.setObjectName("iconbtn")
        btn_cw.setIcon(pixmap("rotcw", 13, C.TEXT_2))
        btn_cw.setToolTip("Girar +90° (horario)")
        btn_cw.setFixedSize(26, 26)
        btn_cw.setCursor(Qt.PointingHandCursor)
        btn_cw.clicked.connect(lambda: self.rotate_requested.emit(self.current_pos, 90))
        btn_row.addWidget(btn_cw)

        btn_del = QPushButton()
        btn_del.setObjectName("iconbtn")
        btn_del.setIcon(pixmap("trash", 13, C.DANGER))
        btn_del.setToolTip("Eliminar página")
        btn_del.setFixedSize(26, 26)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self.current_pos))
        btn_row.addWidget(btn_del)

        layout.addLayout(btn_row)

        self.update_view()

    def set_base_pixmap(self, pm: QPixmap):
        self.base_pixmap = pm
        self.update_view()

    def update_view(self):
        # Actualizar badge de rotación
        rot = self.data.rotation % 360
        if rot != 0:
            self.rot_badge.setText(f"{rot}°")
            self.rot_badge.show()
        else:
            self.rot_badge.hide()

        # Renderizar miniatura rotada
        if self.base_pixmap and not self.base_pixmap.isNull():
            if rot != 0:
                t = QTransform().rotate(rot)
                rotated = self.base_pixmap.transformed(t, Qt.SmoothTransformation)
            else:
                rotated = self.base_pixmap

            scaled = rotated.scaled(
                QSize(130, 130),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.thumb_lbl.setPixmap(scaled)
        else:
            self.thumb_lbl.setText(f"Pág. {self.data.original_index + 1}")
            self.thumb_lbl.setStyleSheet(f"color: {C.TEXT_3}; font-size: 11px;")

        # Estilo según selección
        if self.data.selected:
            self.setStyleSheet(f"""
                QFrame#pageCard {{
                    background-color: {rgba(C.ACCENT, 0.12)};
                    border: 2px solid {C.ACCENT};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#pageCard {{
                    background-color: {C.CARD};
                    border: 1px solid {C.BORDER};
                    border-radius: 10px;
                }}
                QFrame#pageCard:hover {{
                    border-color: {C.BORDER_STRONG};
                    background-color: {C.CARD_HOVER};
                }}
            """)


class PageGrid(QFrame):
    """Contenedor de cuadrícula que muestra y administra todas las páginas de un PDF."""
    pages_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pdf_path: str = ""
        self.pdf_doc: Optional[QPdfDocument] = None
        self.pages: List[PageItemData] = []
        self.cache_pixmaps: Dict[int, QPixmap] = {}  # original_index -> base pixmap (0 grados)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 1. Barra de herramientas de acciones sobre páginas
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.btn_cw = QPushButton("↻ +90°")
        self.btn_cw.setToolTip("Girar páginas seleccionadas 90° horario")
        self.btn_cw.setCursor(Qt.PointingHandCursor)
        self.btn_cw.clicked.connect(lambda: self.rotate_selected(90))
        toolbar.addWidget(self.btn_cw)

        self.btn_ccw = QPushButton("↺ -90°")
        self.btn_ccw.setToolTip("Girar páginas seleccionadas 90° antihorario")
        self.btn_ccw.setCursor(Qt.PointingHandCursor)
        self.btn_ccw.clicked.connect(lambda: self.rotate_selected(-90))
        toolbar.addWidget(self.btn_ccw)

        self.btn_180 = QPushButton("↕ 180°")
        self.btn_180.setToolTip("Invertir orientación 180°")
        self.btn_180.setCursor(Qt.PointingHandCursor)
        self.btn_180.clicked.connect(lambda: self.rotate_selected(180))
        toolbar.addWidget(self.btn_180)

        self.btn_del = QPushButton("Eliminar")
        self.btn_del.setObjectName("danger")
        self.btn_del.setToolTip("Eliminar páginas seleccionadas")
        self.btn_del.setCursor(Qt.PointingHandCursor)
        self.btn_del.clicked.connect(self.delete_selected)
        toolbar.addWidget(self.btn_del)

        self.btn_select_all = QPushButton("Seleccionar todas")
        self.btn_select_all.setObjectName("ghost")
        self.btn_select_all.setCursor(Qt.PointingHandCursor)
        self.btn_select_all.clicked.connect(self.toggle_select_all)
        toolbar.addWidget(self.btn_select_all)

        self.btn_reset = QPushButton("Restablecer")
        self.btn_reset.setObjectName("ghost")
        self.btn_reset.setToolTip("Restaurar orden y rotación originales")
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_pages)
        toolbar.addWidget(self.btn_reset)

        toolbar.addStretch()

        self.status_lbl = QLabel("0 páginas")
        self.status_lbl.setFont(font(9.5, 600))
        self.status_lbl.setStyleSheet(f"color: {C.TEXT_2};")
        toolbar.addWidget(self.status_lbl)

        main_layout.addLayout(toolbar)

        # 2. Scroll de cuadrícula
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {C.SURFACE};
                border: 1px solid {C.BORDER};
                border-radius: 12px;
            }}
        """)

        self.grid_container = QWidget()
        self.grid_container.setObjectName("scrollContent")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(12, 12, 12, 12)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll, 1)

    def load_pdf(self, file_path: str):
        """Carga el documento y prepara la cuadrícula de miniaturas."""
        self.pdf_path = file_path
        self.cache_pixmaps.clear()

        # Cerrar documento previo si existía
        if self.pdf_doc:
            self.pdf_doc.close()

        self.pdf_doc = QPdfDocument(self)
        err = self.pdf_doc.load(file_path)
        if err != QPdfDocument.Error.None_:
            # Fallback en caso de error de lectura de QtPdf
            self.pdf_doc = None

        total = self.pdf_doc.pageCount() if self.pdf_doc else 0
        self.pages = [PageItemData(original_index=i, rotation=0) for i in range(total)]

        self._render_grid()
        self.pages_changed.emit()

    def _render_grid(self):
        # Limpiar widgets actuales
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        total = len(self.pages)
        self.status_lbl.setText(f"{total} página(s)")

        has_pages = total > 0
        for btn in (self.btn_cw, self.btn_ccw, self.btn_180, self.btn_del, self.btn_select_all, self.btn_reset):
            btn.setEnabled(has_pages)

        if not self.pages:
            empty = QLabel("Carga un archivo PDF para visualizar y organizar sus páginas.")
            empty.setFont(font(10, 400))
            empty.setStyleSheet(f"color: {C.TEXT_3};")
            empty.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        columns = 4  # Cuadrícula responsive de 4 columnas
        for pos, page_data in enumerate(self.pages):
            orig_idx = page_data.original_index

            # Obtener o renderizar miniatura base con QPdfDocument
            base_pm = self.cache_pixmaps.get(orig_idx)
            if base_pm is None and self.pdf_doc:
                # Renderizar a 180x240 con buena nitidez
                img: QImage = self.pdf_doc.render(orig_idx, QSize(160, 220))
                if not img.isNull():
                    base_pm = QPixmap.fromImage(img)
                    self.cache_pixmaps[orig_idx] = base_pm

            card = PageThumbnailCard(
                current_pos=pos,
                item_data=page_data,
                base_pixmap=base_pm,
                parent=self.grid_container,
            )
            card.rotate_requested.connect(self._on_single_rotate)
            card.delete_requested.connect(self._on_single_delete)
            card.selection_toggled.connect(self._on_single_selection)

            row = pos // columns
            col = pos % columns
            self.grid_layout.addWidget(card, row, col)

    def _on_single_rotate(self, pos: int, degrees: int):
        if 0 <= pos < len(self.pages):
            self.pages[pos].rotation = (self.pages[pos].rotation + degrees) % 360
            self._render_grid()
            self.pages_changed.emit()

    def _on_single_delete(self, pos: int):
        if 0 <= pos < len(self.pages):
            self.pages.pop(pos)
            self._render_grid()
            self.pages_changed.emit()

    def _on_single_selection(self, pos: int, is_selected: bool):
        if 0 <= pos < len(self.pages):
            self.pages[pos].selected = is_selected
            self._update_selection_counts()

    def _update_selection_counts(self):
        sel_count = sum(1 for p in self.pages if p.selected)
        total = len(self.pages)
        if sel_count > 0:
            self.status_lbl.setText(f"{sel_count} de {total} seleccionada(s)")
        else:
            self.status_lbl.setText(f"{total} página(s)")

    def rotate_selected(self, degrees: int):
        targets = [p for p in self.pages if p.selected]
        # Si ninguna está seleccionada, rotar todas
        if not targets:
            targets = self.pages
        for p in targets:
            p.rotation = (p.rotation + degrees) % 360
        self._render_grid()
        self.pages_changed.emit()

    def delete_selected(self):
        self.pages = [p for p in self.pages if not p.selected]
        self._render_grid()
        self.pages_changed.emit()

    def toggle_select_all(self):
        all_selected = all(p.selected for p in self.pages) if self.pages else False
        new_state = not all_selected
        for p in self.pages:
            p.selected = new_state
        self._render_grid()
        self._update_selection_counts()

    def reset_pages(self):
        if self.pdf_path:
            self.load_pdf(self.pdf_path)

    def get_export_config(self) -> List[Dict]:
        """Devuelve la lista con la configuración requerida por pdf_tools.reorganize_pdf."""
        return [
            {"original_index": p.original_index, "rotation": p.rotation}
            for p in self.pages
        ]

    def count(self) -> int:
        return len(self.pages)
