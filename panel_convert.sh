#!/bin/bash
#url="https://github.com/holychikenz/IdlePy/blob/main/dist/idlescape-0.0.1-py3-none-any.whl"
url="/IdlePy/dist/idlescape-0.0.1-py3-none-any.whl"
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements $url hvplot
