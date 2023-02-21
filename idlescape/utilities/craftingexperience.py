import json


class CraftingExperience:

    def __init__(self, data_file, **kwargs):
        with open(data_file) as dat:
            self.item_data = json.load(dat)
        self.items = {v['name']: v for (k, v) in self.item_data.items()}
        self.id_to_name = {k: v['name'] for (k, v) in self.item_data.items()}
        self.name_to_id = {v: k for (k, v) in self.id_to_name.items()}
        self.verbose = kwargs.get("verbose", False)

    def identify_crafting_recipes(self, item_list, free_list):
        recipe_list = []
        for (name, info) in self.items.items():
            if 'requiredResources' in info:
                for recipe in info['requiredResources']:
                    append_recipe = {}
                    keep_recipe = True
                    for (ingredient, count) in recipe.items():
                        ingredient_name = self.id_to_name.get(ingredient, "")
                        if (ingredient_name not in item_list) and (ingredient_name not in free_list):
                            keep_recipe = False
                        if ingredient_name not in free_list:
                            append_recipe[ingredient_name] = count
                    if keep_recipe:
                        recipe_list.append({
                            'id': info['id'],
                            'name': info['name'],
                            'experience': info.get('craftingExperience', 0),
                            'recipe': append_recipe,
                        })
        return recipe_list

    def estimate_item_xp(self, **kwargs):
        item_list = kwargs.get("item_list", list(self.items.keys()))
        free_list = kwargs.get("free_list", [])
        # 1. Identify available recipes
        # 2. Remove "free" items from the recipes
        # 3. Remove recipes with non-list items
        # 4. Search through single-item recipes first and assign values
        # 5. Iteratively search through remaining recipes, subtracting single-value
        # 6. Traps?
        # 7. Report values, and top recipes
        recipe_list = self.identify_crafting_recipes(item_list, free_list)
        results = {}
        # 1> Available mono-recipes
        for recipe in recipe_list:
            if len(recipe['recipe']) == 1:
                main_ingredient, count = next(iter(recipe['recipe']))
        return recipe_list
