from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTextEdit, QAbstractItemDelegate, QStyledItemDelegate

from pyside_app.gui.ingredients_list_entry_dialog import IngredientsListEntryDialog


class StepsListDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index, /):
        return QTextEdit(parent)

    def setModelData(self, editor: QTextEdit, model, index, /):
        model.setData(index, editor.toPlainText())

    def eventFilter(self, editor: QTextEdit, e: QEvent):
        if (isinstance(e, QKeyEvent) and e.modifiers() & Qt.KeyboardModifier.ControlModifier
                and e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.SubmitModelCache)
            return False
        return super().eventFilter(editor, e)


class IngredientsListDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index, /):
        return IngredientsListEntryDialog(parent)

    def setModelData(self, editor: IngredientsListEntryDialog, model, index, /):
        entry = editor.entry()
        model.setData(index, entry.pretty_text())
