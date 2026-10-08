"""
ui/worker.py
Ejecución en segundo plano con QThreadPool. Las señales se emiten desde el hilo
de trabajo y Qt las entrega en el hilo de la interfaz (conexión en cola).
"""

from typing import Callable, Optional, Set

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int, int, str)
    item = Signal(object)


class Worker(QRunnable):
    """
    Ejecuta `fn` en un hilo del pool.
    - with_progress: fn recibe un callback progress(actual, total, texto).
    - with_items: fn recibe un callback emit(obj) para resultados parciales.
    Si ambos están activos, fn(progress, emit).
    """

    def __init__(self, fn: Callable, with_progress: bool = False, with_items: bool = False):
        super().__init__()
        self.fn = fn
        self.with_progress = with_progress
        self.with_items = with_items
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        sig = self.signals
        try:
            args = []
            if self.with_progress:
                args.append(lambda cur, total, text="": sig.progress.emit(int(cur), int(total), str(text)))
            if self.with_items:
                args.append(lambda obj: sig.item.emit(obj))
            result = self.fn(*args)
        except Exception as exc:  # noqa: BLE001 - se reporta a la interfaz
            sig.error.emit(str(exc) or exc.__class__.__name__)
        else:
            sig.finished.emit(result)


_alive: Set[WorkerSignals] = set()


def start(
    worker: Worker,
    on_done: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    on_progress: Optional[Callable] = None,
    on_item: Optional[Callable] = None,
) -> None:
    sig = worker.signals
    _alive.add(sig)

    if on_item:
        sig.item.connect(on_item)
    if on_progress:
        sig.progress.connect(on_progress)
    if on_done:
        sig.finished.connect(on_done)
    if on_error:
        sig.error.connect(on_error)

    def _cleanup(*_):
        _alive.discard(sig)

    sig.finished.connect(_cleanup)
    sig.error.connect(_cleanup)
    QThreadPool.globalInstance().start(worker)
