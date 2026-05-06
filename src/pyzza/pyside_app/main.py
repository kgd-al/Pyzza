from PySide6.QtCore import QCoreApplication, Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pyside_app.gui.icons import Icons
from pyside_app.gui.main_window import MainWindow

# noinspection PyUnusedImports
import pyside_app.rc_icons  # Needed to load the icons

# TODOLIST:
# > TODO: Adding/removing recipe
# - TODO: Handling search for ingredients and sub-recipes
# - TODO: Pdf printing
# - TODO: Make the about
# - TODO: List parent recipes in sub-recipes?

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(Icons.BOOK.image())
    QCoreApplication.setApplicationName("Pyzza")
    QCoreApplication.setOrganizationDomain("almann.studio")
    QCoreApplication.setOrganizationName("Almann Studio")

    w = MainWindow()
    w.show()
    #
    # def go():
    #     w.table.doubleClicked.emit(w.proxy_model.index(0, 0))
    #     # QTest.keyClick(w, Qt.Key.Key_I, Qt.KeyboardModifier.ControlModifier, delay=100)
    #
    # QTimer.singleShot(100, go)


    # def goto_about():
    #     QTest.keyClick(w, Qt.Key.Key_M, Qt.KeyboardModifier.AltModifier, delay=100)
    #     QTest.keyClick(w, Qt.Key.Key_Down, delay=100)
    #     QTest.keyClick(w, Qt.Key.Key_Enter, delay=100)

    # QTimer.singleShot(100, goto_about)

    app.exec()

