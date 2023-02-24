import panel as pn
import json
from io import StringIO
from idlescape.dashboard import InteractiveCharacter

pn.extension('ace', 'jsoneditor')


class BalanceEditor:
    def __init__(self, character: InteractiveCharacter):
        self.character = character
        self.json_editor = None

    def display_editor(self, additional_callback=None):
        with open(self.character.location_file) as j:
            loc_data = json.load(j)

        # Hack to avoid json string '
        string_data = json.loads(json.dumps(loc_data).replace("'", "^^"))
        self.json_editor = pn.widgets.JSONEditor(value=string_data, mode='tree', width_policy='max', height=1000)

        def json_callback(event):
            # Unhack the string
            unstring_data = json.loads(json.dumps(self.json_editor.value).replace("^^", "'"))
            self.character.mining.set_location_data(unstring_data)
            self.character.foraging.set_location_data(unstring_data)
            self.character.fishing.set_location_data(unstring_data)
            if additional_callback is not None:
                additional_callback(event)

        self.json_editor.param.watch(json_callback, ['value'])
        return self.json_editor

    def save_json(self):
        sio = StringIO(json.dumps(self.json_editor.value))
        return sio
