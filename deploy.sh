#!/bin/bash
source venv/bin/activate
python setup.py bdist_wheel
url="/IdlePy/dist/idlescape-0.0.2-py3-none-any.whl"
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements $url hvplot
patch docs/zones/ZonePanel.js < nativefs.patch

panel convert AugmentPanel.py --to pyodide-worker --out docs/augment --requirements $url hvplot
