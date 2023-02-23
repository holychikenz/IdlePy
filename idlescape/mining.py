from abc import ABC

import numpy as np
from .gathering import *
from .character import *


class Mining(Gathering, ABC):
    player = None
    valid_enchants = ['gathering', 'empoweredGathering', 'haste', 'superheating', 'empoweredSuperheating']
    primary_attribute = 'mining_level'
    action_name = "Action-Mining"
    sh_table = {
        101: 201,  # Copper
        102: 201,  # Tin
        103: 202,  # Iron
        104: 203,  # Gold
        105: 204,  # Mithril
        106: 205,  # Adamantite
        107: 206,  # Runite
        110: 3001,  # Sand
        114: 207,  # Stygian
        115: 208,  # Void
    }

    def __init__(self, character, location_data, **kwargs):
        self.player = character
        self.items = self.player.item_data
        self.locations = self._select_action_locations(location_data)
        self.alt_experience = kwargs.get("alt_experience", None)

    def _effective_level(self):
        return self.player.mining_level + self.player.mining_bonus * (1 + self.player.mining_set_bonus)

    def _node_rates(self, location):
        frequency_dict = dict()
        for (k, v) in location.nodes.items():
            frequency = v.frequency
            frequency_dict[k] = max(0, frequency)
        total_frequency = sum([v for (k, v) in frequency_dict.items()])
        return {k: v / total_frequency for (k, v) in frequency_dict.items()}

    def _average_node_size(self, location, node):
        return (node.maximum_base_amount + node.minimum_base_amount) / 2

    def _node_sizes(self, location):
        return {k: self._average_node_size(location, v) for (k, v) in location.nodes.items()}

    def _node_actions(self, location):
        return self._node_sizes(location)

    def zone_action_rate(self, location_name):
        location = self.get_location_by_name(location_name)
        if location.level > self.player.mining_level:
            return 0
        haste = self.get_enchant('haste')
        rate_modifier = (self._effective_level() + 99) / 100 * (1 + haste * 0.04)
        return rate_modifier * 3600000 / location.base_duration


Gathering.register(Mining)
