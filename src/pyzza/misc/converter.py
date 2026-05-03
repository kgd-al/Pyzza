import argparse
import json
from functools import lru_cache

from ..models.recipe import Recipe, IngredientEntry, SubrecipeEntry, DecorationEntry, write_recipes, load_recipes, \
    Regimen, DishType, Duration


@lru_cache
def regimen_mapping(regimen):
    return {
        1: Regimen.MEAT,
        2: Regimen.VEGGY,
        3: Regimen.VEGAN,
    }[regimen]


@lru_cache
def type_mapping(r_type):
    return {
        1: DishType.NEUTRAL,
        2: DishType.SALTY,
        3: DishType.SUGARY,
    }[r_type]


@lru_cache
def duration_mapping(duration):
    return {
        1: Duration.SHORT,
        2: Duration.MEDIUM,
        3: Duration.LONG,
        4: Duration.VERY_LONG,
    }[duration]


def convert_ingredients(ingredients, recipes_names, ingredients_data, units_data):
    ingredient_entries = []
    for entry in ingredients:
        match entry[0]:
            case 0:
                amount, unit_id, data_id, qualif = entry[1]
                ingredient_entries.append(IngredientEntry(
                    amount=amount,
                    unit=units_data[unit_id],
                    name=ingredients_data[data_id],
                    qualif=qualif,
                ))
            case 1:
                ingredient_entries.append(SubrecipeEntry(name=recipes_names[entry[1]]))
            case 2:
                ingredient_entries.append(DecorationEntry(text=entry[1]))
            case _: raise NotImplementedError(f"Unknown ingredient type {entry[0]}")
    return ingredient_entries


def main():
    parser = argparse.ArgumentParser(
        description='Converts old c++ cookbook storage into new python format')
    parser.add_argument('file')
    parser.add_argument('--dest', required=True,
                        help="Where to store the converted recipes book")
    args = parser.parse_args()

    json_db = json.loads(open(args.file).read())
    # del json_db["ingredients"]
    # del json_db["planning"]
    # del json_db["units"]
    # print(json_db["recipes"])
    recipes_names = {r["id"]: r["title"] for r in json_db["recipes"]}
    ingredients_data = {
        iid: istr for iid, istr, _, _ in json_db["ingredients"]
    }
    units_data = {uid: ustr for uid, ustr, _ in json_db["units"]}
    # print(yaml.dump(json_db, allow_unicode=True))

    recipes = {}
    for recipe in json_db["recipes"]:
        # print()
        # print(recipe)
        # print()
        title = recipe["title"]
        recipes[title] = Recipe(
            title=title,

            basic=recipe["basic"],
            duration=duration_mapping(recipe["duration"]),
            type=type_mapping(recipe["type"]),
            regimen=regimen_mapping(recipe["regimen"]),

            n_portions=recipe["d-portions"],
            t_portions=recipe["t-portions"],

            ingredients=convert_ingredients(recipe["ing"],
                                            recipes_names, ingredients_data, units_data),
            steps=recipe["steps"],
            notes=recipe["notes"],

        )

    # print(recipe.keys())

    with open(args.dest, "w") as f:
        write_recipes(recipes, stream=f)

    with open(args.dest, "r") as f:
        recipes_roundtrip = load_recipes(f)

    for r_lhs, r_rhs in zip(recipes, recipes_roundtrip):
        assert r_lhs == r_rhs, f"\n{r_lhs=}\n\n{r_rhs=}"
    assert recipes_roundtrip == recipes
    print(write_recipes(recipes))
    print()
    print(f"Generated {args.dest} from {args.file} ({len(recipes)} recipes)")


if __name__ == '__main__':
    main()
