import panel as pn
from panel.template import DarkTheme
from idlescape.dashboard import InteractiveCharacter, ActionSummary, BalanceEditor

pn.config.throttled = True
player_character = InteractiveCharacter()
action_selector = pn.widgets.Select(name='Action', options={'Mining': player_character.mining,
                                                            'Foraging': player_character.foraging,
                                                            'Fishing': player_character.fishing})
zone_selector = pn.widgets.Select(options=action_selector.value.list_of_actions())
open_modal_button = pn.widgets.Button(name="Adjust Balance", button_type='default', )
action_summary = ActionSummary(player_character)
balance = BalanceEditor(player_character)
file_download = pn.widgets.FileDownload(callback=balance.save_json, filename='locations.json')


@pn.depends(action_selector.param.value, watch=True)
def _update_zone(action):
    locations = action.list_of_actions()
    zone_selector.options = locations
    zone_selector.value = locations[0]


interactive_plot = pn.bind(action_summary.summarize, action_selector, zone_selector)
selection_column = pn.Column(action_selector, zone_selector)


def update(event):
    zone_selector.param.trigger('value')


player_character.assign_callback(update)
stats_column = pn.Column(*(player_character.level_widgets()))
equipment_column = pn.Column(*(player_character.equipment_widgets()))
enchant_column = pn.Column(*(player_character.enchant_widgets()))
selection_tabs = pn.Tabs(('Action', selection_column), ('Character', stats_column), ('Equipment', equipment_column),
                         ('Enchants', enchant_column))
main_tabs = pn.Tabs(('Zone Summary', interactive_plot))

template = pn.template.FastListTemplate(
    title='Idlescape',
    sidebar=[pn.Column(open_modal_button, file_download), selection_tabs],
    main=main_tabs,
    theme=DarkTheme,
    theme_toggle=False,
    modal=balance.display_editor(update),
)

open_modal_button.on_click(lambda event: template.open_modal())

template.servable()
