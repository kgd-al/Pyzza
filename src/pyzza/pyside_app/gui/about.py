import ast

from PySide6.QtWidgets import QGridLayout, QLabel, QDialog, QVBoxLayout, QCheckBox

from pyside_app.gui.icons import Icons
from pyside_app.gui.misc import icon_label
from pyside_app.settings import Settings


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setLayout(layout := QVBoxLayout())

        layout.addWidget(QLabel("Made with love <3"))
        layout.addWidget(icon_label(Icons.BOOK.image(), size=512), 1)
        layout.addWidget(QLabel("Download latest versions for desktop and android from"))

        url = "https://github.com/kgd-al/Pyzza/releases"
        url_label = QLabel(f"<a href={url}>{url}</a>")
        url_label.setOpenExternalLinks(True)
        layout.addWidget(url_label)

        layout.addSpacing(5)
        layout.addWidget(animation := QCheckBox("Start-up animation?"))
        self.animation = animation

        self.restore_settings()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def restore_settings(self):
        if animation := Settings.STARTUP_ANIMATION.get(True):
            self.animation.setChecked(animation)

    def save_settings(self):
        Settings.STARTUP_ANIMATION.set(self.animation.isChecked())
