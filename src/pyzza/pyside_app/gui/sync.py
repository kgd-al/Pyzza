from enum import StrEnum
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QToolButton, QHBoxLayout, \
    QLineEdit, QPushButton, QFileDialog

from pyside_app.settings import Settings
from pyzza.networking.sync_server import SyncServer


class SyncDialog(QDialog):
    class Status(StrEnum):
        NO_FILE = "red"
        SYNCING = "yellow"
        ALL_GOOD = "green"

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Synchronization tool")

        self.input_field = QLineEdit(self)
        self.input_field.textChanged.connect(self.on_input_field_changed)

        input_button = QToolButton()
        input_button.setIcon(QIcon.fromTheme("document-open"))
        input_button.clicked.connect(self.on_file_select)

        sub_layout = QHBoxLayout()
        sub_layout.addWidget(self.input_field)
        sub_layout.addWidget(input_button)

        self.log = QTextEdit(self)
        self.log.setReadOnly(True)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.log)
        layout.addWidget(close_button)
        self.setLayout(layout)

        self.server = SyncServer(self.on_file_sent)

        self.status = None
        self.is_file_sent = False

        if (last_file := Settings.LAST_FILE.get()) is not None:
            self.input_field.setText(str(last_file))
        else:
            self.input_field.setPlaceholderText("File path")
            self.update_status()

        self.setMinimumWidth(300)
        self.adjustSize()

    def update_status(self):
        if self.is_file_sent:
            self.status = self.Status.ALL_GOOD
        else:
            path = self.input_field.text()
            if self.is_valid_file(path):
                self.status = SyncDialog.Status.SYNCING
                if not self.server.started:
                    self.log.insertPlainText(f"Starting server...\n")
                    self.server.start()
                    self.log.insertPlainText(f"Server started on {self.server.server_address()}\n")
            else:
                self.status = SyncDialog.Status.NO_FILE

        self.input_field.setStyleSheet(
            "QLineEdit { background-color: " + self.status.value + "; }")

    @staticmethod
    def is_valid_file(file):
        file = Path(file)
        return file.exists() and file.is_file() and file.suffix == ".rbk"

    def on_file_select(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Open File",
            dir=Settings.LAST_FILE.get(),
            filter="*.rbk"
        )
        self.input_field.setText(file)

    def on_input_field_changed(self):
        file = self.input_field.text()
        if self.is_valid_file(file):
            self.is_file_sent = False
            Settings.LAST_FILE.set(file)
            self.server.set_file(file)
            self.update_status()

    def on_file_sent(self, address):
        self.log.insertPlainText(f"File sent to {address}")
        self.is_file_sent = True
        self.update_status()

    def close(self):
        self.server.stop()
        super().close()

