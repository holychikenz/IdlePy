# IdlePy

---
Python implementation of gathering actions for Idlescape, served in wasm using Pyodide / Panel at  
[https://holychikenz.github.io/IdlePy](holychikenz.github.io/IdlePy)

---
##  Local server
The local implementation includes optimization using Numba to speed up calculations, running several times
faster than the pure python implementation. To serve locally, run with Panel
```bash
pip install panel
panel serve ZonePanel.py
```

---
## To-do
- [x] Fishing bonus frequency
- [ ] Summary table
  - [ ] Crafting experience (link to specific recipe)
  - [ ] Cooking experience
  - [ ] Farming time / experience
  - [ ] Enchanting experience ?
  - [ ] Essence
  - [ ] Vendor
- [ ] Prospector / root-digging
- [ ] Archaeology
- [ ] All zones together table / tab
