from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QDialog, QWidget

from models.recipe import DecorationEntry


class IngredientsListEntryDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def showEvent(self, e):
        geom = self.frameGeometry()
        geom.moveCenter(QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(e)

    def entry(self): return DecorationEntry(text="Test")
