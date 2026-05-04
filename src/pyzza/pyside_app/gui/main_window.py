from pathlib import Path

import qtawesome as qta

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QTableWidget, QVBoxLayout, QLineEdit, QWidget, QTableView, \
    QFileDialog, QHeaderView, QStyle, QPushButton, QWidgetAction

from models.recipe import load_recipes
from pyside_app.gui.filters import FilterView
from pyside_app.gui.recipe import RecipeDialog
from pyside_app.models.recipes import RecipesModel, RecipesProxyModel
from pyside_app.settings import Settings
from pyside_app.gui.sync import SyncDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recipes = {}

        self.splitter = QSplitter()

        self.filters = FilterView()

        self.table = QTableView()
        self.proxy_model = RecipesProxyModel(self.filters.filter)
        self._make_table()

        self._make_menu()
        self._make_layout()
        self._make_signals()

        if last := Settings.LAST_FILE.get():
            self.load(last)
        self.restore_settings()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def _make_menu(self):
        menu = self.menuBar()

        def action(parent, text,
                   icon=None, checkable=False,
                   shortcut=None,
                   fn=None):
            _a = QAction(text, self)
            if icon:
                _a.setIcon(qta.icon(icon))
            _a.setCheckable(checkable)
            if shortcut:
                _a.setShortcut(shortcut)
            if fn:
                _a.triggered.connect(fn)
            parent.addAction(_a)
            return _a

        file_menu = menu.addMenu("File")

        action(file_menu, "Load", "fa5s.folder-open", shortcut="Ctrl+O", fn=self.load_new_file)
        action(file_menu, "Save", "fa5s.save", shortcut="Ctrl+S")
        action(file_menu, "Print", "fa5s.print", shortcut="Ctrl+P")
        action(file_menu, "Quit", "fa5s.power-off", fn=self.close)

        # --
        recipe_menu = menu.addMenu("Recipes")

        add_recipe = action(recipe_menu, "Add", "fa5s.plus", shortcut="Ctrl+N")

        # --
        filters_menu = menu.addMenu("Filters")

        show_filters = action(
            filters_menu, "Show", 'fa5s.search', checkable=True, shortcut="Ctrl+F",
            fn=lambda on: self.splitter.widget(1).setVisible(on)
        )
        show_filters.setChecked(True)
        self.splitter.splitterMoved.connect(
            lambda: show_filters.setChecked(self.splitter.sizes()[1] > 0)
        )

        action(
            filters_menu, "Clear", 'fa5s.times-circle', shortcut="Ctrl+Shift+F",
            fn=self.filters.unset
        )

        # --
        misc_menu = menu.addMenu("Misc")

        sync = action(misc_menu, "Sync", "fa5s.sync")
        sync.triggered.connect(lambda: SyncDialog().exec())

        about = action(misc_menu, "About", "fa5s.info-circle")

    def _make_layout(self):
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.filters)
        self.splitter.setCollapsible(0, False)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.setCentralWidget(self.splitter)

    def _make_signals(self):
        self.filters.filter_changed.connect(self.on_filter_changed)
        self.table.doubleClicked.connect(self.on_recipe_clicked)

    def _make_table(self):
        self.proxy_model.setDynamicSortFilter(True)
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)
        self.table.setModel(self.proxy_model)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        self.table.setTabKeyNavigation(False)

        self.table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)

    def load(self, path: Path):
        self.recipes = load_recipes(path)
        self.proxy_model.setSourceModel(RecipesModel(self.recipes))
        self.table.setCurrentIndex(QModelIndex())

    def load_new_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File",
            dir=str(Settings.LAST_FILE.get()),
            filter="Cookbook (*.rbk)",
            # options=QFileDialog.Option.DontUseNativeDialog
        )
        path = Path(path)
        if not path.exists() or not path.is_file():
            return

        self.load(path)
        Settings.LAST_FILE.set(path)

    def on_recipe_clicked(self, index):
        item = self.proxy_model.recipe_title(index)
        recipe = self.recipes[item]
        RecipeDialog(self, recipe).exec()

    def on_filter_changed(self):
        self.proxy_model.invalidateFilter()
        if self.recipes:
            shown, total = self.proxy_model.rowCount(), len(self.recipes)
            title = f"Pyzza Cookbook - {shown} recipes"
            if shown < total:
                title += f" (out of {total})"
            self.setWindowTitle(title)

    def restore_settings(self):
        if geom := Settings.WINDOW_GEOMETRY.get():
            self.restoreGeometry(geom)
        if state := Settings.WINDOW_STATE.get():
            self.restoreState(state)
        if sorting := Settings.RECIPES_SORTING.get():
            self.table.sortByColumn(sorting[0], sorting[1])
        if filtering := Settings.RECIPES_FILTERING.get():
            self.filters.restore_state(filtering)

    def save_settings(self):
        Settings.WINDOW_GEOMETRY.set(self.saveGeometry())
        Settings.WINDOW_STATE.set(self.saveState())
        Settings.RECIPES_SORTING.set((self.proxy_model.sortColumn(), self.proxy_model.sortOrder()))
        Settings.RECIPES_FILTERING.set(self.filters.save_state())
