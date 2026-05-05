import dataclasses
import re

from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import QWidget, QLineEdit, QLabel, QCheckBox, QGridLayout, QListWidget

from models.recipe import DishType, Regimen, Duration, Recipe
from pyside_app.gui.misc import line, YesNoGroupBox, EnumComboBox


class FilterView(QWidget):
    filter_changed = Signal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.title_filter = QLineEdit(self)
        self.title_filter.setPlaceholderText("Filter by recipe name")

        self.basic_filter = YesNoGroupBox(self)
        self.subrecipe_filter = YesNoGroupBox(self)

        self.type_filter = EnumComboBox(DishType, self)
        self.regimen_filter = EnumComboBox(Regimen, self)
        self.duration_filter = EnumComboBox(Duration, self)

        self.ingredients_filter = QListWidget(self)
        self.subrecipes_filter = QListWidget(self)
        self.ingredients_filter.addItem("Not implemented. Useful?")
        self.subrecipes_filter.addItem("Not implemented. Useful?")

        recipe_fields = {f.name: f for f in dataclasses.fields(Recipe)}

        self.contents = {
            filter_widget: (
                QCheckBox(label), filter_widget,
                recipe_fields.get(field, None)
            )
            for filter_widget, label, field in [
                (self.title_filter, "Name:", "title"),
                (self.basic_filter, "Basic?", "basic"),
                (self.subrecipe_filter, "Sub recipe?", "is_sub_recipe"),
                (self.type_filter, "Type", "type"),
                (self.regimen_filter, "Regimen", "regimen"),
                (self.duration_filter, "Duration", "duration"),
                (self.ingredients_filter, "Ingredients", "ingredients"),
                (self.subrecipes_filter, "Sub recipes", None),
            ]}

        filter_layout = QGridLayout()
        filter_layout.setHorizontalSpacing(4)
        filter_layout.setVerticalSpacing(8)
        filter_layout.addWidget(QLabel("Set filtering criteria"), 0, 0, 1, 2)
        filter_layout.addWidget(line(), 1, 0, 1, 2)
        for i, (checkbox, widget, field) in enumerate(self.contents.values(), 2):
            checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            filter_layout.addWidget(checkbox, i, 0)
            filter_layout.addWidget(widget, i, 1)

            checkbox.toggled.connect(self.emit_filter_changed)
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self.emit_filter_changed)
            elif isinstance(widget, YesNoGroupBox):
                widget.toggled.connect(self.emit_filter_changed)
            elif isinstance(widget, EnumComboBox):
                widget.currentTextChanged.connect(self.emit_filter_changed)
            # Ingredients and subrecipes are not implemented

        self.setLayout(filter_layout)

        # Disabled for now
        for disabled in [self.ingredients_filter, self.subrecipes_filter]:
            disabled.setEnabled(False)
            self.contents.get(disabled)[0].setEnabled(False)

    def unset(self):
        with QSignalBlocker(self):
            for checkbox, _, _ in self.contents.values():
                checkbox.setChecked(False)
        self.filter_changed.emit()

    def emit_filter_changed(self):
        source = self.sender()
        if (entry := self.contents.get(source)) is not None:
            if not entry[0].isChecked():
                return
        self.filter_changed.emit()

    def filter(self, r: Recipe):
        for checkbox, widget, field in self.contents.values():
            if not checkbox.isChecked():
                continue

            if field is None:
                continue
            value = getattr(r, field.name)

            if isinstance(widget, QLineEdit):
                if re.search(widget.text(), r.title, re.IGNORECASE) is None:
                    return False

            elif isinstance(widget, YesNoGroupBox):
                if value != widget.value():
                    return False

            elif isinstance(widget, EnumComboBox):
                if value.capitalize() != widget.currentText():
                    return False

        return True

    def save_state(self):
        state = []
        for checkbox, widget, _ in self.contents.values():
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, YesNoGroupBox):
                value = widget.state()
            elif isinstance(widget, EnumComboBox):
                value = widget.currentIndex()
            else:
                value = None
            state.append((checkbox.isChecked(), value))
        return state

    def restore_state(self, state):
        for (checkbox, widget, _), (checked, value) in zip(self.contents.values(), state):
            checkbox.setChecked(checked)
            if isinstance(widget, QLineEdit):
                widget.setText(value)
            elif isinstance(widget, YesNoGroupBox):
                widget.set_state(value)
            elif isinstance(widget, EnumComboBox):
                widget.setCurrentIndex(value)
            else:
                pass
