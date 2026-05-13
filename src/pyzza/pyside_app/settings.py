import ast
from enum import StrEnum
from functools import lru_cache

from PySide6.QtCore import QSettings


class Settings(StrEnum):
    LAST_FILE = "last-cookbook"

    WINDOW_GEOMETRY = "window-geom"
    WINDOW_STATE = "window-state"

    RECIPES_SORTING = "recipes-sorting"
    RECIPES_FILTERING = "recipes-filtering"

    RECIPE_DIALOG_GEOMETRY = "recipe-dialog-geometry"

    STARTUP_ANIMATION = "startup-animation"

    @staticmethod
    @lru_cache
    def _qsettings(): return QSettings()

    def set(self, value): self._qsettings().setValue(self.value, value)
    def get(self, default=None):
        value: str = self._qsettings().value(self.value, default)
        # print(f"Settings value: {self.name}: {value} ({type(value)}")
        if default is None:
            return value

        if isinstance(default, bool) and not isinstance(value, bool):
            return ast.literal_eval(value.capitalize())

        return value