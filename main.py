"""Point d'entrée de l'application FlexiBeam."""
import sys
import os

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from app.ui.main_window import FenetrePrincipale
from app.ui.theme import ThemeManager
from app.config import APP_NAME


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Police par défaut
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Appliquer le thème
    tm = ThemeManager.get()
    tm.apply(app)
    tm.on_change(lambda: tm.apply(app))

    fenetre = FenetrePrincipale()
    fenetre.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
