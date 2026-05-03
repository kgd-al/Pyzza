import dataclasses
from enum import StrEnum, auto
from typing import List, ClassVar, Dict, Iterable

import yaml


class Regimen(StrEnum):
    MEAT = auto()
    VEGGY = auto()
    VEGAN = auto()


class DishType(StrEnum):
    NEUTRAL = auto()
    SALTY = auto()
    SUGARY = auto()


class Duration(StrEnum):
    SHORT = auto()
    MEDIUM = auto()
    LONG = auto()
    VERY_LONG = auto()


class EntryType(StrEnum):
    INGREDIENT = auto()
    SUB_RECIPE = auto()
    DECORATION = auto()


@dataclasses.dataclass(kw_only=True)
class IngredientEntry(yaml.YAMLObject):
    yaml_tag = "!Ingredient"

    amount: float
    unit: str
    name: str
    qualif: str

    NO_UNIT: ClassVar[str] = "Ø"


@dataclasses.dataclass(kw_only=True)
class SubrecipeEntry(yaml.YAMLObject):
    yaml_tag = "!Sub_recipe"

    name: str


@dataclasses.dataclass(kw_only=True)
class DecorationEntry(yaml.YAMLObject):
    yaml_tag = "!Decoration"

    text: str


@dataclasses.dataclass
class Recipe(yaml.YAMLObject):
    yaml_tag = "!Recipe"

    title: str

    basic: bool
    type: DishType
    regimen: Regimen
    # status: ???Enum
    duration: Duration

    n_portions: float
    t_portions: str

    #id

    ingredients: List[IngredientEntry | SubrecipeEntry | DecorationEntry]
    steps: List[str]
    notes: str


for __class in [IngredientEntry, SubrecipeEntry, DecorationEntry, Recipe]:
    yaml.SafeLoader.add_constructor(getattr(__class, "yaml_tag"), getattr(__class, "from_yaml"))
    yaml.SafeDumper.add_multi_representer(__class, getattr(__class, "to_yaml"))
yaml.SafeDumper.add_multi_representer(
  StrEnum,
  yaml.representer.SafeRepresenter.represent_str,
)


def write_recipes(recipes: Dict[str, Recipe], **kwargs):
    _kwargs = dict(stream=None, allow_unicode=True, sort_keys=False) | kwargs
    def do_write(): return yaml.safe_dump(list(recipes.values()), **_kwargs)
    stream = _kwargs["stream"]
    if stream is None:
        return do_write()
    else:
        if not hasattr(stream, "read"):
            with open(stream, "w") as f:
                _kwargs["stream"] = f
                return do_write()
        else:
            return do_write()


def load_recipes(stream=None) -> Dict[str, Recipe]:
    def do_load(__f): return yaml.safe_load(__f)
    if hasattr(stream, "read") or isinstance(stream, bytes):
        recipes = do_load(stream)
    else:
        with open(stream, "r") as f:
            recipes = do_load(f)

    for r in recipes:
        r.type = DishType(r.type)
        r.regimen = Regimen(r.regimen)
        r.duration = Duration(r.duration)

        # print(r)

    return {r.title: r for r in recipes}
