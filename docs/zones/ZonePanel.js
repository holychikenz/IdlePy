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
