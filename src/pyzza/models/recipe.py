import dataclasses
from dataclasses import Field
from enum import StrEnum, auto
from typing import List, ClassVar, Dict, Iterable, Set, TYPE_CHECKING

import yaml


def named_fields():
    """
     This generates a named accessor for every field in the dataclass.
     Note: this is not enough for the IDE to pick up on it so you need to also
     generate stubs (see generate_stubs in pyzza.pyside_app)
     """
    def decorator(klass):
        for f in dataclasses.fields(klass):
            setattr(klass, f.name.upper(), f)
        return klass
    return decorator


def get_field(dc, name):
    for field in dataclasses.fields(dc):
        if field.name == name:
            return field
    raise LookupError(f"Field {name} not found in {dc.__class__.__name__}")


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

    def pretty_text(self, scaling=1):
        return self.name


@dataclasses.dataclass(kw_only=True)
class DecorationEntry(yaml.YAMLObject):
    yaml_tag = "!Decoration"

    text: str

    def pretty_text(self, scaling=1):
        return self.text


IngredientsListEntry = IngredientEntry | SubrecipeEntry | DecorationEntry
IngredientsList = List[IngredientsListEntry]


@named_fields()
@dataclasses.dataclass
class Recipe(yaml.YAMLObject):
    yaml_tag = "!Recipe"

    title: str

    basic: bool
    # BASIC: dataclasses.Field

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

    is_sub_recipe: bool = False

    if TYPE_CHECKING:  # Just to make IDEs happy, actually filled by the decorator
        TITLE: Field = None
        BASIC: Field = None
        TYPE: Field = None
        REGIMEN: Field = None
        DURATION: Field = None
        N_PORTIONS: Field = None
        T_PORTIONS: Field = None

RecipesDict = Dict[str, Recipe]


@dataclasses.dataclass
class RecipeBook:
    recipes: RecipesDict = dataclasses.field(default_factory=dict)
    ingredients: Set[str] = dataclasses.field(default_factory=set)
    units: Set[str] = dataclasses.field(default_factory=set)

    def __post_init__(self):
        for r in self.recipes.values():
            r.type = DishType(r.type)
            r.regimen = Regimen(r.regimen)
            r.duration = Duration(r.duration)

            for i in r.ingredients:
                if isinstance(i, IngredientEntry):
                    self.ingredients.add(i.name)
                    self.units.add(i.unit)

                elif isinstance(i, SubrecipeEntry):
                    self.recipes[i.name].is_sub_recipe = True

            # print(r)

    def __len__(self): return len(self.recipes)
    def __bool__(self): return len(self) > 0

    @classmethod
    def default_recipe(cls) -> 'Recipe':
        return Recipe(
            title="Poudre de pinrlinpinpin",
            basic=False,
            type=DishType.SALTY,
            regimen=Regimen.MEAT,
            duration=Duration.SHORT,
            n_portions=0,
            t_portions="",
            ingredients=[],
            steps=[],
            notes=""
        )

    def write(self, **kwargs):
        _kwargs = dict(stream=None, allow_unicode=True, sort_keys=False) | kwargs
        def do_write(): return yaml.safe_dump(list(self.recipes.values()), **_kwargs)
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

    @classmethod
    def load(cls, stream=None) -> 'RecipeBook':
        recipes = cls(), None
        def do_load(__f): return yaml.safe_load(__f)
        if hasattr(stream, "read") or isinstance(stream, bytes):
            recipes = do_load(stream)
        else:
            with open(stream, "r") as f:
                recipes = do_load(f)

        if recipes is None:
            raise RuntimeError(f"Failed to read recipes from stream '{stream}'")

        return cls(recipes={r.title: r for r in recipes})


for __class in [IngredientEntry, SubrecipeEntry, DecorationEntry, Recipe]:
    yaml.SafeLoader.add_constructor(getattr(__class, "yaml_tag"), getattr(__class, "from_yaml"))
    yaml.SafeDumper.add_multi_representer(__class, getattr(__class, "to_yaml"))
yaml.SafeDumper.add_multi_representer(
  StrEnum,
  yaml.representer.SafeRepresenter.represent_str,
)


