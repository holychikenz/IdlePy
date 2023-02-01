#!/bin/bash
#panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements "git+https://github.com/holychikenz/IdlePy#egg=idlescape" hvplot
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements "https://github.com/holychikenz/IdlePy/dist/idlescape-0.0.1-py3-none-any.whl" hvplot
#panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements requirements.txt
