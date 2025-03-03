import requests
import yaml

# Φόρτωση του API Key από το endpoints.yml
with open("endpoints.yml", "r") as file:
    endpoints = yaml.safe_load(file)
    api_key = endpoints.get("spoonacular", {}).get("api_key")

if not api_key:
    print(" API Key not found! Please check your endpoints.yml file.")
    exit()

def get_recipes_by_ingredients(ingredients, number=5):
    """
    Λαμβάνει συνταγές βασισμένες στα παρεχόμενα υλικά μέσω του Spoonacular API.
    
    Args:
    - ingredients (list): Λίστα με υλικά.
    - number (int): Αριθμός προτεινόμενων συνταγών.

    Returns:
    - List of recipes or error message.
    """

    ingredients_query = ",".join(ingredients)

    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ingredients_query,
        "number": number,
        "apiKey": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        recipes = response.json()
        if recipes:
            return recipes
        else:
            return " No recipes found for the given ingredients."
    else:
        return f" API Error: {response.status_code} - {response.json().get('message', 'Unknown error')}"

def get_nutrition_info(recipe_id):
    """
    Λαμβάνει διατροφικές πληροφορίες για μια συνταγή μέσω του Spoonacular API.

    Args:
    - recipe_id (int): Το ID της συνταγής.

    Returns:
    - Dictionary με διατροφικές πληροφορίες ή error message.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"
    params = {"apiKey": api_key}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None  # Δεν υπάρχει διαθέσιμη πληροφορία

# 🔹 Δοκιμή της συνάρτησης με συγκεκριμένα υλικά
ingredients_list = ["chicken", "rice"]
recipes = get_recipes_by_ingredients(ingredients_list)

if isinstance(recipes, list):
    print("\n Suggested Recipes:")
    for recipe in recipes:
        print(f"- {recipe['title']} (ID: {recipe['id']})")

        # Λήψη διατροφικών πληροφοριών
        nutrition = get_nutrition_info(recipe['id'])
        if nutrition:
            print(f"   Calories: {nutrition.get('calories', 'N/A')}")
            print(f"   Carbs: {nutrition.get('carbs', 'N/A')}")
            print(f"   Fat: {nutrition.get('fat', 'N/A')}")
            print(f"   Protein: {nutrition.get('protein', 'N/A')}")
        else:
            print("   Nutrition info unavailable.")
else:
    print(recipes)

