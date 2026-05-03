import asyncio
import sys
import warnings

print("APP STARTING")
print("YOOOHOOO")
print("08:26")

import functools
import os
import urllib
from pathlib import Path

import flet as ft
import flet_datatable2 as ftd

from icons import Icons
from networking.sync_server import fetch
from models.recipe import load_recipes, Recipe, IngredientEntry, SubrecipeEntry, DecorationEntry, write_recipes
from misc.debug import kgd_debug


# os.system('clear')
# print("[kgd-debug] Force-clearing console")

CACHE = Path(os.getenv("FLET_APP_STORAGE_DATA")).joinpath("cookbook.rbk").resolve()


class MainWindow:
    def __init__(self, page: ft.Page):
        self.sync_button = ft.IconButton(
            ft.Icons.DOWNLOAD, tooltip="Fetch cookbook from streaming desktop app",
            on_click=self.sync_file,
        )

        self.filter = ft.TextField(
            label="Filter", hint_text="Search by recipe name",
            on_change=self.filter_changed
        )

        self.icon_size = Icons.default_size()
        self.icol_icons = 4
        self.icol_spacing = 4
        self.icol_width = self.icol_icons * self.icon_size + (self.icol_icons - 1) * self.icol_spacing

        self.sync_hint = ft.Text("Please sync using the above button")
        self.sync_hint.visible = False

        self.table = ftd.DataTable2(
            expand=True,
            show_bottom_border=True,
            columns=[
                ftd.DataColumn2(label=ft.Text(""), fixed_width=self.icol_width),
                ftd.DataColumn2(label=ft.Text("Name")),
            ]
        )

        controls = ft.Row(
            controls=[self.sync_button, self.filter],
            margin=ft.Margin(top=10),
        )

        self.debug_dialog = ft.AlertDialog(
            title=ft.Text("debug"),
            content=ft.Container(
                ft.TextField(read_only=True, multiline=True),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
                border_radius=4,
            )
        )

        self.view = ft.Column(
            expand=True,
            controls=[
                controls,
                self.sync_hint,
                self.table,
            ],
        )
        self.page = page

        self.recipes = {}
        self.update_data()

    def debug_message(self, msg):
        print(msg)
        debug_log = self.debug_dialog.content.content
        if len(debug_log.value) > 0:
            debug_log.value += "\n"
        debug_log.value += msg
        if not self.debug_dialog.open:
            self.page.show_dialog(self.debug_dialog)
        self.debug_dialog.content.update()

    async def sync_success(self):
        self.debug_message(f"Book is updated")
        self.debug_message(f"Please close me")
        content = self.debug_dialog.content

        for _ in range(3):
            content.bgcolor = ft.Colors.GREEN
            content.update()
            await asyncio.sleep(0.3)
            content.bgcolor = None
            content.update()
            await asyncio.sleep(0.3)

        content.bgcolor = ft.Colors.with_opacity(.1, ft.Colors.GREEN)
        content.update()

    async def sync_file(self):
        self.debug_message("Requesting file from network")
        self.sync_button.disabled = True
        data = await fetch(print_callback=self.debug_message)
        self.sync_button.disabled = False

        recipes = load_recipes(data)
        self.debug_message(f"> {len(recipes)} recipes")
        if recipes:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            write_recipes(recipes, stream=str(CACHE))
            self.debug_message(f"Wrote recipes to {CACHE}")
            self.update_data()
            await self.sync_success()

    def update_data(self):
        def set_title(msg): self.page.title = f"Pyzza CookBook - {msg}"

        if not CACHE.exists():
            set_title("No recipes")
            self.sync_hint.visible = True
            self.table.visible = False
            return

        self.sync_hint.visible = False
        self.table.visible = True

        new_recipes = load_recipes(CACHE)
        self.recipes = new_recipes

        self.page.title = f"Pyzza CookBook - {len(self.recipes)} recipes"

        callbacks = dict(
            on_tap=self.show_recipe,
            on_long_press=self.show_recipe,
            on_double_tap=self.show_recipe)
        self.table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Row(
                            controls=[
                                Icons.BASIC_RECIPE.image() if r.basic else ft.Container(width=self.icon_size),
                                Icons.get_image(r.regimen),
                                Icons.get_image(r.type),
                                Icons.get_image(r.duration),
                            ],
                            spacing=self.icol_spacing,
                            alignment=ft.MainAxisAlignment.END,
                            tight=False, width=self.icol_width,
                        ),
                        **callbacks,
                    ),
                    ft.DataCell(ft.Text(r.title), **callbacks),
                ],

            ) for r in self.recipes.values()
        ]
        self.page.update()

    def filter_changed(self, e: ft.Event[ft.TextField]):
        if not isinstance(e.data, str):
            kgd_debug(f"Got something other than text in the filter: {e}")
            return
        for r in self.table.rows:
            if isinstance(content := r.cells[-1].content, ft.Text):
                r.visible = (e.data.lower() in content.value.lower())

    async def show_recipe(self, e: ft.Event[ft.DataRow]):
        if not isinstance(row := e.control.parent, ft.DataRow):
            kgd_debug(f"Got something other than row in double click event: {row}")
            return
        if not isinstance(text := row.cells[-1].content, ft.Text):
            kgd_debug(f"Could not get recipe name in double click event: {text}")
            return
        print(f"Showing recipe: /details/{text.value}")
        await self.page.push_route(urllib.parse.quote(f"/details/{text.value}"))


