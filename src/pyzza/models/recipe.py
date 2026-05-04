import dataclasses
from enum import StrEnum, auto
from typing import List, ClassVar, Dict, Iterable

import yaml


def get_field(dc, name):
    for field in dataclasses.fields(dc):
        if field.name == name:
            return field
    raise LookupError(f"Field {name} not found in {dc.__class__.__name__}")


def named_fields(fields: List[str]):
    def decorator(klass):
        all_fields = {f.name: f for f in dataclasses.fields(klass)}
        for f in fields:
            setattr(klass, f.upper(), all_fields[f])
        return klass
    return decorator


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

    def pretty_text(self, scaling=1):
        tokens = [f"{scaling * self.amount:g}", self.name, self.qualif]
        if self.unit != IngredientEntry.NO_UNIT:
            tokens.insert(1, self.unit)
        return " ".join(tokens)


@dataclasses.dataclass(kw_only=True)
class SubrecipeEntry(yaml.YAMLObject):
    yaml_tag = "!Sub_recipe"

    name: str


@dataclasses.dataclass(kw_only=True)
class DecorationEntry(yaml.YAMLObject):
    yaml_tag = "!Decoration"

    text: str


IngredientsListEntry = IngredientEntry | SubrecipeEntry | DecorationEntry
IngredientsList = List[IngredientsListEntry]


@named_fields(["title", "basic", "type", "regimen", "duration"])
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

    ingredients: IngredientsList
    steps: List[str]
    notes: str


for __class in [IngredientEntry, SubrecipeEntry, DecorationEntry, Recipe]:
    yaml.SafeLoader.add_constructor(getattr(__class, "yaml_tag"), getattr(__class, "from_yaml"))
    yaml.SafeDumper.add_multi_representer(__class, getattr(__class, "to_yaml"))
yaml.SafeDumper.add_multi_representer(
  StrEnum,
  yaml.representer.SafeRepresenter.represent_str,
)


RecipesDict = Dict[str, Recipe]


def write_recipes(recipes: RecipesDict, **kwargs):
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


def load_recipes(stream=None) -> RecipesDict:
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
