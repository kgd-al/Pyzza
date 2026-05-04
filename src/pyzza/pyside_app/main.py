from PySide6.QtCore import QCoreApplication, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pyside_app.gui.main_window import MainWindow
import pyside_app.rc_icons

# TODOLIST:
# - TODO: All of the recipe viewer editing logic
# -> TODO: Ingredient input dialog
# ->> TODO: Actually list ingredients/units on book read?
# > TODO: Adding recipe
# - TODO: Saving (and handling cancels) of the whole book
# - TODO: Handling search for sub-recipe, ingredients and sub-recipes
# - TODO: Pdf printing
# - TODO: Make the about

if __name__ == "__main__":
    app = QApplication([])
    QCoreApplication.setApplicationName("Pyzza")
    QCoreApplication.setOrganizationDomain("almann.studio")
    QCoreApplication.setOrganizationName("Almann Studio")

    w = MainWindow()
    w.show()

    # QTimer.singleShot(100, lambda: w.table.doubleClicked.emit(w.proxy_model.index(0, 0)))
    def goto_about():
        QTest.keyClick(w, Qt.Key.Key_M, Qt.KeyboardModifier.AltModifier, delay=100)
        QTest.keyClick(w, Qt.Key.Key_Down, delay=100)
        QTest.keyClick(w, Qt.Key.Key_Enter, delay=100)

    QTimer.singleShot(100, goto_about)

    app.exec()

