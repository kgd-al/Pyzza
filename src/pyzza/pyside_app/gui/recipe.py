from enum import StrEnum

import qtawesome as qta
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QDoubleSpinBox, QTextEdit, \
    QToolButton, QListWidget, QListWidgetItem, QPushButton, QAbstractScrollArea, QCheckBox, QComboBox, QListView, \
    QAbstractItemView

from models.recipe import IngredientsListEntry, DecorationEntry, IngredientEntry, SubrecipeEntry, RecipesDict, Recipe
from pyside_app.gui.icons import Icons
from pyside_app.gui.misc import line, EnumComboBox, icon_label, fa_button
from pyside_app.settings import Settings


def list_item_widget(text: str):
    return QListWidgetItem(qta.icon("mdi.chevron-right"), text)


def ingredient_widget(i: IngredientsListEntry, is_first):
    if isinstance(i, DecorationEntry):
        return QListWidgetItem(("\n" if not is_first else "") + i.text)
    elif isinstance(i, IngredientEntry):
        return list_item_widget(i.pretty_text())

    elif isinstance(i, SubrecipeEntry):
        return QListWidgetItem(qta.icon("fa5s.link"), i.name)

    return QListWidgetItem("Error")


class RecipeDialog(QDialog):
    def __init__(self, parent: QWidget,
                 recipes: RecipesDict, recipe_name: str,
                 scaling: float = 1.0):
        super().__init__(parent=parent)
        self.recipes = recipes
        self.recipe = recipes[recipe_name]

        self.editable = None

        self.status_items, self.status_edit_items = None, None

        self.ingredients_list = QListWidget(self)
        self.ingredients_list_controls = ListControls(self.ingredients_list)

        self.steps_list = QListWidget(self)
        self.steps_list_controls = ListControls(self.steps_list)
        self.steps_list.setWordWrap(True)
        self.steps_list.setEditTriggers(QListWidget.EditTrigger.DoubleClicked)
        self.steps_list.setSpacing(5)

        self.notes = QTextEdit(self)
        self.notes.setPlaceholderText("No notes for this recipe")
        self.notes.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.portions = QDoubleSpinBox(value=scaling * self.recipe.n_portions)

        self.button_edit, self.button_validate = None, None
        buttons = self._make_layout()
        self._fill_in()
        self._set_signals(buttons)
        self._set_editable(False)
        self._set_editable(True)

        self.restore_settings()

    def _make_layout(self):
        r = self.recipe
        layout = QVBoxLayout()

        layout.addLayout(header_centerer := QHBoxLayout(), stretch=0)
        header_centerer.addStretch()
        header_centerer.addLayout(header_layout := QVBoxLayout())
        header_centerer.addStretch()
        header_layout.addWidget(title := QLabel(r.title))
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(line())

        layout.addSpacing(10)

        self.status_items = QWidget()
        self.status_items.setLayout(status_layout := QHBoxLayout())
        status_layout.addStretch()

        self.status_edit_items = QWidget()
        self.status_edit_items.setLayout(status_edit_layout := QHBoxLayout())
        status_edit_layout.addStretch()
        for i in [Recipe.BASIC, Recipe.TYPE, Recipe.REGIMEN, Recipe.DURATION]:
            value = getattr(r, i.name)
            if isinstance(value, bool):
                if value:
                    icon = Icons.BASIC_RECIPE.image()
                else:
                    icon = None
                editor = QCheckBox(i.name.capitalize())
                editor.setChecked(value)

            elif isinstance(value, StrEnum):
                icon = Icons.get_image(value)
                editor = EnumComboBox(type(value), self)
                editor.setCurrentEnum(value)

            else:
                raise RuntimeError(f"Unknown value type: {value}")

            if icon is not None:
                status_layout.addWidget(icon_label(icon))
            status_edit_layout.addWidget(editor)
        status_layout.addStretch()
        status_edit_layout.addStretch()
        header_layout.addWidget(self.status_items)
        header_layout.addWidget(self.status_edit_items)

        ingredients_layout = QVBoxLayout()
        ingredients_layout.addWidget(QLabel("Ingredients:"))

        portions_layout = QHBoxLayout()
        portions_layout.addWidget(self.portions)
        portions_layout.addWidget(QLabel(r.t_portions))
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
        controls_layout.addWidget(b_delete := fa_button("fa5s.trash-alt"))
        controls_layout.addStretch()
        controls_layout.addWidget(b_edit := fa_button("fa5s.edit"))
        controls_layout.addWidget(b_validate := fa_button("fa5s.check-circle"))
        controls_layout.addWidget(b_quit := fa_button("fa5s.sign-out-alt"))
        layout.addLayout(controls_layout)

        self.setLayout(layout)

        self.button_edit = b_edit
        self.button_validate = b_validate
        return b_delete, b_edit, b_validate, b_quit

    def _fill_in(self):
        for i, ingredient in enumerate(self.recipe.ingredients):
            self.ingredients_list.addItem(item := ingredient_widget(ingredient, i == 0))
            if isinstance(ingredient, SubrecipeEntry):
                recipe = ingredient.name
                self.ingredients_list.setItemWidget(item, button := QPushButton(recipe))
                item.setSizeHint(button.sizeHint())
                button.setFixedSize(button.sizeHint())
                button.clicked.connect(
                    lambda: RecipeDialog(self, self.recipes, recipe,
                                         self.portions_scaling()).show())

        for i, step in enumerate(self.recipe.steps):
            self.steps_list.addItem(list_item_widget(step))

        self.notes.setText(self.recipe.notes)

    def _set_signals(self, buttons):
        self.portions.valueChanged.connect(self._portions_changed)
        b_delete, b_edit, b_validate, b_quit = buttons
        b_edit.clicked.connect(lambda: self._set_editable(True))
        b_validate.clicked.connect(lambda: self._set_editable(False))
        b_quit.clicked.connect(self.accept)

    def _portions_changed(self):
        ratio = self.portions_scaling()
        for i, ingredient in enumerate(self.recipe.ingredients):
            if isinstance(ingredient, IngredientEntry):
                item = self.ingredients_list.item(i)
                item.setText(ingredient.pretty_text(ratio))

    def _set_editable(self, editable):
        self.editable = editable

        self.status_items.setVisible(not self.editable)
        self.status_edit_items.setVisible(self.editable)

        self.ingredients_list_controls.setVisible(editable)
        self.steps_list_controls.setVisible(editable)
        self.notes.setReadOnly(not editable)

        self.button_edit.setEnabled(not editable)
        self.button_validate.setEnabled(editable)

        self.setWindowTitle(
            ("Editing" if editable else "Viewing") + f": {self.recipe.title}")

    def portions_scaling(self): return self.portions.value() / self.recipe.n_portions

    def restore_settings(self):
        if geom := Settings.RECIPE_DIALOG_GEOMETRY.get():
            self.restoreGeometry(geom)

    def save_settings(self):
        Settings.RECIPE_DIALOG_GEOMETRY.set(self.saveGeometry())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)


class ListControls(QWidget):
    def __init__(self, parent: QListView):
        super().__init__(parent)

        self.list = parent
        self.list.setDragEnabled(True)
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(add := fa_button("ri.insert-row-bottom"))
        layout.addWidget(rmv := fa_button("ri.delete-row"))
        layout.addWidget(edt := fa_button("fa5s.edit"))
        layout.addSpacing(12)
        layout.addWidget(up := fa_button("ri.arrow-drop-up-line"))
        layout.addWidget(dwn := fa_button("ri.arrow-drop-down-line"))
        layout.addStretch()
        self.add, self.rmv, self.edt, self.up, self.dwn = add, rmv, edt, up, dwn

        parent.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._on_selection_changed()

        # add.clicked.connect(add_callback)
        # rmv.clicked.connect(self.remove)
        # edt.clicked.connect()

    def _on_selection_changed(self):
        selection = self.list.selectionModel().selectedRows()
        any_selected = len(selection) > 0
        for b in [self.rmv, self.edt, self.up, self.dwn]:
            b.setEnabled(any_selected)
        self.up

    def wrapper(self):
        widget = QWidget()
        widget.setLayout(layout := QHBoxLayout())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self, stretch=0)
        layout.addWidget(self.list, stretch=1)
        return widget
