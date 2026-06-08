from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

# noinspection PyUnusedImports
import pyzza.pyside_app.rc_icons  # Needed to load the icons
from pyzza.pyside_app.gui.icons import Icons
from pyzza.pyside_app.gui.main_window import MainWindow

# TODOLIST:
# - TODO: Handling search for ingredients and sub-recipes
# - TODO: Better packaging
# - TODO: Delete recipe from details dialog
# - TODO: Swap +- in android recipe viewer
# - TODO: Update ingredients/units list on recipe update/add/del
# - TODO: Update used_in on recipe update/add/dell

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(Icons.BOOK.image())
    QCoreApplication.setApplicationName("Pyzza")
    QCoreApplication.setOrganizationDomain("almann.studio")
    QCoreApplication.setOrganizationName("Almann Studio")

    w = MainWindow()
    w.show()

    w.print_pdf("test.pdf")
    QTimer.singleShot(100, w.close)

    app.exec()

