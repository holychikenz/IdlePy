#!/bin/bash
python setup.py bdist_wheel
url="/IdlePy/dist/idlescape-0.0.2-cp310-cp310-linux_x86_64.whl"
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements $url hvplot
