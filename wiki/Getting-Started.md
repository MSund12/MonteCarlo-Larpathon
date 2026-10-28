# Getting started

Clone or download the repository, open its folder, and use Python 3.10 or newer.

```powershell
python monte_carlo_demo.py
```

This opens the interactive menus. On Windows, the included launcher is another option:

```powershell
.\run_demo.ps1
```

- Basic pricing can run using Python's standard library.
- NumPy enables accelerated pricing, Greeks, and variance reduction.
- NumPy and Matplotlib are required for charts. Install the plotting dependencies with:

```powershell
python -m pip install -r requirements-visualization.txt
```

Use the same Python environment for installation and execution. The PowerShell launcher tries a bundled runtime when available and otherwise uses `python` from PATH.

## First repeatable run

```powershell
python monte_carlo_demo.py --engine terminal --product european --type call --simulations 50000 --seed 42 --report first_run.json
```

Read price together with standard error and the confidence interval. Compare the European estimate with the analytical benchmark; they need not match exactly.

After installing NumPy, add `--greeks` or `--variance-reduction both`. Add `--chart first_run.png` for an illustration. Use `python monte_carlo_demo.py --help` to inspect available flags. Use different output names when comparing runs.

Menus support exploration; command-line arguments support repeatable execution. The standalone application does not need other project Python modules, but optional third-party libraries still require installation.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
