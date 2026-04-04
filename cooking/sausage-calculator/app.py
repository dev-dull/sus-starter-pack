from flask import Flask, render_template, request
from recipes import RECIPES, RECIPE_ORDER

app = Flask(__name__)


def compute_weights(recipe, base_g):
    return {ing["id"]: round(base_g * ing["ratio"], 2) for ing in recipe["ingredients"]}


@app.get("/")
def index():
    recipe_id = request.args.get("recipe", "kielbasa")
    if recipe_id not in RECIPES:
        recipe_id = "kielbasa"
    recipe = RECIPES[recipe_id]
    weights = compute_weights(recipe, recipe["default_base_g"])
    return render_template(
        "index.html",
        all_recipes=RECIPES,
        recipe_order=RECIPE_ORDER,
        recipe_id=recipe_id,
        recipe=recipe,
        weights=weights,
    )


@app.post("/calculate/<recipe_id>/<ingredient_id>")
def calculate(recipe_id, ingredient_id):
    if recipe_id not in RECIPES:
        return "", 400
    recipe = RECIPES[recipe_id]

    try:
        new_value = float(request.form.get("value", 0))
        if new_value <= 0:
            raise ValueError
    except (TypeError, ValueError):
        weights = compute_weights(recipe, recipe["default_base_g"])
        return render_template("_table.html", recipe=recipe, recipe_id=recipe_id, weights=weights)

    ing = next((i for i in recipe["ingredients"] if i["id"] == ingredient_id), None)
    if ing is None or ing["ratio"] == 0:
        return "", 400

    base_g = new_value / ing["ratio"]
    weights = compute_weights(recipe, base_g)
    return render_template("_table.html", recipe=recipe, recipe_id=recipe_id, weights=weights)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
