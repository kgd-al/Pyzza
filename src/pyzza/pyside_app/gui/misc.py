from enum import StrEnum
from typing import Type

import qtawesome as qta
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QToolButton
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QComboBox, \
    QSizePolicy
from mypyc.primitives.misc_ops import type_object_op

from pyside_app.gui.icons import Icons


def line():
    l = QFrame()
    l.setFrameShape(QFrame.Shape.HLine)
    l.setFrameShadow(QFrame.Shadow.Sunken)
    return l


def decoration(text):
    frame = QFrame()
    frame.setLayout(layout := QVBoxLayout(frame))
    layout.addWidget(QLabel(text))
    return frame


def icon_label(icon: QIcon, size=32):
    label = QLabel()
    label.setPixmap(icon.pixmap(size, size))
    label.setFixedSize(size, size)
    return label


def fa_icon_label(icon: str, size=32):
    return icon_label(qta.icon(icon), size)


def fa_button(name: str, tooltip: str = None, **kwargs):
    button = QToolButton()
    button.setIcon(qta.icon(name, **kwargs))
    if tooltip:
        button.setToolTip(tooltip)
    return button


class YesNoGroupBox(QWidget):
    toggled = Signal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.yes = QRadioButton("Yes")
        self.no = QRadioButton("No")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.yes)
        layout.addWidget(self.no)
        layout.addStretch()
        self.setLayout(layout)

        self.group = QButtonGroup(self)
        self.group.addButton(self.yes)
        self.group.addButton(self.no)

        self.yes.toggled.connect(lambda: self.toggled.emit())
        self.no.toggled.connect(lambda: self.toggled.emit())

    def state(self): return self.yes.isChecked(), self.no.isChecked()

    def set_state(self, state):
        self.yes.setChecked(state[0])
        self.no.setChecked(state[1])

    def value(self):
        return self.yes.isChecked()


class EnumComboBox(QComboBox):
    def __init__(self, enum: Type[StrEnum], parent=None):
        QComboBox.__init__(self, parent)
        for e in enum:
            self.addItem(Icons.get_image(e), self.display(e))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.adjustSize()

    @staticmethod
    def display(e: StrEnum): return e.name.capitalize()

    def setCurrentEnum(self, e: StrEnum):
        self.setCurrentText(self.display(e))

