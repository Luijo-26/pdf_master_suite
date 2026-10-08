"""
main.py
Punto de entrada principal para PDF Master Suite.
Interfaz gráfica moderna, fluida y nativa construida con PySide6 (Qt) en modo oscuro.
Procesamiento asíncrono multihilo, arrastre de archivos nativo y soporte integral offline.
"""

import sys
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from ui.app import MainWindow
from ui.theme import apply_theme


def main():
    # Soporte para pantallas con escala High-DPI en Windows
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("PDF Master Suite")
    app.setOrganizationName("PDF Master")

    # Aplicar sistema de diseño y paleta oscura
    apply_theme(app)

    # Ventana principal
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
