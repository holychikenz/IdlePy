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
                / self.level_norm) ** (item_level / self.level_weight) + self.old_chances

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
        cost = (base_cost / (np.cumsum(failure_pdf[::-1])[::-1])
                + failure_pdf * self.x_values * augment_cost)
        return cost

    def mean_experience(self, item_tier, character_level):
        failure_pdf, statistics = self.probability_distribution(character_level)
        experience_curve = self.experience_formula(item_tier, self.x_values)
        total_experience = np.sum(statistics['cum_product'] * experience_curve)
        return total_experience / statistics['mean']
