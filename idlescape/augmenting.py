import numpy as np
from .character import Character


class Augmenting:
    """
    Augmenting contains both a pure analytic form, and a simulation
    mode to check the values.
    """
    x_values = np.arange(0, 51, 1)
    base_probability = 0.9
    level_scaling = 1.5
    level_norm = 200
    exp_scale = 20
    exp_tier_power = 2.5
    exp_level_power = 1.5
    old_chances = 0.06
    tool_bonus = 0
    level_weight = 1.0

    def __init__(self):
        pass

    def single_probability(self, item_level, character_level):
        character_level = character_level + self.tool_bonus
        return (self.base_probability + np.sqrt(character_level * self.level_scaling)
                / self.level_norm) ** (item_level ** self.level_weight) + self.old_chances

    def experience_formula(self, item_tier, target_level):
        return self.exp_scale * item_tier**self.exp_tier_power * target_level**self.exp_level_power

    def probability_distribution(self, character_level, attempts=1):
        p_at_x = self.single_probability(self.x_values, character_level)
        p_at_x[p_at_x > 1] = 1
        p_at_x[p_at_x < 0] = 0
        cum_prod = np.cumprod(p_at_x)
        cum_failure = 1 - cum_prod
        cum_failure = cum_failure ** attempts
        failure_pdf = cum_failure - np.roll(cum_failure, 1)
        failure_pdf[0] = 0
        failure_pdf = failure_pdf / np.sum(failure_pdf)

        # Statistics
        mean = np.sum(self.x_values * failure_pdf)
        variance = np.sum((self.x_values - mean)**2 * failure_pdf)**0.5
        return_statistics = {
            "mean": mean,
            "variance": variance,
            "cum_product": cum_prod,
            "cum_failure": cum_failure,
        }

        return failure_pdf, return_statistics

    def mean_augment(self, character_levels):
        if not isinstance(character_levels, np.ndarray):
            character_levels = np.array([character_levels])
        mean_array = np.array([
            self.probability_distribution(clvl)[1]["mean"] for clvl in character_levels
        ])
        return mean_array

    def mean_cost(self, character_level, base_cost, augment_cost):
        failure_pdf, statistics = self.probability_distribution(character_level)
        attempts = (np.cumsum(np.roll(failure_pdf[::-1], 1))[::-1])
        base_cost_component = base_cost / attempts
        p_at_x = self.single_probability(self.x_values, character_level)
        p_at_x[p_at_x > 1] = 1
        p_at_x[p_at_x < 0] = 0
        cum_prod = np.cumprod(p_at_x)
        aug_cost_component = np.array([np.sum(cum_prod[:target]) for target in self.x_values]) / attempts * augment_cost
        return base_cost_component + aug_cost_component

    def mean_cost_target(self, target_level, character_level, base_cost, augment_cost):
        failure_pdf, statistics = self.probability_distribution(character_level)
        new_failure_pdf = failure_pdf[0:(target_level+1)]

    def soulbind_cost(self, base_cost, augment_cost):
        base_mods = []
        for z in self.x_values:
            if (z - 1)%3 == 0:
                base_mods.append((z-1)//3)
            else:
                base_mods.append(0)
        total_base_cost = np.cumsum(base_mods) * base_cost
        total_aug_cost = self.x_values * augment_cost
        return total_base_cost + total_aug_cost

    def mean_experience(self, item_tier, character_level):
        failure_pdf, statistics = self.probability_distribution(character_level)
        experience_curve = self.experience_formula(item_tier, self.x_values)
        total_experience = np.sum(statistics['cum_product'] * experience_curve)
        return total_experience / statistics['mean']

    # Simulations
    def simulate_pdf(self, character_level, attempts=1):
        trials = 10000
        final_values = []
        for t in range(trials):
            item_level = 0
            broken = False
            while not broken:
                chance = self.single_probability(item_level+1, character_level)
                if np.random.rand() < chance:
                    item_level += 1
                else:
                    final_values.append(item_level)
                    broken = True
        return np.array(final_values)

    def simulate_cost(self, target_level, character_level, base_cost, augment_cost):
        trials = 10000
        successes = 0
        total_cost = 0
        for t in range(trials):
            total_cost += base_cost
            item_level = 0
            broken = False
            while (not broken) and (item_level < target_level):
                chance = self.single_probability(item_level+1, character_level)
                total_cost += augment_cost
                if np.random.rand() < chance:
                    item_level += 1
                else:
                    broken = True
            if item_level >= target_level:
                successes += 1
        return total_cost / successes
