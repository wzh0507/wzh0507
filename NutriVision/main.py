import sys
from pathlib import Path

# Ensure NutriVision package root is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nutri-Vision 2026")

    # Load QSS
    qss_path = Path(__file__).parent / "assets" / "style.qss"
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    from ui.main_window import MainWindow
    window = MainWindow()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
