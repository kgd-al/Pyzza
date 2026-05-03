from PySide6.QtWidgets import QFrame


def line():
    l = QFrame()
    l.setFrameShape(QFrame.Shape.HLine)
    l.setFrameShadow(QFrame.Shadow.Sunken)
    return l
