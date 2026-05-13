from enum import StrEnum

import qtawesome as qta
from PySide6.QtCore import QSize, Signal, QSignalBlocker
from PySide6.QtGui import Qt, QFontMetrics, QKeySequence
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QDoubleSpinBox, QTextEdit, \
    QListWidget, QListWidgetItem, QPushButton, QAbstractScrollArea, QCheckBox, QLineEdit, QSlider, QMessageBox

from models.recipe import IngredientsListEntry, DecorationEntry, IngredientEntry, SubrecipeEntry, Recipe, \
    RecipeBook
from pyside_app.gui.delegates import IngredientsListDelegate, StepsListDelegate
from pyside_app.gui.icons import Icons
from pyside_app.gui.list_controls import ListControls
from pyside_app.gui.misc import line, EnumComboBox, fa_button, set_icon
from pyside_app.settings import Settings


def set_header_font(widget):
    font = widget.font()
    font.setBold(True)
    font.setPointSize(font.pointSize() + 2)
    widget.setFont(font)
    widget.setAlignment(Qt.AlignmentFlag.AlignCenter)


def list_item_widget(text: str, editable=True) -> QListWidgetItem:
    item = QListWidgetItem(qta.icon("mdi.chevron-right"), text)
    if editable:
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
    return item


def ingredient_widget(i: IngredientsListEntry, editable=True):
    if isinstance(i, DecorationEntry):
        item = DecorationItem(i.text)
    elif isinstance(i, IngredientEntry):
        item = list_item_widget(i.pretty_text())
    elif isinstance(i, SubrecipeEntry):
        item = QListWidgetItem(qta.icon("fa5s.link"), i.name)

    else:
        return QListWidgetItem("Error")

    if editable:
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
    item.setData(Qt.ItemDataRole.UserRole, i)

    return item


class DecorationItem(QListWidgetItem):
    def __init__(self, text):
        super().__init__(text)

    def maybe_adjust_height(self, row: int):
        fm = QFontMetrics(self.font())
        self.setSizeHint(QSize(0, round((1.5 if row > 0 else 1) * fm.height())))
        self.setTextAlignment(Qt.AlignmentFlag.AlignBottom)


