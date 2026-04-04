_BASE = 4535.92  # andouille ratio base (10 lbs)
_SI_BASE = 2722   # spicy italian ratio base (6 lbs)

RECIPE_ORDER = ["kielbasa", "andouille", "spicy_italian", "classic_bacon", "salmon"]

RECIPES = {
    "kielbasa": {
        "id": "kielbasa",
        "name": "Kielbasa",
        "description": "Polish garlic sausage",
        "default_base_g": 1000.0,
        "ingredients": [
            {"id": "pork",        "label": "Pork",          "ratio": 1.0},
            {"id": "salt",        "label": "Salt",           "ratio": 15/1000},
            {"id": "black_pepper","label": "Black Pepper",   "ratio": 2.5/1000},
            {"id": "garlic",      "label": "Garlic",         "ratio": 5.5/1000},
            {"id": "marjoram",    "label": "Marjoram",       "ratio": 1/1000},
            {"id": "sugar",       "label": "Sugar",          "ratio": 2.5/1000},
            {"id": "eco_cure",    "label": "Eco Cure #1",    "ratio": 10/1000},
            {"id": "milk_powder", "label": "Milk Powder",    "ratio": 10/1000},
            {"id": "liquid",      "label": "Liquid",         "ratio": 100/1000},
        ],
    },
    "andouille": {
        "id": "andouille",
        "name": "Andouille",
        "description": "Spicy Cajun smoked sausage",
        "default_base_g": _BASE,
        "ingredients": [
            {"id": "pork",          "label": "Pork",           "ratio": 1.0},
            {"id": "salt",          "label": "Salt",           "ratio": 90/_BASE},
            {"id": "fresh_garlic",  "label": "Fresh Garlic",   "ratio": 50/_BASE},
            {"id": "cayenne",       "label": "Cayenne",        "ratio": 30/_BASE},
            {"id": "black_pepper",  "label": "Black Pepper",   "ratio": 30/_BASE},
            {"id": "fresh_thyme",   "label": "Fresh Thyme",    "ratio": 10/_BASE},
            {"id": "powdered_milk", "label": "Powdered Milk",  "ratio": 120/_BASE},
            {"id": "dry_white_wine","label": "Dry White Wine", "ratio": 400/_BASE},
            # eco_cure = 1% of (pork + all spices): (730 + 4535.92) * 0.01 / 4535.92
            {"id": "eco_cure",      "label": "Eco Cure #1",    "ratio": (730 + _BASE) * 0.01 / _BASE},
        ],
    },
    "spicy_italian": {
        "id": "spicy_italian",
        "name": "Spicy Italian",
        "description": "Fennel and red pepper Italian sausage",
        "default_base_g": _SI_BASE,
        "ingredients": [
            {"id": "pork",              "label": "Pork",              "ratio": 1.0},
            {"id": "milk_powder",       "label": "Milk Powder",       "ratio": 50/_SI_BASE},
            {"id": "salt",              "label": "Salt",              "ratio": 45/_SI_BASE},
            {"id": "white_sugar",       "label": "White Sugar",       "ratio": 35/_SI_BASE},
            {"id": "liquid",            "label": "Liquid",            "ratio": 250/_SI_BASE},
            {"id": "fennel",            "label": "Fennel",            "ratio": 20/_SI_BASE},
            {"id": "paprika",           "label": "Paprika",           "ratio": 20/_SI_BASE},
            {"id": "italian_herb_mix",  "label": "Italian Herb Mix",  "ratio": 20/_SI_BASE},
            {"id": "granulated_garlic", "label": "Granulated Garlic", "ratio": 20/_SI_BASE},
            {"id": "red_pepper_flakes", "label": "Red Pepper Flakes", "ratio": 16/_SI_BASE},
            {"id": "black_pepper",      "label": "Black Pepper",      "ratio": 10/_SI_BASE},
            {"id": "coriander",         "label": "Coriander",         "ratio": 10/_SI_BASE},
            {"id": "turmeric",          "label": "Turmeric",          "ratio": 5/_SI_BASE},
            {"id": "parsley",           "label": "Parsley",           "ratio": 5/_SI_BASE},
            # eco_cure = 1% of (pork + all spices): (506 + 2722) * 0.01 / 2722
            {"id": "eco_cure",          "label": "Eco Cure #1",       "ratio": (506 + _SI_BASE) * 0.01 / _SI_BASE},
        ],
    },
    "classic_bacon": {
        "id": "classic_bacon",
        "name": "Classic Bacon",
        "description": "Simple dry-cured bacon",
        "default_base_g": 2268.0,  # 5 lbs
        "ingredients": [
            {"id": "pork_belly",        "label": "Pork Belly",        "ratio": 1.0},
            {"id": "salt",              "label": "Salt",              "ratio": 0.0225},
            {"id": "sugar",             "label": "Sugar",             "ratio": 0.0125},
            {"id": "garlic_powder",     "label": "Garlic Powder",     "ratio": 0.005},
            {"id": "pepper",            "label": "Pepper",            "ratio": 0.005},
            {"id": "sage",              "label": "Sage",              "ratio": 0.0025},
            {"id": "red_pepper_flakes", "label": "Red Pepper Flakes", "ratio": 0.0025},
            # eco_cure = 1% of (belly + all spices): (1 + 0.05) * 0.01
            {"id": "eco_cure",          "label": "Eco Cure #1",       "ratio": 1.05 * 0.01},
        ],
    },
    "salmon": {
        "id": "salmon",
        "name": "Cured Salmon",
        "description": "Cold-smoked salmon dry cure",
        "default_base_g": 1000.0,
        "ingredients": [
            {"id": "salmon",           "label": "Salmon",           "ratio": 1.0},
            # Total cure = 3% of salmon weight, distributed by base ratios (sum=1380)
            {"id": "salt",             "label": "Salt",             "ratio": 0.03 * 900/1380},
            {"id": "sugar",            "label": "Sugar",            "ratio": 0.03 * 400/1380},
            {"id": "garlic",           "label": "Garlic",           "ratio": 0.03 * 30/1380},
            {"id": "pepper",           "label": "Pepper",           "ratio": 0.03 * 30/1380},
            {"id": "sage",             "label": "Sage",             "ratio": 0.03 * 10/1380},
            {"id": "red_pepper_flake", "label": "Red Pepper Flake", "ratio": 0.03 * 10/1380},
        ],
    },
}
