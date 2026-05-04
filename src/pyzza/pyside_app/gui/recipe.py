from enum import StrEnum

import qtawesome as qta

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QWidget, QDoubleSpinBox, QListView, QTextEdit, \
    QToolButton

from models.recipe import Recipe
from pyside_app.gui.icons import Icons
from pyside_app.gui.misc import line


def icon_label(icon: QIcon, size=32):
    label = QLabel()
    label.setPixmap(icon.pixmap(size, size))
    label.setFixedSize(size, size)
    return label


def fa_button(name: str):
    button = QToolButton()
    button.setIcon(qta.icon(name))
    return button


class RecipeDialog(QDialog):
    def __init__(self, parent: QWidget, recipe: Recipe):
        super().__init__(parent=parent)
        self.recipe = recipe

        self.ingredients_list = QListView(self)
        self.steps_list = QListView(self)
        self.notes = QTextEdit(self)

        self.portions = QDoubleSpinBox(value=recipe.n_portions)

        b_delete, b_edit, b_validate, b_quit = self._make_layout()
        self._fill_in()

        self.setWindowTitle(f"Viewing: {recipe.title}")

        b_quit.clicked.connect(self.accept)

    def _make_layout(self):
        r = self.recipe
        layout = QVBoxLayout()

        layout.addWidget(title := QLabel(r.title))
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)
        layout.addWidget(line())

        icons_layout = QHBoxLayout()
        icons_layout.addStretch()
        for i in [r.basic, r.type, r.regimen, r.duration]:
            if isinstance(i, bool):
                icon = Icons.BASIC_RECIPE.image() if i else QIcon()
            else:
                icon = Icons.get_image(i)
            icons_layout.addWidget(icon_label(icon))
        icons_layout.addStretch()
        layout.addLayout(icons_layout)

        ingredients_layout = QVBoxLayout()
        ingredients_layout.addWidget(QLabel("Ingredients:"))

        portions_layout = QHBoxLayout()
        portions_layout.addWidget(self.portions)
        portions_layout.addWidget(QLabel(r.t_portions))
        portions_layout.addStretch()
        ingredients_layout.addLayout(portions_layout)

        ingredients_layout.addWidget(self.ingredients_list)

        mid_layout = QHBoxLayout()
        mid_layout.addLayout(ingredients_layout)
        mid_layout.addWidget(self.steps_list)
        layout.addLayout(mid_layout)

        layout.addWidget(self.notes)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(b_delete := fa_button("fa5s.trash-alt"))
        controls_layout.addStretch()
        controls_layout.addWidget(b_edit := fa_button("fa5s.edit"))
        controls_layout.addWidget(b_validate := fa_button("fa5s.check-circle"))
        controls_layout.addWidget(b_quit := fa_button("fa5s.sign-out-alt"))
        layout.addLayout(controls_layout)

        self.setLayout(layout)

        return b_delete, b_edit, b_validate, b_quit

    def _fill_in(self):
        
