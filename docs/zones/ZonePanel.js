importScripts("https://cdn.jsdelivr.net/pyodide/v0.22.1/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  const dirHandle = await navigator.storage.getDirectory();
  if ((await dirHandle.queryPermission({ mode: "readwrite" })) !== "granted") {
    if (
      (await dirHandle.requestPermission({ mode: "readwrite" })) !== "granted"
    ) {
      throw Error("Unable to read and write directory");
    }
  }

  let mountDir = "/idlecache";
  const nativefs = await pyodide.mountNativeFS(mountDir, dirHandle);
  setInterval( ()=>nativefs.syncfs(), 1000 );
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/0.14.3/dist/wheels/bokeh-2.4.3-py3-none-any.whl', 'https://cdn.holoviz.org/panel/0.14.3/dist/wheels/panel-0.14.3-py3-none-any.whl', 'pyodide-http==0.1.0', '/IdlePy/dist/idlescape-0.0.2-py3-none-any.whl', 'hvplot']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

import panel as pn
import pandas as pd
import numpy as np
import hvplot.pandas
from idlescape.dashboard import InteractiveCharacter

pn.config.throttled = True
pc = InteractiveCharacter()
action_selector = pn.widgets.Select(name='Action', options={'Mining': pc.mining, 'Foraging': pc.foraging,
                                                            'Fishing': pc.fishing})
zone_selector = pn.widgets.Select(options=action_selector.value.list_of_actions())

@pn.depends(action_selector.param.value, watch=True)
def _update_zone(action):
    locations = action.list_of_actions()
    zone_selector.options = locations
    zone_selector.value = locations[0]


def zone_summary(action, zone):
    pc.assign_equipment(action.primary_attribute)
    item_series = action.location_item_histogram(zone, interval='hour').round(2)
    item_series.name = 'Count / Hour'
    height_per_row = 25
    options = {'rot': 45, 'min_height': 400, 'max_height': 800, 'responsive': False}
    skip_items = ['Heat']
    the_plot = (item_series[item_series.gt(0)]).drop(labels=skip_items, errors='ignore').hvplot.bar(**options)
    tab_options = {'sortable': True, 'height': (len(item_series) + 1) * height_per_row}
    the_table = item_series.hvplot.table(columns=['index', 'Count / Hour'], **tab_options)
    # New rows: crafting, cooking, combustible
    craft_xp = {"Log": 5, "Oak Log": 10, "Willow Log": 15, "Maple Log": 30, "Yew Log": 45, "Elder Log": 100,
                "Raw Tentacle Meat": 150, "Rotten Driftwood": 5, "Sturdy Driftwood": 10,
                "Aqueous Grass": 1, "Water Weeds": 3, "River Vines": 8.7, "Violet Ribbons": 16.45, "White Reeds": 37.6,
                "Ancient Kelp": 61.5,
                "Adamantite Ore": 5.3, "Adamantite Bar": 40, "Runite Ore": 6.36, "Runite Bar": 70,
                "Stygian Ore": 8, "Stygian Bar": 150, "Copper Ore": 1}
    alt_heat = {"Fish Oil": 240}
    for (k, v) in pc.player.item_data.items():
        if "fish" in v.get("tags", []):
            crafting_xp = 48 * v.get("size", 0) / 20
            craft_xp[v["name"]] = crafting_xp
            alt_heat[v["name"]] = v.get("size", 0) / 20 * 240

    total_craft_xp = np.sum([item_series.get(k, 0) * v for (k, v) in craft_xp.items()])
    total_cooking_xp = 0
    total_combustible = 0
    for (k, v) in item_series.items():
        this_item = pc.player.get_item_by_name(k)
        total_cooking_xp += 5 * (this_item.get('difficulty', 0) + this_item.get('bonusDifficultyXP', 0)) * v
        total_combustible += (this_item.get('heat', 0) + alt_heat.get(k, 0)) * v
    total_zone_experience = action.zone_experience_rate(zone)
    second_df = pd.Series({'Experience': total_zone_experience,
                           'Crafting': total_craft_xp,
                           'Cooking': total_cooking_xp,
                           'Combustible': total_combustible})
    second_df = second_df[second_df.gt(0)].round(0)
    second_df.name = 'Count / Hour'
    second_table = second_df.hvplot.table(columns=['index', 'Count / Hour'], height=(len(second_df) + 1) * height_per_row)
    return pn.Column(the_plot, second_table, the_table)


interactive_plot = pn.bind(zone_summary, action_selector, zone_selector)
selection_column = pn.Column(action_selector, zone_selector)


def update(event):
    zone_selector.param.trigger('value')


pc.assign_callback(update)
stats_column = pn.Column(*(pc.level_widgets()))
equipment_column = pn.Column(*(pc.equipment_widgets()))
enchant_column = pn.Column(*(pc.enchant_widgets()))
selection_tabs = pn.Tabs(('Action', selection_column), ('Character', stats_column), ('Equipment', equipment_column),
                         ('Enchants', enchant_column))
main_tabs = pn.Tabs(('Zone Summary', interactive_plot))

template = pn.template.FastListTemplate(
    title='Idlescape',
    sidebar=selection_tabs,  # choices
    main=main_tabs,
    accent_base_color='#88d8b0',
    header_background='#88d8b0',
)

template.servable()


await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.runPythonAsync(`
    import json

    state.curdoc.apply_json_patch(json.loads('${msg.patch}'), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads("""${msg.location}""")
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()
