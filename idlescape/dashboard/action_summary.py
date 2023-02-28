import panel as pn
import numpy as np
import pandas as pd
import hvplot.pandas
from idlescape.dashboard import InteractiveCharacter


class ActionSummary:
    """
    Action Summary displayed per action / zone pair

    Calculate the individual item drop rates and display as graphs and tables. Additionally provide
    a summary table for the total experience from different components of the drops.
    """

    def __init__(self, character: InteractiveCharacter):
        """
        Parameters
        ----------
        character : InteractiveCharacter
        """
        self.character = character
        self.alt_heat = {"Fish Oil": 240}
        foraging_craft_xp = {"Log": 5, "Oak Log": 10, "Willow Log": 15, "Maple Log": 30, "Yew Log": 45,
                             "Elder Log": 100}
        fishing_craft_xp = {"Raw Tentacle Meat": 150, "Rotten Driftwood": 5, "Sturdy Driftwood": 10,
                            "Aqueous Grass": 1, "Water Weeds": 3, "River Vines": 8.7, "Violet Ribbons": 16.45,
                            "White Reeds": 37.6, "Ancient Kelp": 61.5}
        mining_craft_xp = {"Bronze Bar": 5, "Iron Bar": 10, "Gold Bar": 12, "Mithril Bar": 20, "Adamantite Bar": 40,
                           "Runite Bar": 70, "Stygian Bar": 150}
        ore_xp = {
            "Copper Ore": mining_craft_xp["Bronze Bar"]/2,
            "Tin Ore": mining_craft_xp["Bronze Bar"]/2,
            "Iron Ore": mining_craft_xp["Iron Bar"] * 2/5,
            "Gold Ore": mining_craft_xp["Gold Bar"] * 2/15,
            "Mithril Ore": mining_craft_xp["Mithril Bar"] * 2/8,
            "Adamantite Ore": mining_craft_xp["Adamantite Bar"] * 2/15,
            "Runite Ore": mining_craft_xp["Runite Bar"] * 2/23,
            "Stygian Ore": mining_craft_xp["Stygian Bar"] * 2/38,
        }
        self.craft_xp = foraging_craft_xp | fishing_craft_xp | mining_craft_xp | ore_xp
        for (k, v) in self.character.player.item_data.items():
            if "fish" in v.get("tags", []):
                crafting_xp = 48 * v.get("size", 0) / 20
                self.craft_xp[v["name"]] = crafting_xp
                self.alt_heat[v["name"]] = v.get("size", 0) / 20 * 240

    def summarize(self, action, zone):
        """

        Parameters
        ----------
        action : str
            Mining, foraging, and fishing
        zone : str
            Based on a subset of locations

        Returns
        -------
        panel.Column
            Contains a bar graph and two tables
        """
        self.character.assign_equipment(action.primary_attribute)
        item_series = action.location_item_histogram(zone, interval='hour').round(2)
        item_series.name = 'Count / Hour'
        height_per_row = 25
        options = {'rot': 45, 'min_height': 400, 'max_height': 800, 'responsive': False}
        skip_items = ['Heat']
        the_plot = (item_series[item_series.gt(0)]).drop(labels=skip_items, errors='ignore').hvplot.bar(**options)
        tab_options = {'sortable': True, 'height': (len(item_series) + 1) * height_per_row}
        the_table = item_series.hvplot.table(columns=['index', 'Count / Hour'], **tab_options)

        total_craft_xp = np.sum([item_series.get(k, 0) * v for (k, v) in self.craft_xp.items()])
        total_cooking_xp = 0
        total_combustible = 0
        for (k, v) in item_series.items():
            this_item = self.character.player.get_item_by_name(k)
            total_cooking_xp += 5 * (this_item.get('difficulty', 0) + this_item.get('bonusDifficultyXP', 0)) * v
            total_combustible += (this_item.get('heat', 0) + self.alt_heat.get(k, 0)) * v
        total_zone_experience = action.zone_experience_rate(zone)
        second_df = pd.Series({'Experience': total_zone_experience,
                               'Crafting': total_craft_xp,
                               'Cooking': total_cooking_xp,
                               'Combustible': total_combustible})
        second_df = second_df[second_df.gt(0)].round(0)
        second_df.name = 'Count / Hour'
        second_table = second_df.hvplot.table(columns=['index', 'Count / Hour'],
                                              height=(len(second_df) + 1) * height_per_row)
        return pn.Column(the_plot, second_table, the_table)
