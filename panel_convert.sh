#!/bin/bash
panel convert ZonePanel.py --to pyodide-worker --out docs/zones --requirements "git+https://github.com/holychikenz/IdlePy#egg=idlescape" hvplot
