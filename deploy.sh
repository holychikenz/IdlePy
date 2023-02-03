#!/bin/bash
python setup.py bdist_wheel
#pyodide build
#url="/IdlePy/dist/idlescape-0.0.2-cp310-cp310-emscripten_3_1_27_wasm32.whl"
url="/IdlePy/dist/idlescape-0.0.2-py3-none-any.whl"
panel convert ZonePanel.py --to pyscript --out docs/zones --requirements $url hvplot diskcache
