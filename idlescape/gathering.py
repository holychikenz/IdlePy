import numpy as np
import json
from abc import ABC, abstractmethod
import pandas as pd


class Gathering(ABC):
    @property
    @abstractmethod
    def player(self):
        pass

    @property
    def sh_table(self):
        return dict()

    @property
    @abstractmethod
    def valid_enchants(self):
        pass

    @property
    @abstractmethod
    def primary_attribute(self):
        pass

    @abstractmethod
    def _node_rates(self, location):
        pass

    @abstractmethod
    def _node_sizes(self, location):
        pass

    def get_enchant(self, name):
        if name in self.valid_enchants:
            enchantment_level = self.player.enchantments.get(name, 0)
            # Todo: Enchantment strength read from a json
            enchantment_strength = 1
            return enchantment_strength * enchantment_level
        return 0

    @abstractmethod
    def _node_actions(self, location):
        pass

    @abstractmethod
    def zone_action_rate(self, location_name):
        pass

    def zone_experience_rate(self, name):
        location = self.get_location_by_name(name)
        return location.experience * self.zone_action_rate(name)

    def get_maximum_experience(self):
        zone_xp_list = [self.zone_experience_rate(loc.name) for (k, loc) in self.locations.items()]
        return max(zone_xp_list)

    def _loot_rates(self, node):
        frequency_dict = dict()
        count_dict = dict()
        # Apply gathering, superheat, embers, etc.
        gathering = min(1, self.get_enchant("gathering") * 0.10)
        empowered_gathering = min(1, self.get_enchant("empoweredGathering") * 0.10)
        total_gathering = 1 - (1 - gathering) * (1 - empowered_gathering)
        superheat = min(1, self.get_enchant("superheating") * 0.01)
        empowered_superheat = min(1, self.get_enchant("empoweredSuperheating") * 0.01)
        total_superheat = 1 - (1 - superheat) * (1 - empowered_superheat)
        embers = self.get_enchant("embers") * 0.1
        # Calculate frequency
        for (idd, loot) in node.loot.items():
            frequency = self._get_relative_frequency(loot)
            frequency_dict[idd] = frequency_dict.get(idd, 0) + frequency
            # Todo Put in SH and Embers
        total_frequency = sum([v for (k, v) in frequency_dict.items()])
        frequency_dict = {k: v / total_frequency for (k, v) in frequency_dict.items()}
        # Collect items
        for (idd, loot) in node.loot.items():
            frequency = frequency_dict.get(idd, 0)
            new_base_items = ((loot.min_amount + loot.max_amount) / 2 + total_gathering - total_superheat) * frequency
            count_dict[idd] = count_dict.get(idd, 0) + new_base_items
            if total_superheat > 0:
                if idd in self.sh_table:
                    sh_id = self.sh_table[idd]
                    sh_count = total_superheat * frequency
                    count_dict[sh_id] = count_dict.get(sh_id, 0) + sh_count
                    lost_heat = sh_count * 1.5 * self.items[str(sh_id)].get('requiredResources', [{}])[0].get('2', 0)
                    count_dict[2] = count_dict.get(2, 0) - lost_heat
                    lost_fire = frequency * superheat * (1 - empowered_superheat)
                    count_dict[512] = count_dict.get(512, 0) - lost_fire
            if embers > 0:
                new_heat = self.items[str(idd)].get('heat', 0) * embers * frequency
                count_dict[2] = count_dict.get(2, 0) + new_heat
            if gathering > 0:
                lost_nature = frequency * gathering * 0.15 * (1 - empowered_gathering)
                count_dict[517] = count_dict.get(517, 0) - lost_nature
        return count_dict

    def _get_relative_frequency(self, loot):
        return max(0, np.min([loot.frequency, loot.max_frequency]))

    def list_of_actions(self):
        return list(self.locations.keys())

    def get_location_by_name(self, name):
        if name not in self.list_of_actions():
            raise IndexError(f'{name} not in {self.list_of_actions()}')
        return self.locations[name]

    def location_item_histogram(self, location_name, **kwargs):
        location = self.get_location_by_name(location_name)
        key = kwargs.get('key', 'name')
        interval = kwargs.get('interval', 'action')

        node_rates = self._node_rates(location)
        node_sizes = self._node_sizes(location)
        node_actions = self._node_actions(location)
        action_rate = self.zone_action_rate(location_name) if (interval == 'hour') else 1

        items = dict()
        total_actions = 0
        for (name, rate) in node_rates.items():
            avg_size = node_sizes[name]
            total_actions += node_actions[name] * rate
            loot_rates = self._loot_rates(location.nodes[name])
            for (itemid, count) in loot_rates.items():
                item_node_rate = count * avg_size * rate * action_rate
                items[itemid] = items.get(itemid, 0) + item_node_rate
        if key == 'name':
            return pd.Series({self.items[str(k)]['name']: v / total_actions for (k, v) in items.items()})
        else:
            return pd.Series({k: v / total_actions for (k, v) in items.items()})


