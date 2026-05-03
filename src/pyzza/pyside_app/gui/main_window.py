from pathlib import Path

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QTableWidget, QVBoxLayout, QLineEdit, QWidget, QTableView, \
    QFileDialog, QHeaderView

from models.recipe import load_recipes
from pyside_app.gui.filters import FilterView
from pyside_app.models.recipes import RecipesModel, RecipesProxyModel
from pyside_app.settings import Settings
from pyside_app.gui.sync import SyncDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._make_menu()

        self.recipes = {}

        self.splitter = QSplitter()

        self.filters = FilterView()

        self.table = QTableView()
        self.proxy_model = RecipesProxyModel(self.filters.filter)
        self._make_table()

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

        load_action = menu.addAction("Load")
        load_action.triggered.connect(self.load_new_file)
        menu.addAction(load_action)

        sync_action = QAction("Sync", self)
        sync_action.triggered.connect(lambda: SyncDialog().exec())
        menu.addAction(sync_action)

    def _make_layout(self):
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.filters)
        self.setCentralWidget(self.splitter)

    def _make_signals(self):
        self.filters.filter_changed.connect(self.on_filter_changed)

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
            dir=Settings.LAST_DIRECTORY.get(),
            filter="*.rbk"
        )
        path = Path(path)
        self.load(path)
        Settings.LAST_FILE.set(path)
        Settings.LAST_DIRECTORY.set(path.parent)

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
