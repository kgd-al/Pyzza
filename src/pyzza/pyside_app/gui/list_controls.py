from typing import Callable
from unittest import case

from PySide6.QtCore import QModelIndex, Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QAbstractItemView, QListView, QListWidget, \
    QListWidgetItem

from pyside_app.gui.misc import fa_button


class ListControls(QWidget):
    def __init__(self, parent: QListWidget, item_builder: Callable = None):
        super().__init__(parent)

        self.item_builder = item_builder

        self.list = parent
        self.list.setDragEnabled(True)
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(add := fa_button("ri.insert-row-bottom", "Add"))
        layout.addWidget(rmv := fa_button("ri.delete-row", "Remove"))
        layout.addWidget(edt := fa_button("fa5s.edit", "Edit"))
        layout.addSpacing(12)
        layout.addWidget(up := fa_button("ri.arrow-drop-up-line", "Up"))
        layout.addWidget(dwn := fa_button("ri.arrow-drop-down-line", "Down"))
        layout.addStretch()
        self.add, self.rmv, self.edt, self.up, self.dwn = buttons = add, rmv, edt, up, dwn

        parent.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._on_selection_changed()

        for button in buttons:
            button.clicked.connect(getattr(self, f"_on_{button.toolTip().lower()}_clicked"))

        self.list.installEventFilter(self)

    def eventFilter(self, watched, event, /):
        if (isinstance(event, QKeyEvent)
                and event.type() == QEvent.Type.KeyPress
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            match event.key():
                case Qt.Key.Key_Down:
                    self._on_down_clicked()
                    return True
                case Qt.Key.Key_Up:
                    self._on_up_clicked()
                    return True
        return False

    def _on_selection_changed(self):
        selection = [r.row() for r in self.list.selectionModel().selectedRows()]

        self.add.setEnabled(self.item_builder is not None)
        self.edt.setEnabled(len(selection) == 1)

        any_selected = len(selection) > 0
        for b in [self.rmv, self.up, self.dwn]:
            b.setEnabled(any_selected)

        if any_selected:
            self.up.setEnabled(max(selection) >= len(selection))
            self.dwn.setEnabled(self.list.model().rowCount() - min(selection) > len(selection))

    def _on_add_clicked(self):
        row = self.list.model().rowCount()
        self.list.insertItem(row, self.item_builder())
        self.list.edit(self.list.model().index(row, 0))

    def _on_edit_clicked(self):
        self.list.edit(self.list.selectionModel().selectedRows()[0])

    def _on_remove_clicked(self):
        selection, model = sorted(self.list.selectionModel().selectedRows()), self.list.model()
        for index in reversed(selection):
            model.removeRow(index.row(), QModelIndex())

    def _on_down_clicked(self):
        selection, model = sorted(self.list.selectionModel().selectedRows()), self.list.model()
        for index in reversed(selection):
            model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row()+2)
        self._on_selection_changed()

    def _on_up_clicked(self):
        selection, model = sorted(self.list.selectionModel().selectedRows()), self.list.model()
        for index in selection:
            model.moveRow(QModelIndex(), index.row(), QModelIndex(), index.row()-1)
        self._on_selection_changed()

    def wrapper(self):
        widget = QWidget()
        widget.setLayout(layout := QHBoxLayout())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self, stretch=0)
        layout.addWidget(self.list, stretch=1)
        return widget
