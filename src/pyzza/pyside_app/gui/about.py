from PySide6.QtWidgets import QGridLayout, QLabel, QDialog

from pyside_app.gui.icons import Icons
from pyside_app.gui.misc import icon_label


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayout(layout := QGridLayout())

        layout.addWidget(QLabel("Text"), 0, 0, 1, 3)
        layout.addWidget(icon_label(Icons.BOOK.image(), size=512), 1, 0, 2, 2)
