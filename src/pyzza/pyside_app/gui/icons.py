from enum import StrEnum, auto

from PySide6.QtGui import QIcon
from anyio.functools import lru_cache


class Icons(StrEnum):
    @staticmethod
    @lru_cache()
    def get_image(e: StrEnum, prefix=None) -> QIcon:
        if prefix is None:
            prefix = f"{e.__class__.__name__.lower()}_"
        path = f":/assets/icons/{prefix}{e.value}.png"
        return QIcon(path)

    def image(self) -> QIcon:
        return self.get_image(self, prefix="")

    BASIC_RECIPE = auto()
