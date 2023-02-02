#!/bin/bash
python setup.py bdist_wheel
url="/IdlePy/dist/idlescape-0.0.2-py3-none-any.whl"
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements $url hvplot
