from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from recipes import RECIPES, RECIPE_ORDER

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def compute_weights(recipe, base_g):
    return {ing["id"]: round(base_g * ing["ratio"], 2) for ing in recipe["ingredients"]}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, recipe: str = "kielbasa"):
    if recipe not in RECIPES:
        recipe = "kielbasa"
    r = RECIPES[recipe]
    weights = compute_weights(r, r["default_base_g"])
    return templates.TemplateResponse(request, "index.html", {
        "all_recipes": RECIPES,
        "recipe_order": RECIPE_ORDER,
        "recipe_id": recipe,
        "recipe": r,
        "weights": weights,
    })


@app.post("/calculate/{recipe_id}/{ingredient_id}", response_class=HTMLResponse)
async def calculate(
    request: Request,
    recipe_id: str,
    ingredient_id: str,
    value: float = Form(...),
):
    if recipe_id not in RECIPES:
        return HTMLResponse("", status_code=400)
    r = RECIPES[recipe_id]

    ing = next((i for i in r["ingredients"] if i["id"] == ingredient_id), None)
    if ing is None or ing["ratio"] == 0 or value <= 0:
        weights = compute_weights(r, r["default_base_g"])
    else:
        weights = compute_weights(r, value / ing["ratio"])

    return templates.TemplateResponse(request, "_table.html", {
        "recipe": r,
        "recipe_id": recipe_id,
        "weights": weights,
    })
