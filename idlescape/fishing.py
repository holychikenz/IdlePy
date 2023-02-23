from abc import ABC

from .gathering import *
from .character import *
import numpy as np


class Fishing(Gathering, ABC):
    player = None
    valid_enchants = ['gathering', 'empoweredGathering', 'haste', 'pungentBait', 'deadliestCatch', 'fishingMagnetism',
                      'reinforcedLine', 'fiberFinder', 'fishing']
    primary_attribute = 'fishing_level'
    action_name = "Action-Fishing"

    def __init__(self, character, location_data, **kwargs):
        self.player = character
        self.items = self.player.item_data
        self.locations = self._select_action_locations(location_data)
        self.accuracy = kwargs.get("accuracy", 10000)
        self.alt_experience = kwargs.get("alt_experience", None)

    def _effective_level(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        level = self.player.fishing_level
        gear_base = self.player.fishing_bonus
        bait = self.player.bait_fishing_bonus * (1 + self.get_enchant('deadliestCatch') * 0.05)
        return level + bait + gear_base * set_bonus

    def _bait_power(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.bait_power
        gear_enchant = (self.get_enchant('pungentBait') * 3
                        - self.get_enchant('fishingMagnetism') * 2)
        bait = self.player.bait_bait_power * (1 + self.get_enchant('deadliestCatch') * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _bonus_rarity(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.bonus_rarity
        gear_enchant = self.get_enchant('fishingMagnetism') * 2
        bait = self.player.bait_bonus_rarity * (1 + self.get_enchant('deadliestCatch') * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _reel_power(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.reel_power
        gear_enchant = (self.get_enchant('reinforcedLine') * 3
                        - self.get_enchant('fishingMagnetism') * 2)
        bait = self.player.bait_reel_power * (1 + self.get_enchant('deadliestCatch') * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _node_rates(self, location):
        frequency_dict = dict()
        for (k, v) in location.nodes.items():
            frequency = (v.frequency + self._bonus_rarity()) * (1 + self._effective_level() / 360)
            frequency = min(frequency, v.max_frequency)

            frequency_dict[k] = max(0, frequency)
        # Fishing magnetism boost
        positive_average = np.mean([v for (k, v) in frequency_dict.items() if v > 0])
        boosted_frequency_dict = \
            {k: (v * (1 + self.get_enchant('fishingMagnetism') * 2 / 50) if v < positive_average else v)
             for (k, v) in frequency_dict.items()}
        # Normalize
        total_frequency = sum([v for (k, v) in boosted_frequency_dict.items()])
        return {k: v / total_frequency for (k, v) in boosted_frequency_dict.items()}

    def _get_relative_frequency(self, loot):
        frequency = (loot.frequency + self._bonus_rarity()) * (1 + self._effective_level() / 360)
        frequency = min(frequency, loot.max_frequency)
        if loot.item_class == "fiber":
            frequency = frequency * (1 + self.get_enchant('fiberFinder') * 0.25)
        return max(0, frequency)

    def _node_base_chance(self, location):
        fishing_enchant = self.get_enchant("fishing")
        # Changed bait_power from 420 to 200, 0.2 to 0.3
        return 0.4 + (self._effective_level() - location.level * 1.25) / 275 + (fishing_enchant * 0.025) + (
                self._bait_power() / 200)

    def _average_tries_to_find_node(self, location):
        average_tries = 0
        chance_to_reach_this_attempt = 1
        base_chance = self._node_base_chance(location)
        fishing_enchant = self.get_enchant('fishing')

        for nodeFindFailures in range(7):
            chance_this_attempt = min(1, base_chance + fishing_enchant * 0.025 + nodeFindFailures / 6)
            average_tries += chance_this_attempt * chance_to_reach_this_attempt * (nodeFindFailures + 1)
            chance_to_reach_this_attempt *= 1 - chance_this_attempt
        return average_tries

    def _average_node_size(self, location, node):
        nodes = self.accuracy
        return self._calculate_node_resources(node, location, trials=nodes)

    def _calculate_node_resources(self, node, location, **kwargs):
        zone_level = location.level
        min_base = node.minimum_base_amount
        max_base = node.maximum_base_amount
        trials = kwargs.get('trials', 1)
        return _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, self._effective_level(),
                                                     self._bait_power(),
                                                     trials)

    def _node_sizes(self, location):
        return {k: self._average_node_size(location, v) for (k, v) in location.nodes.items()}

    def _node_actions(self, location):
        return {k: self._average_tries_to_finish_node(location, v) for (k, v) in location.nodes.items()}

    def _average_tries_to_finish_node(self, location, node, **kwargs):
        zone_level = location.level
        min_base = node.minimum_base_amount
        max_base = node.maximum_base_amount
        fishing_level = self.player.fishing_level + self.player.fishing_bonus
        bait_power = self.player.bait_power
        base_chance = self._node_base_chance(location)
        fishing_enchant = self.get_enchant('fishing')
        return _average_tries_to_finish_node_jit_fishing(base_chance, zone_level, min_base, max_base, fishing_level,
                                                         bait_power, fishing_enchant, self.accuracy)

    def zone_action_rate(self, location_name):
        """
        Action rate (per hour)
        """
        location = self.get_location_by_name(location_name)
        if location.level > self.player.fishing_level:
            return 0

        node_rates = self._node_rates(location)
        node_sizes = self._node_sizes(location)
        node_actions = self._node_actions(location)
        haste = self.get_enchant('haste')

        base_time = location.base_duration / 1000 / (1 + haste * 0.04)
        node_search_time = max(1, base_time * 1.75 * (1 - (self._bait_power() / 400)))
        a_find = self._average_tries_to_find_node(location)
        loot_search_time = max(1, base_time / 1.25 * (200 / (self._reel_power() + 200)))

        total_actions = 0
        total_time = 0
        for (name, rate) in node_rates.items():
            total_time += (node_search_time * a_find + loot_search_time * node_actions[name]) * rate
            total_actions += node_sizes[name] * rate
        return total_actions / total_time * 3600


Gathering.register(Fishing)

# Numba JITFishing section
try:
    from numba import jit


    @jit()
    def _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, trials):
        total_resources = 0
        for i in range(trials):
            maximum_node_size = np.floor(max_base + (np.random.rand() * (fishing_level - zone_level) / 8) + np.floor(
                np.random.rand() * bait_power / 20))
            minimum_node_size = np.floor(min_base + (np.random.rand() * (fishing_level - zone_level) / 6) + np.floor(
                np.random.rand() * bait_power / 10))

            lucky_chance = 0.05 + (bait_power / 2000)
            if np.random.rand() <= lucky_chance:
                minimum_node_size *= 1.5
                maximum_node_size *= 3.0

            delta = abs(maximum_node_size - minimum_node_size)
            small = min(maximum_node_size, minimum_node_size)
            total_resources += np.floor(np.random.rand() * (delta + 1) + small)
        return total_resources / trials


    @jit
    def _average_tries_to_finish_node_jit_fishing(base_chance, zone_level, min_base, max_base, fishing_level,
                                                  bait_power,
                                                  fishing, trials):
        node_resources = np.array(
            [int(_calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, 1))
             for
             _ in range(trials)])
        min_node_count = min(node_resources)
        max_node_count = max(node_resources)
        node_average = []
        for total_node_resources in range(min_node_count, max_node_count + 1):
            total_tries_sub = 0.0
            for n_res in range(total_node_resources, 0, -1):
                never_tell_me_the_odds = min(1.0, base_chance + fishing * 0.025 + n_res / 48)
                total_tries_sub += 1 / never_tell_me_the_odds
            node_average.append(total_tries_sub)
        node_average = np.array(node_average)
        return np.mean(node_average[(node_resources - min_node_count)])

except ImportError:
    def _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, trials):
        maximum_node_size = np.floor(max_base + (np.random.rand(trials) * (fishing_level - zone_level) / 8) + np.floor(
            np.random.rand(trials) * bait_power / 20))
        minimum_node_size = np.floor(min_base + (np.random.rand(trials) * (fishing_level - zone_level) / 6) + np.floor(
            np.random.rand(trials) * bait_power / 10))

        lucky_chance = 0.05 + (bait_power / 2000)
        lucky_rolls = np.random.rand(trials) <= lucky_chance
        minimum_node_size = minimum_node_size * (1 + 0.5 * lucky_rolls)
        maximum_node_size = maximum_node_size * (1 + 2.0 * lucky_rolls)

        delta = abs(maximum_node_size - minimum_node_size)
        small = np.min([maximum_node_size, minimum_node_size], axis=0)
        total_resources = sum(np.floor(np.random.rand(trials) * (delta + 1) + small))
        return total_resources / trials


    def _average_tries_to_finish_node_jit_fishing(base_chance, zone_level, min_base, max_base, fishing_level,
                                                  bait_power,
                                                  fishing, trials):
        node_resources = np.array(
            [int(_calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, 1))
             for
             _ in range(trials)])
        min_node_count = min(node_resources)
        max_node_count = max(node_resources)
        node_average = []
        for total_node_resources in range(min_node_count, max_node_count + 1):
            total_tries_sub = 0.0
            for n_res in range(total_node_resources, 0, -1):
                never_tell_me_the_odds = min(1.0, base_chance + fishing * 0.025 + n_res / 48)
                total_tries_sub += 1 / never_tell_me_the_odds
            node_average.append(total_tries_sub)
        node_average = np.array(node_average)
        return np.mean(node_average[(node_resources - min_node_count)])