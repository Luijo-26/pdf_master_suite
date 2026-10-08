"""
ui/components/page_grid.py
Cuadrícula visual interactiva de miniaturas de páginas PDF.
Utiliza PySide6.QtPdf para renderizar las páginas en miniatura con alta nitidez,
permite reordenar páginas arrastrando y soltando (drag & drop), botones rápidos (◀ ▶),
rotación visual instantánea (+90°, -90°, 180°), inversión de orden, eliminación y selección múltiple.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set

from PySide6.QtCore import QByteArray, QPoint, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent,
    QDropEvent, QImage, QPainter, QPen, QPixmap, QTransform
)
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel,
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
    """
    Tarjeta individual que muestra una miniatura de página con sus controles.
    Soporta arrastre interactivo para reordenar páginas, botones para mover
    hacia la izquierda/derecha, rotación y eliminación.
    """
    rotate_requested = Signal(int, int)    # current_pos, degrees
    delete_requested = Signal(int)         # current_pos
    selection_toggled = Signal(int, bool)  # current_pos, is_selected
    move_requested = Signal(int, int)      # current_pos, delta (-1 o +1)
    reorder_requested = Signal(int, int)   # src_pos, target_pos
    live_drag_started = Signal(object, QPoint)
    live_drag_moved = Signal(object, QPoint)
    live_drag_finished = Signal(object)

    def __init__(
        self,
        current_pos: int,
        item_data: PageItemData,
        base_pixmap: Optional[QPixmap] = None,
        is_first: bool = False,
        is_last: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.current_pos = current_pos
        self.data = item_data
        self.base_pixmap = base_pixmap
        self.is_first = is_first
        self.is_last = is_last
        self._drag_start_pos: Optional[QPoint] = None
        self._drop_indicator: Optional[str] = None  # "left" o "right"

        self.setObjectName("pageCard")
        self.setFixedSize(164, 230)
        self.setCursor(Qt.OpenHandCursor)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 1. Cabecera de la tarjeta: Grip + Checkbox + Número de página + Badge rotación
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
        self.num_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
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
        self.thumb_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.thumb_lbl, 1)

        # 3. Barra de acciones rápidas sobre la página
        btn_row = QHBoxLayout()
        btn_row.setSpacing(3)
        btn_row.setAlignment(Qt.AlignCenter)

        # Botón mover hacia la izquierda
        btn_left = QPushButton()
        btn_left.setObjectName("iconbtn")
        btn_left.setIcon(pixmap("chevronleft", 13, C.TEXT_2))
        btn_left.setToolTip("Mover a la izquierda (antes)")
        btn_left.setFixedSize(24, 24)
        btn_left.setCursor(Qt.PointingHandCursor)
        btn_left.setEnabled(not is_first)
        btn_left.clicked.connect(lambda: self.move_requested.emit(self.current_pos, -1))
        btn_row.addWidget(btn_left)

        # Girar antihorario
        btn_ccw = QPushButton()
        btn_ccw.setObjectName("iconbtn")
        btn_ccw.setIcon(pixmap("rotccw", 13, C.TEXT_2))
        btn_ccw.setToolTip("Girar -90° (antihorario)")
        btn_ccw.setFixedSize(24, 24)
        btn_ccw.setCursor(Qt.PointingHandCursor)
        btn_ccw.clicked.connect(lambda: self.rotate_requested.emit(self.current_pos, -90))
        btn_row.addWidget(btn_ccw)

        # Girar horario
        btn_cw = QPushButton()
        btn_cw.setObjectName("iconbtn")
        btn_cw.setIcon(pixmap("rotcw", 13, C.TEXT_2))
        btn_cw.setToolTip("Girar +90° (horario)")
        btn_cw.setFixedSize(24, 24)
        btn_cw.setCursor(Qt.PointingHandCursor)
        btn_cw.clicked.connect(lambda: self.rotate_requested.emit(self.current_pos, 90))
        btn_row.addWidget(btn_cw)

        # Botón mover hacia la derecha
        btn_right = QPushButton()
        btn_right.setObjectName("iconbtn")
        btn_right.setIcon(pixmap("chevronright", 13, C.TEXT_2))
        btn_right.setToolTip("Mover a la derecha (después)")
        btn_right.setFixedSize(24, 24)
        btn_right.setCursor(Qt.PointingHandCursor)
        btn_right.setEnabled(not is_last)
        btn_right.clicked.connect(lambda: self.move_requested.emit(self.current_pos, 1))
        btn_row.addWidget(btn_right)

        # Eliminar página
        btn_del = QPushButton()
        btn_del.setObjectName("iconbtn")
        btn_del.setIcon(pixmap("trash", 13, C.DANGER))
        btn_del.setToolTip("Eliminar página")
        btn_del.setFixedSize(24, 24)
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

    # --- Arrastre en vivo: mantener presionado y mover ---
    def set_pos(self, pos: int):
        self.current_pos = pos
        self.num_lbl.setText(f"Pág. {pos + 1}")

    def set_placeholder(self, active: bool):
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
            event.accept()  # necesario para seguir recibiendo mouseMoveEvent
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
        if event.mimeData().hasFormat("application/x-pdf-page-card"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasFormat("application/x-pdf-page-card"):
            x = event.position().x()
            indicator = "right" if x > self.width() / 2 else "left"
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
        insert_after = event.position().x() > self.width() / 2
        target_idx = self.current_pos + 1 if insert_after else self.current_pos
        self._drop_indicator = None
        self.update()

        if event.mimeData().hasFormat("application/x-pdf-page-card"):
            src_idx = int(bytes(event.mimeData().data("application/x-pdf-page-card")).decode("utf-8"))
            event.acceptProposedAction()
            self.reorder_requested.emit(src_idx, target_idx)
        else:
            event.ignore()

    def paintEvent(self, event):
        super().paintEvent(event)
        # Línea indicadora vertical en el borde izquierdo o derecho
        if self._drop_indicator:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            x = self.width() - 2 if self._drop_indicator == "right" else 2
            pen = QPen(QColor(C.ACCENT), 3.0)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawLine(x, 8, x, self.height() - 8)

            p.setBrush(QColor(C.ACCENT))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPoint(x, 8), 3, 3)
            p.drawEllipse(QPoint(x, self.height() - 8), 3, 3)


class PageGrid(QFrame):
    """Contenedor de cuadrícula que muestra y administra todas las páginas de un PDF."""
    pages_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pdf_path: str = ""
        self.pdf_doc: Optional[QPdfDocument] = None
        self.pages: List[PageItemData] = []
        self.cache_pixmaps: Dict[int, QPixmap] = {}  # original_index -> base pixmap (0 grados)
        self._cards: List[PageThumbnailCard] = []
        self._columns = 4
        self._drag_card: Optional[PageThumbnailCard] = None
        self._drag_ghost: Optional[QLabel] = None
        self._grab_offset = QPoint()
        self._last_global = QPoint()
        self._auto_scroll = QTimer(self)
        self._auto_scroll.setInterval(25)
        self._auto_scroll.timeout.connect(self._on_auto_scroll)

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

        self.btn_reverse = QPushButton("Invertir orden")
        self.btn_reverse.setObjectName("ghost")
        self.btn_reverse.setIcon(pixmap("reverse", 14, C.TEXT_2))
        self.btn_reverse.setToolTip("Invertir el orden completo de las páginas")
        self.btn_reverse.setCursor(Qt.PointingHandCursor)
        self.btn_reverse.clicked.connect(self.reverse_pages)
        toolbar.addWidget(self.btn_reverse)

        self.btn_del = QPushButton("Eliminar")
        self.btn_del.setObjectName("danger")
        self.btn_del.setIcon(pixmap("trash", 14, C.DANGER))
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

        self.hint_lbl = QLabel("Arrastra las tarjetas o usa ◀ ▶ para cambiar el orden")
        self.hint_lbl.setFont(font(8.5, 400))
        self.hint_lbl.setStyleSheet(f"color: {C.TEXT_3};")
        toolbar.addWidget(self.hint_lbl)

        self.status_lbl = QLabel("0 páginas")
        self.status_lbl.setFont(font(9.5, 600))
        self.status_lbl.setStyleSheet(f"color: {C.ACCENT_SOFT};")
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

        if self.pdf_doc:
            self.pdf_doc.close()

        self.pdf_doc = QPdfDocument(self)
        err = self.pdf_doc.load(file_path)
        if err != QPdfDocument.Error.None_:
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
        for btn in (
            self.btn_cw, self.btn_ccw, self.btn_180, self.btn_reverse,
            self.btn_del, self.btn_select_all, self.btn_reset
        ):
            btn.setEnabled(has_pages)
        self.hint_lbl.setVisible(total > 1)

        if not self.pages:
            empty = QLabel("Carga un archivo PDF para visualizar y organizar sus páginas.")
            empty.setFont(font(10, 400))
            empty.setStyleSheet(f"color: {C.TEXT_3};")
            empty.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(empty, 0, 0, 1, 4)
            return

        self._cards = []
        columns = 4  # Cuadrícula responsive de 4 columnas
        for pos, page_data in enumerate(self.pages):
            orig_idx = page_data.original_index

            # Obtener o renderizar miniatura base con QPdfDocument
            base_pm = self.cache_pixmaps.get(orig_idx)
            if base_pm is None and self.pdf_doc:
                img: QImage = self.pdf_doc.render(orig_idx, QSize(160, 220))
                if not img.isNull():
                    base_pm = QPixmap.fromImage(img)
                    self.cache_pixmaps[orig_idx] = base_pm

            card = PageThumbnailCard(
                current_pos=pos,
                item_data=page_data,
                base_pixmap=base_pm,
                is_first=(pos == 0),
                is_last=(pos == total - 1),
                parent=self.grid_container,
            )
            card.rotate_requested.connect(self._on_single_rotate)
            card.delete_requested.connect(self._on_single_delete)
            card.selection_toggled.connect(self._on_single_selection)
            card.move_requested.connect(self._on_move_page)
            card.reorder_requested.connect(self._on_reorder_pages)
            card.live_drag_started.connect(self._on_live_drag_started)
            card.live_drag_moved.connect(self._on_live_drag_moved)
            card.live_drag_finished.connect(self._on_live_drag_finished)

            self._cards.append(card)
            row = pos // columns
            col = pos % columns
            self.grid_layout.addWidget(card, row, col)

    # ------------------------------------------------------------------
    # Arrastre en vivo de tarjetas de páginas
    # ------------------------------------------------------------------
    def _on_live_drag_started(self, card: "PageThumbnailCard", grab_offset: QPoint):
        self._drag_card = card
        self._grab_offset = grab_offset
        vp = self.scroll.viewport()

        ghost = QLabel(vp)
        ghost.setPixmap(card.grab())
        ghost.resize(card.size())
        ghost.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        shadow = QGraphicsDropShadowEffect(ghost)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        ghost.setGraphicsEffect(shadow)
        ghost.move(card.mapTo(vp, QPoint(0, 0)))
        ghost.show()
        ghost.raise_()
        self._drag_ghost = ghost

        card.set_placeholder(True)
        self._auto_scroll.start()

    def _on_live_drag_moved(self, card: "PageThumbnailCard", global_pos: QPoint):
        if self._drag_card is not card or self._drag_ghost is None:
            return
        self._last_global = global_pos
        vp = self.scroll.viewport()

        # El fantasma sigue al cursor libremente en 2D
        local = vp.mapFromGlobal(global_pos)
        x = local.x() - self._grab_offset.x()
        y = local.y() - self._grab_offset.y()
        self._drag_ghost.move(x, y)

        # Calcular la tarjeta destino más cercana en la cuadrícula
        container_pos = self.grid_container.mapFromGlobal(global_pos)
        cur = self._cards.index(card)
        target = min(
            range(len(self._cards)),
            key=lambda i: (self._cards[i].geometry().center() - container_pos).manhattanLength(),
        )
        if target != cur:
            self._cards.pop(cur)
            self._cards.insert(target, card)
            p = self.pages.pop(cur)
            self.pages.insert(target, p)

            for c in self._cards:
                self.grid_layout.removeWidget(c)
            for idx, c in enumerate(self._cards):
                r = idx // self._columns
                col = idx % self._columns
                self.grid_layout.addWidget(c, r, col)
                c.set_pos(idx)
            self.grid_layout.activate()

    def _on_auto_scroll(self):
        if self._drag_card is None:
            self._auto_scroll.stop()
            return
        vp = self.scroll.viewport()
        y = vp.mapFromGlobal(self._last_global).y()
        bar = self.scroll.verticalScrollBar()
        margin = 50
        step = 0
        if y < margin:
            step = -max(4, (margin - y) // 2)
        elif y > vp.height() - margin:
            step = max(4, (y - (vp.height() - margin)) // 2)
        if step:
            old = bar.value()
            bar.setValue(old + step)
            if bar.value() != old:
                self._on_live_drag_moved(self._drag_card, self._last_global)

    def _on_live_drag_finished(self, card: "PageThumbnailCard"):
        self._auto_scroll.stop()
        if self._drag_ghost is not None:
            self._drag_ghost.deleteLater()
            self._drag_ghost = None
        card.set_placeholder(False)
        self._drag_card = None

        self._render_grid()
        self.pages_changed.emit()

    def _on_reorder_pages(self, src: int, target: int):
        """Reordena páginas arrastradas de `src` a `target`."""
        if src == target or not (0 <= src < len(self.pages)):
            return

        item = self.pages.pop(src)
        dest = target - 1 if src < target else target
        dest = max(0, min(len(self.pages), dest))
        self.pages.insert(dest, item)

        self._render_grid()
        self.pages_changed.emit()

    def _on_move_page(self, pos: int, delta: int):
        """Mueve una página una posición hacia la izquierda (-1) o derecha (+1)."""
        target = pos + delta
        if 0 <= target < len(self.pages):
            self.pages[pos], self.pages[target] = self.pages[target], self.pages[pos]
            self._render_grid()
            self.pages_changed.emit()

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
        if not targets:
            targets = self.pages
        for p in targets:
            p.rotation = (p.rotation + degrees) % 360
        self._render_grid()
        self.pages_changed.emit()

    def reverse_pages(self):
        """Invierte el orden de todas las páginas."""
        self.pages.reverse()
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
