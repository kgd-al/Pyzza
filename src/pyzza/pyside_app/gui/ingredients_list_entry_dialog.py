import math

import qtawesome as qta
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor, Qt
from PySide6.QtWidgets import QDialog, QWidget, QTabWidget, QVBoxLayout, QDialogButtonBox, QHBoxLayout, QLineEdit, \
    QComboBox, QCompleter, QDoubleSpinBox

from ...models.recipe import DecorationEntry, IngredientsListEntry, SubrecipeEntry, IngredientEntry, RecipeBook


def editable_combobox(items, allow_inserts):
    cb = QComboBox()
    cb.addItems(items)
    cb.setEditable(True)
    cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

    completer = QCompleter(items)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    if allow_inserts:
        cb.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
    else:
        cb.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    cb.setCompleter(completer)

    return cb


class IngredientsListEntryDialog(QDialog):
    def __init__(self, entry: IngredientsListEntry, book: RecipeBook, parent: QWidget = None):
        super().__init__(parent)
        self._entry = entry
        self._book = book

        self.tabs = QTabWidget()
        self.widgets = {
            IngredientEntry: QWidget(),
            DecorationEntry: QWidget(),
            SubrecipeEntry: QWidget(),
        }
        header = {
            IngredientEntry: ("Ingredient", "mdi.food-drumstick"),
            DecorationEntry: ("Decoration", "ei.star"),
            SubrecipeEntry: ("Sub-recipe", "fa5s.link"),
        }
        self.elements = dict()

        for entry_type, widget in self.widgets.items():
            label, icon = header.get(entry_type)
            self.tabs.addTab(widget, qta.icon(icon), label)

            fn_name = f"_build_{entry_type.__name__.replace('Entry', '').lower()}_tab"
            getattr(self, fn_name)(entry_type, widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)
        self.setLayout(layout)

        self._fill_in(entry)

    def _fill_in(self, entry):
        self.tabs.setCurrentWidget(self.widgets[entry.__class__])
        elements = self.elements[entry.__class__]
        if isinstance(entry, IngredientEntry):
            amount, unit, name, qualif = elements
            amount.setValue(entry.amount)
            unit.setCurrentText(entry.unit)
            name.setCurrentText(entry.name)
            qualif.setText(entry.qualif)
        elif isinstance(entry, DecorationEntry):
            elements[0].setText(entry.text)
        elif isinstance(entry, SubrecipeEntry):
            elements[0].setCurrentText(entry.name)

        def _select():
            elements[0].setFocus()
            if isinstance(elements[0], QDoubleSpinBox):
                elements[0].selectAll()
        QTimer.singleShot(0, _select)

    def _build_ingredient_tab(self, entry, widget):
        self.elements[entry] = [
            amount := QDoubleSpinBox(),
            unit := editable_combobox(list(self._book.units), allow_inserts=True),
            name := editable_combobox(list(self._book.ingredients), allow_inserts=True),
            qualif := QLineEdit()
        ]
        amount.setMaximum(math.inf)
        amount.setDecimals(0)
        qualif.setMinimumWidth(100)
        layout = QHBoxLayout()
        for e in self.elements[entry]:
            layout.addWidget(e)
        widget.setLayout(layout)

    def _build_decoration_tab(self, entry, widget):
        self.elements[entry] = [text := QLineEdit()]

        text.setPlaceholderText("Enter some text")

        layout = QHBoxLayout()
        layout.addWidget(text)
        widget.setLayout(layout)

    def _build_subrecipe_tab(self, entry, widget):
        self.elements[entry] = [
            cb := editable_combobox(list(self._book.recipes.keys()), allow_inserts=False),
        ]

        layout = QHBoxLayout()
        layout.addWidget(cb)
        widget.setLayout(layout)

    def showEvent(self, e):
        geom = self.frameGeometry()
        geom.moveCenter(QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(e)

    def entry(self):
        tab = self.tabs.currentWidget()
        entry_type = {v: k for k, v in self.widgets.items()}[tab]
        elements = self.elements[entry_type]
        if entry_type is IngredientEntry:
            amount, unit, name, qualif = elements
            return IngredientEntry(
                amount=amount.value(), unit=unit.currentText(),
                name=name.currentText(), qualif=qualif.text())
        elif entry_type is DecorationEntry:
            return DecorationEntry(text=elements[0].text())
        elif entry_type is SubrecipeEntry:
            return SubrecipeEntry(name=elements[0].currentText())
        return None
