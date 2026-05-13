from dataclasses import fields
from enum import StrEnum
from typing import Dict

from PySide6 import QtCore
from PySide6.QtCore import Qt, QSize, QSortFilterProxyModel, QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QIcon

from models.recipe import Recipe, RecipeBook, DishType, Regimen, Duration
from pyside_app.gui.icons import Icons


class RecipesModel(QtCore.QAbstractTableModel):
    def __init__(self, book: RecipeBook):
        super().__init__()
        self._data = book.recipes

    def _index(self): return list(self._data.keys())

    def recipe(self, i: int | QModelIndex | QPersistentModelIndex):
        if not isinstance(i, int):
            i = i.row()
        return self._data[self._index()[i]]

    def row(self, recipe: Recipe):
        return self._index().index(recipe.title)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        def get(): return RecipeTupleView.data(self.recipe(index), index.column())
        if role == Qt.ItemDataRole.DisplayRole and isinstance(r := get(), str):
            return r
        elif role == Qt.ItemDataRole.DecorationRole and isinstance(r := get(), QIcon):
            return r
        elif role == Qt.ItemDataRole.SizeHintRole:
            return RecipeTupleView.column_size(index.column())
        elif role == Qt.ItemDataRole.UserRole:
            return RecipeTupleView.sort_key(self.recipe(index), index.column())

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation != Qt.Orientation.Horizontal:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return RecipeTupleView.header(section)
        elif role == Qt.ItemDataRole.SizeHintRole:
            return RecipeTupleView.header_size(section)
        return None

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, index=QtCore.QModelIndex()):
        return RecipeTupleView.columns()

    def recipe_changed(self, recipe: Recipe):
        row = self.row(recipe)
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount()-1))

    def recipe_added(self, recipe: Recipe):
        row = self.rowCount()-1
        self.beginInsertRows(QModelIndex(), row, row)
        self.insertRow(row, QModelIndex())
        self.endInsertRows()

    def recipe_deleted(self, row: int):
        self.beginRemoveRows(QModelIndex(), row, row)
        self.removeRow(row)
        self.endRemoveRows()


class RecipesProxyModel(QSortFilterProxyModel):
    def __init__(self, filterer, parent=None):
        super().__init__(parent)
        self._filterer = filterer

    def filterAcceptsRow(self, source_row, source_parent):
        recipe = self.sourceModel().recipe(source_row)
        return self._filterer(recipe)

    def recipe_title(self, index):
        return self.data(self.index(index.row(), RecipeTupleView.title_column()))


class RecipeTupleView:
    COLUMNS = [Recipe.BASIC, Recipe.TYPE, Recipe.REGIMEN, Recipe.DURATION, Recipe.TITLE]

    @classmethod
    def columns(cls): return len(cls.COLUMNS)

    @classmethod
    def data(cls, recipe: Recipe, index: int):
        value = cls._value(recipe, index)
        if isinstance(value, str) and not isinstance(value, StrEnum):
            return value
        elif isinstance(value, bool):
            return Icons.BASIC_RECIPE.image() if value else None
        else:
            return Icons.get_image(value)

    @classmethod
    def sort_key(cls, recipe: Recipe, index: int):
        return cls._value(recipe, index)

    @classmethod
    def _value(cls, recipe: Recipe, index: int):
        return getattr(recipe, cls.COLUMNS[index].name)

    @classmethod
    def is_title(cls, col: int): return col == cls.title_column()

    @classmethod
    def header(cls, col: int): return "Name" if cls.is_title(col) else None

    @classmethod
    def column_size(cls, index): return None if cls.is_title(index) else QSize(0, 0)

    @classmethod
    def header_size(cls, index): return None if cls.is_title(index) else QSize(cls.icon_size(), cls.icon_size())

    @classmethod
    def icon_size(cls): return 32

    @classmethod
    def title_column(cls): return cls.COLUMNS.index(Recipe.TITLE)

#
# valid_fields = {f.name for f in fields(Recipe)}
# assert all(col in valid_fields for col in RecipeTupleView.COLUMNS)
