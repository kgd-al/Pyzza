from enum import StrEnum
from functools import lru_cache

from PySide6.QtCore import QSettings


class Settings(StrEnum):
    LAST_FILE = "last-cookbook"

    WINDOW_GEOMETRY = "window-geom"
    WINDOW_STATE = "window-state"

    RECIPES_SORTING = "recipes-sorting"
    RECIPES_FILTERING = "recipes-filtering"

    @staticmethod
    @lru_cache
    def _qsettings(): return QSettings()

    def get(self): return self._qsettings().value(self.value)
    def set(self, value): self._qsettings().setValue(self.value, value)
