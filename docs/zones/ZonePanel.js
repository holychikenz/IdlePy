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
  const dirHandle = await showDirectoryPicker();
  if ((await dirHandle.queryPermission({mode: "readwrite" })) !== "granted") {
    if (
      (await dirHandle.requestPermission({ mode: "readwrite" })) !== "granted"
    ) {
      throw Error("Unable to read and write directory");
    }
  }
  const nativefs = await pyodide.mountNativeFS("/idlescape", dirHandle);
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/0.14.3/dist/wheels/bokeh-2.4.3-py3-none-any.whl', 'https://cdn.holoviz.org/panel/0.14.3/dist/wheels/panel-0.14.3-py3-none-any.whl', 'pyodide-http==0.1.0', '/IdlePy/dist/idlescape-0.0.2-py3-none-any.whl', 'hvplot', 'diskcache', 'sqlite3']
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
import hvplot.pandas
import json
from idlescape.dashboard import InteractiveCharacter

html = pn.pane.HTML('')
pn.config.throttled = True
import os
print('Hello idle world', os.listdir('/idlescape'))

pc = InteractiveCharacter()

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