class RecipeDialog(QDialog):
    edit_validated = Signal(Recipe)

    def __init__(self, parent: QWidget,
                 book: RecipeBook, recipe_name: str,
                 scaling: float = 1.0):
        super().__init__(parent=parent)
        self.book = book
        self.recipe = self.book.recipes[recipe_name]

        self.editable, self.edited = None, False

        self.viewers, self.editors = dict(), dict()

        self.viewers[Recipe.TITLE], self.editors[Recipe.TITLE] = QLabel(), QLineEdit()

        self.ingredients_list = QListWidget(self)
        self.ingredients_list_controls = ListControls(
            self.ingredients_list,
            lambda: ingredient_widget(IngredientEntry(amount=0, unit=IngredientEntry.NO_UNIT, name="", qualif="")),
            # lambda: ingredient_widget(DecorationEntry(text="")),
            # lambda: ingredient_widget(SubrecipeEntry(name="")),
            "Ctrl+I"
        )
        self.ingredients_list.setItemDelegate(IngredientsListDelegate(self.book, self))

        self.steps_list = QListWidget(self)
        self.steps_list_controls = ListControls(
            self.steps_list, lambda: list_item_widget(""))
        self.steps_list.setItemDelegate(StepsListDelegate(self))
        self.steps_list.setWordWrap(True)
        self.steps_list.setSpacing(5)

        self.notes = QTextEdit(self)
        self.notes.setPlaceholderText("No notes for this recipe")
        self.notes.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        portions = QDoubleSpinBox(value=scaling * self.recipe.n_portions)
        self.viewers[Recipe.N_PORTIONS] = self.editors[Recipe.N_PORTIONS] = portions

        self.button_edit, self.button_validate = None, None
        buttons = self._make_layout()
        self._fill_in()
        self._set_signals(buttons)
        self.set_editable(False)

        self._adjust_decorations_heights()

        self.restore_settings()

    def _make_layout(self):
        r = self.recipe
        layout = QVBoxLayout()

        layout.addLayout(header_centerer := QHBoxLayout(), stretch=0)
        header_centerer.addStretch()
        header_centerer.addLayout(header_layout := QVBoxLayout())
        header_centerer.addStretch()
        header_layout.addWidget(title_viewer := self.viewers[Recipe.TITLE])
        set_header_font(title_viewer)
        header_layout.addWidget(title_editor := self.editors[Recipe.TITLE])
        set_header_font(title_editor)
        header_layout.addWidget(line())

        layout.addSpacing(10)

        self.status_items_holder = QWidget()
        self.status_items_holder.setLayout(status_layout := QHBoxLayout())
        status_layout.addStretch()

        self.status_edit_items_holder = QWidget()
        self.status_edit_items_holder.setLayout(status_edit_layout := QHBoxLayout())
        status_edit_layout.addStretch()
        for i in [Recipe.BASIC, Recipe.TYPE, Recipe.REGIMEN, Recipe.DURATION]:
            value = getattr(r, i.name)
            viewer = QLabel()
            if isinstance(value, bool):
                editor = QCheckBox(i.name.capitalize())

            elif isinstance(value, StrEnum):
                editor = EnumComboBox(type(value), self)

            else:
                raise RuntimeError(f"Unknown value type: {value}")

            self.viewers[i] = viewer
            status_layout.addWidget(viewer)

            self.editors[i] = editor
            status_edit_layout.addWidget(editor)

        status_layout.addStretch()
        status_edit_layout.addStretch()
        header_layout.addWidget(self.status_items_holder)
        header_layout.addWidget(self.status_edit_items_holder)

        ingredients_layout = QVBoxLayout()
        ingredients_layout.addWidget(QLabel("Ingredients:"))

        portions_layout = QHBoxLayout()
        portions_layout.addWidget(self.editors[Recipe.N_PORTIONS])
        self.viewers[Recipe.T_PORTIONS], self.editors[Recipe.T_PORTIONS] = QLabel(), QLineEdit()
        portions_layout.addWidget(self.viewers[Recipe.T_PORTIONS])
        portions_layout.addWidget(self.editors[Recipe.T_PORTIONS])
        portions_layout.addStretch()
        ingredients_layout.addLayout(portions_layout)

        ingredients_layout.addWidget(self.ingredients_list_controls.wrapper())

        mid_layout = QHBoxLayout()
        mid_layout.addLayout(ingredients_layout)
        mid_layout.addWidget(self.steps_list_controls.wrapper())
        layout.addLayout(mid_layout, stretch=20)

        layout.addWidget(self.notes, stretch=0)

        layout.addSpacing(10)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(b_delete := fa_button("fa5s.trash-alt", color="black"))
        controls_layout.addStretch()
        controls_layout.addWidget(b_edit := fa_button("fa5s.edit"))
        controls_layout.addWidget(b_validate := fa_button("fa5s.check-circle"))
        controls_layout.addWidget(b_quit := fa_button("fa5s.sign-out-alt"))
        layout.addLayout(controls_layout)

        self.setLayout(layout)

        self.button_edit = b_edit
        self.button_validate = b_validate
        b_delete.setStyleSheet("background-color: red")
        return b_delete, b_edit, b_validate, b_quit

    def _validate(self):
        self.edited = False

        def _process_ingredients():
            l = self.ingredients_list
            return [l.item(j).data(Qt.ItemDataRole.UserRole) for j in range(l.count())]

        def _process_steps():
            l = self.steps_list
            return [l.item(j).text() for j in range(l.count())]

        original_title = self.recipe.title
        self.recipe.title = self.editors[Recipe.TITLE].text()

        self.recipe.basic = self.editors[Recipe.BASIC].isChecked()
        self.recipe.type = self.editors[Recipe.TYPE].currentEnum()
        self.recipe.regimen = self.editors[Recipe.REGIMEN].currentEnum()
        self.recipe.duration = self.editors[Recipe.DURATION].currentEnum()

        self.recipe.n_portions = self.editors[Recipe.N_PORTIONS].value()
        self.recipe.t_portions = self.editors[Recipe.T_PORTIONS].text()

        self.recipe.ingredients = _process_ingredients()
        self.recipe.steps = _process_steps()
        self.recipe.notes = self.notes.toPlainText()

        if original_title != self.recipe.title:
            self.book.recipes[self.recipe.title] = r = self.book.recipes.pop(original_title)
            assert id(r) == id(self.recipe)

            for r in self.book.recipes.values():
                for i in r.ingredients:
                    if isinstance(i, SubrecipeEntry) and i.name == original_title:
                        i.name = self.recipe.title

        self._fill_in()
        self.set_editable(False)

        self.edit_validated.emit(self.recipe)

    def _fill_in(self):
        r = self.recipe

        def _set(f, fn, _value):
            getattr(self.viewers[f], fn)(_value)
            getattr(self.editors[f], fn)(_value)

        # with QSignalBlocker(self):
        _set(Recipe.TITLE, "setText", r.title)

        for i in [Recipe.BASIC, Recipe.TYPE, Recipe.REGIMEN, Recipe.DURATION]:
            value = getattr(r, i.name)
            viewer, editor = self.viewers[i], self.editors[i]
            if isinstance(value, bool):
                if value:
                    set_icon(viewer, Icons.BASIC_RECIPE.image())
                else:
                    viewer.setVisible(False)
                editor.setChecked(value)

            elif isinstance(value, StrEnum):
                set_icon(viewer, Icons.get_image(value))
                editor.setCurrentEnum(value)

        self.editors[Recipe.N_PORTIONS].setValue(r.n_portions)
        _set(Recipe.T_PORTIONS, "setText", r.t_portions)

        with QSignalBlocker(self.ingredients_list.model()):
            self.ingredients_list.clear()
            for i, ingredient in enumerate(self.recipe.ingredients):
                self.ingredients_list.addItem(item := ingredient_widget(ingredient))
                if isinstance(ingredient, SubrecipeEntry):
                    recipe = ingredient.name
                    self.ingredients_list.setItemWidget(item, button := QPushButton(recipe))
                    item.setSizeHint(button.sizeHint())
                    button.setFixedSize(button.sizeHint())

                    def show_subrecipe():
                        rd = RecipeDialog(self, self.book, recipe, self.portions_scaling())
                        rd.edit_validated.connect(self.edit_validated)
                        rd.edit_validated.connect(self._fill_in)
                        rd.show()

                    button.clicked.connect(show_subrecipe)

        with QSignalBlocker(self.steps_list.model()):
            self.steps_list.clear()
            for i, step in enumerate(self.recipe.steps):
                self.steps_list.addItem(list_item_widget(step))

        with QSignalBlocker(self.notes):
            self.notes.setText(self.recipe.notes)

        self._update_title()

    def _set_signals(self, buttons):
        self.editors[Recipe.N_PORTIONS].valueChanged.connect(self._portions_changed)
        b_delete, b_edit, b_validate, b_quit = buttons
        b_edit.clicked.connect(lambda: self.set_editable(True))
        b_validate.clicked.connect(self._validate)
        b_quit.clicked.connect(self.accept)

        model_signals = ["dataChanged", "rowsInserted", "rowsMoved", "rowsRemoved"]
        model = self.ingredients_list.model()
        for signal_name in model_signals:
            getattr(model, signal_name).connect(self._adjust_decorations_heights)

        # Register any modification
        for field, e in self.editors.items():
            if isinstance(e, QLineEdit):
                e.textEdited.connect(self._on_edit)
            elif isinstance(e, QDoubleSpinBox):
                if field != Recipe.N_PORTIONS:
                    e.valueChanged.connect(self._on_edit)
                else:
                    e.valueChanged.connect(lambda: self._on_edit() if self.editable else None)
            elif isinstance(e, QCheckBox):
                e.checkStateChanged.connect(self._on_edit)
            elif isinstance(e, EnumComboBox):
                e.currentIndexChanged.connect(self._on_edit)
            else:
                raise RuntimeError(f"Unknown signal editor of type {type(e)} for {field.name}")

        for signal_name in model_signals:
            for l in [self.ingredients_list, self.steps_list]:
                getattr(l.model(), signal_name).connect(self._on_edit)

        self.notes.textChanged.connect(self._on_edit)

    def _portions_changed(self):
        ratio = self.portions_scaling()
        with QSignalBlocker(self.ingredients_list.model()):
            for i, ingredient in enumerate(self.recipe.ingredients):
                if isinstance(ingredient, IngredientEntry):
                    item = self.ingredients_list.item(i)
                    item.setText(ingredient.pretty_text(ratio))

    def _adjust_decorations_heights(self):
        with QSignalBlocker(self.ingredients_list.model()):
            for i in range(self.ingredients_list.count()):
                if isinstance(e := self.ingredients_list.item(i), DecorationItem):
                    e.maybe_adjust_height(i)

    def set_editable(self, editable):
        self.editable = editable
        if editable:  # Ensure that viewing different portions does not change the default
            self.editors[Recipe.N_PORTIONS].setValue(self.recipe.n_portions)

        self.viewers[Recipe.TITLE].setVisible(not editable)
        self.editors[Recipe.TITLE].setVisible(editable)

        self.viewers[Recipe.T_PORTIONS].setVisible(not editable)
        self.editors[Recipe.T_PORTIONS].setVisible(editable)

        self.status_items_holder.setVisible(not self.editable)
        self.status_edit_items_holder.setVisible(self.editable)

        self.ingredients_list_controls.setVisible(editable)
        self.steps_list_controls.setVisible(editable)
        self.notes.setReadOnly(not editable)

        self.button_edit.setEnabled(not editable)
        self.button_validate.setEnabled(editable)

        self._update_title()

    def portions_scaling(self): return self.editors[Recipe.N_PORTIONS].value() / self.recipe.n_portions

    def restore_settings(self):
        if geom := Settings.RECIPE_DIALOG_GEOMETRY.get():
            self.restoreGeometry(geom)

    def save_settings(self):
        Settings.RECIPE_DIALOG_GEOMETRY.set(self.saveGeometry())

    def accept(self):
        if self._on_close(QDialog.DialogCode.Accepted):
            super().accept()

    def reject(self, /):
        if self._on_close(QDialog.DialogCode.Rejected):
            super().reject()

    def _update_title(self):
        self.setWindowTitle(
            ("Editing" if self.editable else "Viewing")
            + f": {self.recipe.title}"
            + ("*" if self.edited else "")
        )

    def _on_edit(self):
        self.edited = True
        self._update_title()

    def _on_close(self, status: QDialog.DialogCode):
        yes, no, cancel = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No, QMessageBox.StandardButton.Cancel
        if self.edited:
            answer = QMessageBox.question(
                self, "Unsaved", "Confirm changes before closing?",
                yes | no | cancel, yes if status == QDialog.DialogCode.Accepted else no
            )
            if answer == QMessageBox.StandardButton.Yes:
                self._validate()
                close = True
            elif answer == QMessageBox.StandardButton.No:
                close = True
            else:
                close = False
        else:
            close = True

        self.save_settings()

        return close
