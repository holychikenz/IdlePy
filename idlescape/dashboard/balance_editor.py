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

        self.json_editor = pn.widgets.JSONEditor(value=loc_data, mode='tree', width_policy='max', height=1000)

        def json_callback(event):
            self.character.mining.set_location_data(event.new)
            self.character.foraging.set_location_data(event.new)
            self.character.fishing.set_location_data(event.new)
            if additional_callback is not None:
                additional_callback(event)

        self.json_editor.param.watch(json_callback, ['value'])
        return self.json_editor

    def save_json(self):
        sio = StringIO(json.dumps(self.json_editor.value))
        return sio
