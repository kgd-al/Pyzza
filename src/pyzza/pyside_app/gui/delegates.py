from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QTextEdit, QAbstractItemDelegate, QStyledItemDelegate, QDialog

from .ingredients_list_entry_dialog import IngredientsListEntryDialog
from ...models.recipe import RecipeBook


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
    def __init__(self, book: RecipeBook, parent=None):
        super().__init__(parent)
        self._book = book

    def createEditor(self, parent, option, index, /):
        return IngredientsListEntryDialog(
            entry=index.data(Qt.ItemDataRole.UserRole),
            book=self._book, parent=parent)

    def setModelData(self, editor: IngredientsListEntryDialog, model, index, /):
        if editor.result() == QDialog.DialogCode.Rejected:
            self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.RevertModelCache)
            return
        entry = editor.entry()
        model.setData(index, entry.pretty_text())
        model.setData(index, entry, role=Qt.ItemDataRole.UserRole)