class Location:
    def __init__(self, name, loc_id, action_type, base_duration, level, experience):
        self.name = name
        self.loc_id = loc_id
        self.action_type = action_type
        self.base_duration = base_duration
        self.level = level
        self.experience = experience
        self.nodes = dict()

    def list_of_nodes(self):
        return self.nodes.keys()


class Node:
    def __init__(self, node_id, frequency, max_frequency, minimum_base_amount, maximum_base_amount, tags):
        self.node_id = node_id
        self.frequency = frequency
        self.max_frequency = max_frequency
        self.minimum_base_amount = minimum_base_amount
        self.maximum_base_amount = maximum_base_amount
        self.tags = tags
        self.loot = dict()

    def list_of_loot(self):
        return self.loot.keys()


class NodeLoot:
    def __init__(self, idd, frequency, max_frequency, min_amount, max_amount, item_class):
        self.id = idd
        self.frequency = frequency
        self.max_frequency = max_frequency
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.item_class = item_class


def find_required_level(df):
    try:
        return df["accessRequirements"]["requiredSkills"][0]["level"]
    except:
        print(f'Could not find req. level in {df["name"]}')
        return 0


def find_location_xp(df):
    try:
        return df["xpPerCompletion"][0]["amount"]
    except:
        print(f'Could not find xp in {df["name"]}')
        return 100


def select_action_locations(datafile, item_data, action_type):
    locations = None
    with open(datafile) as j:
        locations = json.load(j)
    results = dict()
    for (k, v) in locations.items():
        if v['actionType'] == action_type:
            loc_name = v.get("name", "")
            loc_id = v.get("locID", 0)
            loc_duration = v.get("baseDuration", 0)
            loc_level = find_required_level(v)
            loc_experience = find_location_xp(v)
            this_location = Location(loc_name, loc_id, action_type, loc_duration, loc_level, loc_experience)
            node_list = v.get("nodes", [{"nodeID": "",
                                         "frequency": 1,
                                         "minimumBaseAmount": 1,
                                         "loot": v.get("loot", [])}])
            for node in node_list:
                node_id = node.get("nodeID", "")
                node_frequency = node.get("frequency", 1)
                node_max_freq = node.get("maxFrequency", node_frequency)
                node_min_base = node.get("minimumBaseAmount", 1)
                node_max_base = node.get("maximumBaseAmount", node_min_base)
                node_tags = node.get("tags", [])
                this_node = Node(node_id, node_frequency, node_max_freq, node_min_base, node_max_base, node_tags)
                for loot in node["loot"]:
                    loot_id = loot.get("id", 0)
                    loot_freq = loot.get("frequency", 1)
                    loot_max_freq = loot.get("maxFrequency", loot_freq)
                    loot_min_amount = loot.get("minAmount", 1)
                    loot_max_amount = loot.get("maxAmount", loot_min_amount)
                    item_class = item_data[str(loot_id)].get("class", "")
                    this_loot = NodeLoot(loot_id, loot_freq, loot_max_freq, loot_min_amount, loot_max_amount,
                                         item_class)
                    this_node.loot[loot["id"]] = this_loot
                this_location.nodes[node["nodeID"]] = this_node
            results[v['name']] = this_location
    return results
