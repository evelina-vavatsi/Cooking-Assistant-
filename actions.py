import os
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from dotenv import load_dotenv

# Φόρτωση μεταβλητών περιβάλλοντος (API Key)
load_dotenv()
api_key = os.getenv("SPOONACULAR_API_KEY")

def text2int(textnum):
    """
    Μετατρέπει αριθμούς σε λέξεις (π.χ. "twenty" -> 20)
    """
    num_dict = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20,
                "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60}
    return num_dict.get(textnum.lower(), None)

class ActionSuggestRecipe(Action):
    def name(self) -> str:
        return "action_suggest_recipe"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        ingredients = tracker.get_slot("ingredients")
        cooking_time = tracker.get_slot("cooking_time")
        
        if not api_key:
            dispatcher.utter_message(text="I can't fetch recipes right now. Please try again later.")
            return []
        if not ingredients:
            dispatcher.utter_message(text="Please provide some ingredients first!")
            return []
        
        ingredients_query = ",".join(ingredients)
        url = "https://api.spoonacular.com/recipes/findByIngredients"
        
        params = {
            "ingredients": ingredients_query,
            "number": 3,
            "apiKey": api_key
        }
        if cooking_time:
            try:
                max_time = int(cooking_time)
            except ValueError:
                max_time = text2int(cooking_time)
            if max_time:
                params["maxReadyTime"] = max_time

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data:
                recipe_options = "**Here are some recipes you can make:**\n\n"
                recipe_dict = {}

                for index, item in enumerate(data, start=1):
                    recipe_id = item['id']
                    recipe_title = item['title']
                    recipe_link = f"https://spoonacular.com/recipes/{recipe_title.replace(' ', '-').lower()}-{recipe_id}"
                    recipe_options += f"{index}. **{recipe_title}**\n[View Recipe]({recipe_link})\n\n"
                    recipe_dict[str(index)] = recipe_id
                    recipe_dict[recipe_title.lower()] = recipe_id

                dispatcher.utter_message(text=recipe_options)
                return [SlotSet("available_recipes", recipe_dict)]
            else:
                dispatcher.utter_message(text=f"No recipes found for {', '.join(ingredients)}.")
        
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text=f"Oops! Something went wrong while fetching recipes: {str(e)}")
        
        return []

class ActionSelectRecipe(Action):
    def name(self) -> str:
        return "action_select_recipe"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        available_recipes = tracker.get_slot("available_recipes") or {}
        user_input = tracker.latest_message.get("text", "").strip().lower()
        selected_recipe = None

        if user_input in available_recipes:
            selected_recipe = available_recipes[user_input]
        else:
            for recipe_name, recipe_id in available_recipes.items():
                if recipe_name in user_input:
                    selected_recipe = recipe_id
                    break

        if selected_recipe:
            dispatcher.utter_message(text="Great choice! Fetching the details now.")
            return [SlotSet("selected_recipe", selected_recipe), FollowupAction("action_provide_recipe_details")]
        
        dispatcher.utter_message(text="I couldn't identify the recipe you want. Please try again by name or number!")
        return []

class ActionProvideRecipeDetails(Action):
    def name(self) -> str:
        return "action_provide_recipe_details"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        selected_recipe = tracker.get_slot("selected_recipe")

        if not selected_recipe:
            dispatcher.utter_message(text="Please select a recipe first.")
            return []
        
        url = f"https://api.spoonacular.com/recipes/{selected_recipe}/information"
        params = {"apiKey": api_key}

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            recipe_data = response.json()

            title = recipe_data.get("title", "Unknown Recipe")
            ingredients_list = "\n".join([f"- {ing['name']}" for ing in recipe_data.get("extendedIngredients", [])])
            instructions = recipe_data.get("instructions", "No instructions available.")

            message = f"**{title}**\n\n**Ingredients:**\n{ingredients_list}\n\n**Instructions:**\n{instructions}"
            dispatcher.utter_message(text=message)
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text=f"Error fetching recipe details: {str(e)}")
        
        return []

class ActionSuggestSubstitute(Action):
    def name(self) -> str:
        return "action_suggest_substitute"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        missing_ingr = tracker.get_slot("missing_ingredient")
        
        if not missing_ingr:
            dispatcher.utter_message(text="Which ingredient are you missing?")
            return []
        
        url = "https://api.spoonacular.com/recipes/ingredientSubstitutes"
        params = {
            "ingredientName": missing_ingr,
            "apiKey": api_key,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if "substitutes" in data and data["substitutes"]:
                suggested_substitute = data["substitutes"][0]
                dispatcher.utter_message(text=f"You can replace {missing_ingr} with {suggested_substitute}. Would you like to use this substitution?")
                return [SlotSet("substitute_ingredient", suggested_substitute)]
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find a substitute for {missing_ingr}.")
                return []
        
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text=f"Error retrieving substitution info: {str(e)}")
        return []

class ActionUpdateRecipeWithSubstitute(Action):
    def name(self) -> str:
        return "action_update_recipe_with_substitute"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> list:
        substitute = tracker.get_slot("substitute_ingredient")
        
        if not substitute:
            dispatcher.utter_message(text="I'm not sure which substitution you meant.")
            return []
        
        dispatcher.utter_message(text=f"Great! I'll update the recipe with {substitute}.")
        return []

