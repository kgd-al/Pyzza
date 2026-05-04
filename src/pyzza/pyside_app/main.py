from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

from pyside_app.gui.main_window import MainWindow
import pyside_app.rc_icons

if __name__ == "__main__":
    app = QApplication([])
    QCoreApplication.setApplicationName("Pyzza")
    QCoreApplication.setOrganizationDomain("almann.studio")
    QCoreApplication.setOrganizationName("Almann Studio")

    w = MainWindow()
    w.show()

    QTimer.singleShot(100, lambda: w.table.doubleClicked.emit(w.proxy_model.index(0, 0)))

    app.exec()