def details_view(page: ft.Page, r: Recipe) -> ft.Control:
    def labeled(title, content):
        return ft.Container(
            ft.Column([
                ft.Text(title, size=18),
                content,
            ], spacing=4),
            expand=True,
            padding=8,
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.GREY_600),
        )

    selected_item = None

    def list_item(text):
        return ft.Container(
            ft.Row(
                controls=[ft.Icon(ft.Icons.ARROW_RIGHT), ft.Text(text, expand=True)],
                spacing=2,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ink=True,
            on_click=select_item,
        )

    def select_item(e):
        control = e.control
        nonlocal selected_item
        if selected_item is not None:
            selected_item.bgcolor = None
        if control != selected_item:
            selected_item = control
            control.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.PRIMARY)

    def format_ingredient(i):
        if isinstance(i, IngredientEntry):
            tokens = [str(i.amount), i.name, i.qualif]
            if i.unit != IngredientEntry.NO_UNIT:
                tokens.insert(1, i.unit)
            return list_item(" ".join(tokens))
        elif isinstance(i, DecorationEntry):
            return ft.Text(f"{i.text}", margin=ft.Margin(top=5))
        elif isinstance(i, SubrecipeEntry):
            return ft.Row(
                controls=[ft.TextButton(f"{i.name}", icon=ft.Icons.LINK, on_click=show_recipe)],
                alignment=ft.MainAxisAlignment.START)
        else:
            return ft.Text(f"Unknown ingredient entry type: {i}")

    async def show_recipe(e: ft.Event[ft.TextButton]):
        print(f"Showing recipe: /details/{e.control.content}")
        await page.push_route(urllib.parse.quote(f"/details/{e.control.content}"))

    def portions_changed():
        portions_field.width = max(40, min(len(portions_field.value) * 10 + 30, 80))
        ratio = float(portions_field.value) / r.n_portions
        for i_control, i_data in zip(ingredients, r.ingredients):
            if isinstance(i_data, IngredientEntry):
                p_text = i_control.content.controls[-1]
                p_tokens = p_text.value.split(" ")
                p_tokens[0] = f"{ratio * i_data.amount:g}"
                p_text.value = " ".join(p_tokens)

    ingredients = [format_ingredient(i) for i in r.ingredients]

    portions_field = ft.TextField(
        value=str(r.n_portions),
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=portions_changed,
    )

    portions_changed()

    def change_portion(e, sign: int):
        v = float(portions_field.value) + sign
        v = 0 if v < 0 else v
        portions_field.value = f"{v:g}"
        portions_changed()

    portions = ft.Row([
        ft.IconButton(ft.Icons.ADD, on_click=functools.partial(change_portion, sign=+1)),
        ft.IconButton(ft.Icons.REMOVE, on_click=functools.partial(change_portion, sign=-1)),
        portions_field,
        ft.Text(r.t_portions),
    ], spacing=0)

    basic_icon = [Icons.BASIC_RECIPE.image()] if r.basic else []

    return ft.Column(
        expand=True,
        controls=[
            # ft.Row(
            #     controls=[ft.Text(r.title, size=24, weight=ft.FontWeight.W_600)],
            #     alignment=ft.MainAxisAlignment.CENTER,
            # ),
            ft.Row(
                # expand=True,
                controls=[portions, ft.Container(expand=True)] + basic_icon + [
                             Icons.get_image(value)
                             for value in [r.type, r.regimen, r.duration]
                         ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                expand=True,
                controls=[
                    labeled("Ingredients", ft.ListView(
                        controls=ingredients,
                        expand=True,
                    )),
                    labeled("Steps", ft.ListView(
                        controls=[list_item(t) for t in r.steps],
                        expand=True,
                    ))
                ],
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            ft.Row(
                expand=False,
                controls=[
                    labeled("Notes", ft.ListView(
                        controls=[ft.Text(r.notes)],
                        expand=True,
                    )),
                ]
            ),
        ]
    )


def main(page: ft.Page):
    try:
        Icons.init(page)
        page.theme = ft.Theme(color_scheme_seed=ft.Colors.GREEN)

        print("Initial route:", page.route)
        main_window = MainWindow(page)

        def route_change():
            if not page.views:
                # Ensure at least top-level view
                page.views.append(
                    ft.View(
                        route="/",
                        controls=[main_window.view]
                    )
                )

            if page.route.startswith("/details/"):
                recipe = urllib.parse.unquote(page.route).split("/")[-1]
                print("route_change():", recipe)
                # only append if not already on stack
                if not any(v.route == f"/details/{recipe}" for v in page.views):
                    page.views.append(
                        ft.View(
                            route=f"/details/{recipe}",
                            controls=[
                                ft.AppBar(
                                    title=ft.Text(recipe),
                                    automatically_imply_leading=True,  # back arrow
                                ),
                                details_view(page, main_window.recipes[recipe]),
                            ]
                        )
                    )

            page.update()

        async def view_pop(e):
            if e.view is not None:
                page.views.remove(e.view)
                top_view = page.views[-1]
                await page.push_route(top_view.route)

        page.views.clear()
        page.on_route_change = route_change
        page.on_view_pop = view_pop
        route_change()

    except Exception as e:
        import traceback
        page.add(ft.Text(str(e), color=ft.Colors.RED))
        page.add(ft.Text(traceback.format_exc(), size=10))
        page.update()


ft.run(main, assets_dir="assets/")
