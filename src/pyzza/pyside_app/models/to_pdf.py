import re
from enum import StrEnum
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import List

from PySide6.QtCore import QBuffer, QIODevice
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, StyleSheet1, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Spacer, Image, Table, TableStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents

from ..gui.icons import Icons
from ...models.recipe import IngredientEntry, DecorationEntry, SubrecipeEntry
from ...models.recipe import RecipeBook, Recipe

TOC_TITLE = "Table of Contents"


def print_to_pdf(book: RecipeBook, path: Path):
    doc = RecipeBook(str(path), title=path.stem.capitalize())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "RecipeLink",
        parent=styles["Normal"],
        textColor=colors.blue,
        underline=True,
    ), "link")

    items = []

    toc = TableOfContents()
    toc.levelStyles = [styles["link"]]
    items.extend([Paragraph(TOC_TITLE, styles["Title"]), toc, PageBreak()])

    for recipe in sorted(book.recipes.values()):
        items.extend(_recipe(recipe, styles))
    doc.multiBuild(items, onFirstPage=_page_callback, onLaterPages=_page_callback)


class RecipeBook(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        """Registers TOC entries when a titled paragraph is encountered."""
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == "Title" and flowable.text != TOC_TITLE:
                text = flowable.getPlainText()
                key = _link_name(text)
                self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (0, text, self.page, key))


def _page_callback(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(A4[0] / 2, 1.5*cm, str(doc.page))
    canvas.restoreState()


def _link_name(title: str) -> str:
    ascii_str = Recipe.to_ascii(title)
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_str.lower()).strip("_")
    return "recipe_" + slug


@lru_cache
def _image(icon, width, height, **kwargs):
    pixmap = icon.pixmap(64, 64)
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    pixmap.save(buffer, "PNG")
    data = bytes(buffer.data())
    buffer.close()
    return Image(BytesIO(data), width=width, height=height, **kwargs)


def _recipe(recipe: Recipe, styles: StyleSheet1) -> List[Flowable]:
    def _spacer(): items.append(Spacer(width=0, height=25))

    def _header(text):
        _spacer()
        items.append(Paragraph(text, styles['Heading1']))

    def _link(name):
        items.append(Paragraph(
            f'➤ <link href="#{_link_name(name)}">{name}</link>', styles['link']))

    items: List[Flowable] = [
        Paragraph(f'{recipe.title}', styles['Title']),
        HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceAfter=12),
    ]

    icons = [Icons.BASIC_RECIPE.image()] if recipe.basic else []
    icons += [Icons.get_image(e) for e in [recipe.type, recipe.regimen, recipe.duration]]
    t = Table([[_image(i, 1*cm, 1*cm) for i in icons]],
              colWidths=[1*cm] * len(icons), hAlign="CENTER")
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), .25 * cm),
        ("RIGHTPADDING", (0, 0), (-1, -1), .25 * cm),
    ]))
    items.append(t)

    _header("Ingredients")
    items.append(Paragraph(f"Pour {recipe.n_portions} {recipe.t_portions}"))

    for i in recipe.ingredients:
        if isinstance(i, IngredientEntry):
            items.append(Paragraph(i.pretty_text(), styles['Normal']))
        elif isinstance(i, DecorationEntry):
            items.append(Paragraph(i.text, styles['Heading2']))
        elif isinstance(i, SubrecipeEntry):
            _link(i.name)

    _header("Steps")
    for s in recipe.steps:
        items.append(Paragraph(s, styles['Normal']))

    if recipe.notes:
        _spacer()

        _header("Notes")
        items.append(Paragraph(recipe.notes.replace("\n", "<br/>"), styles['Normal']))

    if recipe.is_sub_recipe:
        _spacer()
        _header("Used in")

        for r in recipe.used_in:
            _link(r)

    items.append(PageBreak())

    return items
