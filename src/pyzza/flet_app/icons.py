import os
from enum import StrEnum, auto

import flet as ft
from anyio.functools import lru_cache

ASSETS_PREFIX = ""


class Icons(StrEnum):
    @staticmethod
    def init(page):
        global ASSETS_PREFIX
        platform = os.environ.get("FLET_PLATFORM") or page.platform
        if platform not in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
            ASSETS_PREFIX = "assets/"

    @staticmethod
    @lru_cache()
    def get_image(e: StrEnum, prefix=None, **kwargs) -> ft.Image:
        if prefix is None:
            prefix = f"{e.__class__.__name__.lower()}_"
        path = f"{ASSETS_PREFIX}icons/{prefix}{e.value}.png"
        return ft.Image(
            src=path,
            width=Icons.default_size(),
            height=Icons.default_size(),
            tooltip=e.value.casefold().replace("_", " "),
            **kwargs
        )

    def image(self, **kwargs) -> ft.Image:
        return self.get_image(self, prefix="", **kwargs)

    @staticmethod
    def default_size(): return 18

    BASIC_RECIPE = auto()
