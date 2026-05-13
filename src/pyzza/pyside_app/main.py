from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

# noinspection PyUnusedImports
import pyzza.pyside_app.rc_icons  # Needed to load the icons
from pyzza.pyside_app.gui.icons import Icons
from pyzza.pyside_app.gui.main_window import MainWindow

# TODOLIST:
# - TODO: Handling search for ingredients and sub-recipes
# - TODO: Pdf printing
# - TODO: List parent recipes in sub-recipes?
# - TODO: Festive overlay
# - TODO: Packaging
# - TODO: Delete recipe from details dialog

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(Icons.BOOK.image())
    QCoreApplication.setApplicationName("Pyzza")
    QCoreApplication.setOrganizationDomain("almann.studio")
    QCoreApplication.setOrganizationName("Almann Studio")

    w = MainWindow()
    w.show()

    app.exec()

