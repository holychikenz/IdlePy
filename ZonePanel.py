import panel as pn
import hvplot.pandas
import json
from idlescape.dashboard import InteractiveCharacter
#from idlescape import *

location_file = "data/locations.json"
item_file = "data/items.json"
html = pn.pane.HTML('')


def update_cookie():
    v = (pn.state.cookies.get("interactive_character", "{}"))
    mining_equipment = (pn.state.cookies.get("mining_equipment", "{}"))
    foraging_equipment = (pn.state.cookies.get("foraging_equipment", "{}"))
    fishing_equipment = (pn.state.cookies.get("fishing_equipment", "{}"))
    html.object = f"""
    <script>document.cookie="interactive_character={v}; expires=Tue, 01 Jan 2030;"</script>
    <script>document.cookie="mining_equipment={mining_equipment}; expires=Tue, 01 Jan 2030;"</script>
    <script>document.cookie="foraging_equipment={foraging_equipment}; expires=Tue, 01 Jan 2030;"</script>
    <script>document.cookie="fishing_equipment={fishing_equipment}; expires=Tue, 01 Jan 2030;"</script>
    """


pn.state.onload(update_cookie)
pc = InteractiveCharacter(item_file, location_file)

action_selector = pn.widgets.Select(name='Action', options={'Mining': pc.mining, 'Foraging': pc.foraging,
                                                            "Fishing": pc.fishing})
zone_selector = pn.widgets.Select(options=action_selector.value.list_of_actions())


@pn.depends(action_selector.param.value, watch=True)
def _update_zone(action):
    locations = action.list_of_actions()
    zone_selector.options = locations
    zone_selector.value = locations[0]


def zone_summary(action, zone):
    pc.assign_equipment(action.get_action_primary_attribute())
    item_series = action.location_item_histogram(zone, interval='hour').round(2)
    item_series.name = 'Count / Hour'
    options = {'rot': 45, 'min_height': 400, 'max_height': 800, 'responsive': True}
    tab_options = {'sortable': True, 'height': 800}
    the_plot = item_series[item_series.gt(0)].hvplot.bar(**options)
    the_table = item_series.hvplot.table(columns=['index', 'Count / Hour'], **tab_options)
    return pn.Column(the_plot, the_table)


interactive_plot = pn.bind(zone_summary, action_selector, zone_selector)
selection_column = pn.Column(action_selector, zone_selector)


def update(event):
    zone_selector.param.trigger('value')
    update_cookie()


pc.assign_callback(update)
stats_column = pn.Column(*(pc.level_widgets()))
equipment_column = pn.Column(*(pc.equipment_widgets()))
enchant_column = pn.Column(*(pc.enchant_widgets()))
selection_tabs = pn.Tabs(('Action', selection_column), ('Character', stats_column), ('Equipment', equipment_column),
                         ('Enchants', enchant_column))

template = pn.template.FastListTemplate(
    title='Idlescape',
    sidebar=selection_tabs,  # choices
    main=[interactive_plot, pn.Row('', html)],
    accent_base_color="#88d8b0",
    header_background="#88d8b0",
)

template.servable()
