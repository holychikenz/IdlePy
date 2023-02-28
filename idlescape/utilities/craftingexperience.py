import json
import nlopt
import numpy as np


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
                    if 'craftingExperience' not in info:
                        keep_recipe = False
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
        def _mono_loop():
            for recipe in recipe_list:
                if len(recipe['recipe']) == 1:
                    main_ingredient = next(iter(recipe['recipe']))
                    count = recipe['recipe'][main_ingredient]
                    xp_rate = recipe['experience'] / count
                    best_result = {
                        "xp": xp_rate,
                        "recipe": recipe,
                    }
                    if main_ingredient in results:
                        old_value = results[main_ingredient]
                        if old_value['xp'] < best_result['xp']:
                            results[main_ingredient] = best_result
                    else:
                        results[main_ingredient] = best_result

        def _duo_loop():
            duo_sets = {}
            for recipe in recipe_list:
                if len(recipe['recipe']) == 2:
                    ingredient_pair = ([key for (key, value) in recipe['recipe'].items()])
                    ingredient_pair.sort()
                    if ingredient_pair[0] in results:
                        continue
                    if ingredient_pair[1] in results:
                        continue
                    ig_pair_name = '_^_'.join(ingredient_pair)
                    current_array = duo_sets.get(ig_pair_name, [])
                    current_array.append(recipe)
                    duo_sets[ig_pair_name] = current_array
            for (key, duo) in duo_sets.items():
                if len(duo) > 1:
                    # Fit a line
                    name_a, name_b = key.split("_^_")
                    y_values = np.array([v['experience'] for v in duo])
                    x_a = np.array([v['recipe'][name_a] for v in duo])
                    x_b = np.array([v['recipe'][name_b] for v in duo])

                    def _objective(x, grad):
                        if grad.size > 0:
                            grad[:] = 2 * x
                        return np.sum((x[0] * x_a + x[1] * x_b - y_values) ** 2)

                    opt = nlopt.opt(nlopt.LN_SBPLX, 2)
                    opt.set_min_objective(_objective)
                    p0 = opt.optimize([1.0, 1.0])
                    results[name_a] = {"xp": p0[0], "recipe": duo[0]['recipe']}
                    results[name_b] = {"xp": p0[1], "recipe": duo[0]['recipe']}

        # 3> We should be good to estimate Traps now
        def _do_traps():
            traps = [item['name'] for (key, item) in self.items.items() if ' Trap' in item['name']]
            for recipe in recipe_list:
                if recipe['name'] in traps:
                    # Hopefully we have identified the mono-xp already
                    trap_yield = self.items[recipe['name']].get('yield', [])
                    base_experience = recipe.get('experience', 0)
                    for trap_output in trap_yield:
                        count = trap_output.get('chance', 1) * (
                                    trap_output.get('max', 1) + trap_output.get('min', 1)) / 2
                        output_name = self.id_to_name[str(trap_output.get('id', 0))]
                        estimate = results.get(output_name, {'xp': 0})
                        base_experience += estimate.get('xp', 0) * count
                    recipe['experience'] = base_experience

        # 4> Iterate through a few times filling in what we can, pruning out dead recipes
        def _eliminate(mod_list):
            new_recipe_list = []
            for recipe in mod_list:
                free_ingredients = np.sum([1 for ingredient in recipe['recipe'].keys() if ingredient not in results])
                if free_ingredients > 1:
                    new_recipe_list.append(recipe)
                if free_ingredients == 1:
                    base_experience = recipe['experience']
                    the_missing_ingredient = None
                    the_missing_count = None
                    for (ingredient, count) in recipe['recipe'].items():
                        if ingredient in results:
                            base_experience -= results[ingredient]['xp'] * count
                        else:
                            the_missing_ingredient = ingredient
                            the_missing_count = count
                    results[the_missing_ingredient] = {'xp': base_experience / the_missing_count, 'recipe': recipe}
            return new_recipe_list

        _mono_loop()
        _duo_loop()
        _do_traps()
        _mono_loop()
        recipe_list = _eliminate(recipe_list)
        recipe_list = _eliminate(recipe_list)
        recipe_list = _eliminate(recipe_list)

        return results
