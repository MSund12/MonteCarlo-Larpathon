# Testing and code guide

| File or group | Purpose |
|---|---|
| `monte_carlo_demo.py` | Complete standalone application; recommended starting point. |
| `run_demo.ps1` | Windows launcher for the standalone application. |
| `option_pricing.py` | Modular configuration, menus, CLI, and reporting. |
| Original terminal and path engine scripts | Contract models, public engine functions, and simulation/payoff helpers. |
| `pricing_kernels.py` | Basic pricing calculations and backend selection. |
| `pricing_common.py` | Shared validation and statistics. |
| `advanced_pricing.py` | Enhanced estimators, shared draws, and uncertainty accounting. |
| `greeks.py` | Bumped parameter scenarios and finite-difference formulas. |
| `variance_reduction.py` | Analytical controls, coefficient fitting, and moment accumulation. |
| `visualize_outcomes.py` | Modular diagnostic plotting. |
| `build_single_file.py` | Reconstructs the standalone application from modular sources. |
| `test_*.py` | Automated checks of pricing, estimator accounting, CLI behavior, and standalone/modular agreement. |
| `benchmark_pricing.py` and benchmark JSON files | Timing comparison tool and saved historical measurements. |
| Other `.json` and `.png` files | Saved example reports and charts. |
| `docs/code-notes/README.md` | Index linking source files to their detailed point-form explanations. |

The standalone file includes its own copies of the implementation; it does not import the other project Python files. Rebuilding overwrites it. For development intended to survive regeneration, change the modular sources, rebuild intentionally, and run the tests. Direct standalone edits do not automatically update the modular sources.

## Validation workflow

```powershell
python -m unittest discover -v
```

Tests cover analytical European prices and Greeks, streaming payoffs, batch statistics, independent pilot fitting, pair-based uncertainty, reports, and standalone/modular agreement. An isolation test runs the standalone file without modular sources.

Review skipped tests: a successful run without NumPy does not exercise every advanced estimator. Repeated-seed coverage checks support the tested cases rather than guaranteeing all cases. Runtime is excluded from numerical equality checks.

For changes that should survive regeneration, edit modular sources, intentionally run `python build_single_file.py`, and run the tests. Rebuilding replaces direct standalone edits. Use the main repository's `docs/code-notes/README.md` for source explanations and `python benchmark_pricing.py` for backend timing comparisons on consistent workloads.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
