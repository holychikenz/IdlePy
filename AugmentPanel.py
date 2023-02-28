import panel as pn
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
from panel.template import DarkTheme
from idlescape.augmenting import Augmenting

mpl.use('agg')

# pn.config.throttled = True

old_aug = Augmenting()
new_aug = Augmenting()
new_aug.old_chances = 0

# Simple selectors
test_level = pn.widgets.EditableFloatSlider(name='test_level', start=1, end=200, step=1)
test_level.value = 160
base_probability = pn.widgets.EditableFloatSlider(name='base_probability', start=0.5, end=1.0, step=0.01)
base_probability.value = 0.9
level_scaling = pn.widgets.EditableFloatSlider(name='level_scaling', start=0.0, end=3.0, step=0.01)
level_scaling.value = 1.33
level_norm = pn.widgets.EditableFloatSlider(name='level_norm', start=100, end=300, step=1)
level_norm.value = 200
level_weight = pn.widgets.EditableFloatSlider(name='level_weight', start=0.1, end=10, step=0.1)
level_weight.value = 1.0
tool_bonus = pn.widgets.EditableFloatSlider(name='tool_bonus', start=0, end=100, step=1)
tool_bonus.value = 50
exp_scale = pn.widgets.EditableFloatSlider(name='exp_scale', start=1, end=100, step=1)
exp_scale.value = 20
exp_tier_power = pn.widgets.EditableFloatSlider(name='exp_tier_power', start=1, end=4, step=0.01)
exp_tier_power.value = 2.5
exp_level_power = pn.widgets.EditableFloatSlider(name='exp_level_power', start=1, end=4, step=0.01)
exp_level_power.value = 1.25

info_string = """
# Base Formulas

```
P(target) = (base_probability + sqrt(character_level * level_scaling) / level_norm)^(target / level_weight) + old_chances
```

```
experience(tier, target) = exp_scale * tier^exp_tier_power * target^exp_level_power
```
"""
info_panel = pn.pane.Markdown(info_string)


# The plots
def summary_plots(test_level_value, base_probability_value, level_scaling_value, level_norm_value,
                  level_weight_value, tool_bonus_value, exp_scale_value, exp_tier_power_value, exp_level_power_value):
    new_aug.base_probability = base_probability_value
    new_aug.level_scaling = level_scaling_value
    new_aug.level_norm = level_norm_value
    new_aug.level_weight = level_weight_value
    new_aug.tool_bonus = tool_bonus_value
    new_aug.exp_scale = exp_scale_value
    new_aug.exp_tier_power = exp_tier_power_value
    new_aug.exp_level_power = exp_level_power_value
    # Test level as parameter?
    # Plot of success chance
    fig0, ax0 = plt.subplots()
    ax0.step(old_aug.x_values, old_aug.probability_distribution(test_level_value)[0],
             label=f"Old: {test_level_value}")
    ax0.step(new_aug.x_values, new_aug.probability_distribution(test_level_value)[0],
             label=f"New: {test_level_value}(+{new_aug.tool_bonus})")
    ax0.legend()
    ax0.set_ylim(bottom=0)
    ax0.set_xlim(0, 30)
    mpl_pane_0 = pn.pane.Matplotlib(fig0, height=400)
    # Mean augment
    character_levels = np.arange(1, 180, 1)
    fig1, ax1 = plt.subplots()
    ax1.plot(character_levels, old_aug.mean_augment(character_levels), label="Old")
    ax1.plot(character_levels, new_aug.mean_augment(character_levels), label="New")
    ax1.set_xlabel("Character Level (w/o tool)")
    ax1.set_ylabel("Mean Augment")
    ax1.set_xlim(character_levels.min(), character_levels.max())
    ax1.legend()
    ax1.grid()
    mpl_pane_1 = pn.pane.Matplotlib(fig1, height=400)
    # Experience for T5
    fig2, ax2 = plt.subplots(1, 2, figsize=(14, 6))
    old_array = np.array([old_aug.mean_experience(5, c_lvl) for c_lvl in character_levels])
    new_array = np.array([new_aug.mean_experience(5, c_lvl) for c_lvl in character_levels])
    ax2[0].plot(character_levels, old_array, label="Old")
    ax2[0].plot(character_levels, new_array, label="New")
    ax2[0].set_xlabel("Character Level")
    ax2[0].set_ylabel("Mean Experience / T5 Aug")
    ax2[0].set_xlim(character_levels.min(), character_levels.max())
    ax2[0].legend()
    ax2[1].plot(character_levels, old_array / new_array)
    ax2[1].set_xlabel("Character Level")
    ax2[1].set_ylabel("Ratio (Old / New)")
    ax2[1].set_xlim(character_levels.min(), character_levels.max())
    mpl_pane_2 = pn.pane.Matplotlib(fig2, height=400)
    # Cost
    fig3, ax3 = plt.subplots(1, 2, figsize=(14, 6))
    stop_level = 30
    old_array = old_aug.mean_cost(test_level_value, 1.0, 0.1)[1:stop_level]
    new_array = new_aug.mean_cost(test_level_value, 1.0, 0.1)[1:stop_level]
    x_values = old_aug.x_values[1:stop_level]
    ax3[0].plot(x_values, old_array, label="Old")
    ax3[0].plot(x_values, new_array, label="New")
    ax3[0].set_xlabel("Target Level")
    ax3[0].set_ylabel("Cost (normalized to base=1, aug=0.1)")
    ax3[0].set_xlim(x_values.min(), x_values.max())
    ax3[0].set_ylim(bottom=1)
    ax3[0].set_yscale("log")
    ax3[0].legend()
    ax3[1].plot(x_values, new_array / old_array)
    ax3[1].set_xlabel("Character Level")
    ax3[1].set_ylabel("Ratio (New / Old)")
    ax3[1].set_xlim(x_values.min(), x_values.max())
    mpl_pane_3 = pn.pane.Matplotlib(fig3, height=400)

    return_column = pn.Column(info_panel, mpl_pane_0, mpl_pane_1, mpl_pane_2, mpl_pane_3)
    return return_column


interactive_plot = pn.bind(summary_plots, test_level, base_probability, level_scaling, level_norm, level_weight,
                           tool_bonus, exp_scale, exp_tier_power, exp_level_power)
selection_column = pn.Column(test_level, base_probability, level_scaling, level_norm, level_weight, tool_bonus,
                             exp_scale, exp_tier_power, exp_level_power)

template = pn.template.FastListTemplate(
    title='Idlescape Augmenting',
    sidebar=[selection_column],
    main=interactive_plot,
    theme=DarkTheme,
    theme_toggle=False,
)

template.servable()
