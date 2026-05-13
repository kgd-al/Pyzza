from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QModelIndex, QTimer
from PySide6.QtGui import QAction, Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QTableView, \
    QFileDialog, QHeaderView, QMessageBox, QWidget, QStackedLayout

from .about import AboutDialog
from .festive_overlay import FestiveOverlay
from .filters import FilterView
from .recipe import RecipeDialog
from .sync import SyncDialog
from ..models.recipes import RecipesModel, RecipesProxyModel
from ..settings import Settings
from ...models.recipe import RecipeBook, Recipe


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.book = RecipeBook()
        self.edited = False
        self.path = None

        self.overlay = FestiveOverlay(self)

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

        if Settings.STARTUP_ANIMATION.get(True):
            QTimer.singleShot(100, self.overlay.trigger)

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

        file_menu = menu.addMenu("F&ile")

        action(file_menu, "Load", "fa5s.folder-open", shortcut="Ctrl+O", fn=self.load_new_file)
        action(file_menu, "Save", "fa5s.save", shortcut="Ctrl+S", fn=self.save)
        action(file_menu, "Save as", "fa5s.save", shortcut="Ctrl+Shift+S", fn=self.save_as)
        action(file_menu, "Print", "fa5s.print", shortcut="Ctrl+P")
        action(file_menu, "Quit", "fa5s.power-off", fn=self.close)

        # --
        recipe_menu = menu.addMenu("&Recipes")

        action(recipe_menu, "Add", "fa5s.plus", shortcut="Ctrl+N", fn=self.add_recipe)
        action(recipe_menu, "Del", "fa5s.minus", shortcut="Delete", fn=self.del_recipe)

        # --
        filters_menu = menu.addMenu("&Filters")

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
        misc_menu = menu.addMenu("&Misc")

        action(misc_menu, "Sync", "fa5s.sync", fn=lambda: SyncDialog().exec())
        action(misc_menu, "About", "fa5s.info-circle", fn=lambda: AboutDialog().exec())
        action(misc_menu, "Animation", "mdi.animation-play",
               fn=self.overlay.trigger, shortcut="Home")

    def _make_layout(self):
        holder = QWidget()
        holder.setLayout(layout := QStackedLayout())
        layout.addWidget(self.overlay)
        layout.addWidget(self.splitter)
        layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.filters)
        self.splitter.setCollapsible(0, False)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.setCentralWidget(holder)

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

    def save(self, path: Path | str = None, request_file=False):
        path = path or self.path
        if request_file or path is None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Enter savefile name", str(Settings.LAST_FILE.get()),
                "Cookbook (*.rbk)"
            )
            if not path:
                return

        self.book.write(stream=path)
        self.edited = False
        self._update_title()

    def save_as(self):
        self.save(None, request_file=True)

    def load(self, path: Path):
        self.book = RecipeBook.load(path)
        self.path = path
        self.edited = False

        self.proxy_model.setSourceModel(RecipesModel(self.book))
        self.table.setCurrentIndex(QModelIndex())

        self._update_title()

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

    def add_recipe(self):
        new_recipe = self.book.default_recipe()
        self.book.recipes[new_recipe.title] = new_recipe
        rd = RecipeDialog(self, self.book, new_recipe.title)
        rd.rejected.connect(lambda: self.book.recipes.pop(new_recipe.title))
        rd.edit_validated.connect(self._on_recipe_added)

        rd.edited = True
        rd.set_editable(True)

        rd.show()

    def del_recipe(self):
        indices = self.table.selectionModel().selectedRows()
        assert len(indices) == 1
        model: RecipesModel = self.proxy_model.sourceModel()
        source_index = self.proxy_model.mapToSource(indices[0])
        recipe = self.book.recipes.pop(source_index.siblingAtColumn(model.columnCount()-1).data())
        model.recipe_deleted(source_index.row())

        self.edited = True
        self._update_title()

    def on_recipe_clicked(self, index):
        item = self.proxy_model.recipe_title(index)
        rd = RecipeDialog(self, self.book, item)
        rd.edit_validated.connect(self._on_recipe_edited)
        rd.show()

    def _on_recipe_added(self, recipe: Recipe):
        model: RecipesModel = self.proxy_model.sourceModel()
        model.recipe_added(recipe)
        self.edited = True
        self._update_title()

    def _on_recipe_edited(self, recipe: Recipe):
        model: RecipesModel = self.proxy_model.sourceModel()
        model.recipe_changed(recipe)
        self.edited = True
        self._update_title()

    def on_filter_changed(self):
        self.proxy_model.invalidateFilter()
        self._update_title()

    def _update_title(self):
        title = f"Pyzza Cookbook - "
        if self.book:
            shown, total = self.proxy_model.rowCount(), len(self.book)
            title += f"{shown} recipes"
            if shown < total:
                title += f" (out of {total})"
        else:
            title += "No book loaded"
        if self.edited:
            title += "*"
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

    def closeEvent(self, event):
        yes, no, cancel = QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No, QMessageBox.StandardButton.Cancel
        if self.edited:
            answer = QMessageBox.question(
                self, "Unsaved", "Confirm changes before closing?",
                yes | no | cancel, yes
            )
            if answer == yes:
                self.save()
                close = True
            elif answer == no:
                close = True
            else:
                close = False
        else:
            close = True

        if close:
            self.save_settings()
            super().closeEvent(event)

        else:
            event.ignore()
