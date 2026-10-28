# Monte Carlo option pricing

## Project Wiki

The [project Wiki pages](wiki/Home.md) explain setup, pricing engines, inputs,
Greeks, variance reduction, charts, testing, troubleshooting, and model assumptions.
Use the [page index](wiki/_Sidebar.md) to browse all topics.

## Unified demo — start here

The main application is now **`monte_carlo_demo.py`**, a single runnable file
containing both engines, menus, Greeks, variance reduction, JSON reports, and
optional charts. It does not import any of the other project Python files.
The modular source files are preserved as a backup/reference; tests and this
documentation remain separate. NumPy/Matplotlib remain optional external
libraries as described below.

From PowerShell in this folder, run:

```powershell
.\run_demo.ps1
```

Or use your Python 3.10+ interpreter:

```powershell
python monte_carlo_demo.py
```

The interactive menus select the engine, product, call/put, market data, contract
terms, simulation count, seed, calculation backend, and optional saved chart.
Press Enter to accept a displayed default. Terminal pricing supports European
options. Path pricing also supports arithmetic Asian and up-and-out barrier
options. Both call and put payoffs are available for every supported product.
Here “terminal” means sampling the price at expiry; both engines run in the same
command-line application.

For repeatable commands without the menus:

```powershell
.\run_demo.ps1 --engine terminal --type call --simulations 100000
.\run_demo.ps1 --engine path --product asian --type put --time-steps 252 --chart asian_put.png --report asian_put.json
.\run_demo.ps1 --engine path --product up_and_out_barrier --type call --barrier 130 --chart barrier_call.png
python monte_carlo_demo.py --help
```

Use `--show` to open a chart window. JSON reports save all inputs, the selected
backend, estimated price, standard error, confidence interval, benchmark when
available, and pricing time. The PowerShell launcher uses the available bundled
Python runtime on this machine, adds the project-local plotting dependencies
when present, and otherwise falls back to `python`. Relative output paths are
resolved against the folder from which you launch the command.

Charts use the same contract and market inputs, with a **separate diagnostic
sample** (default 5,000 scenarios and seed equal to pricing seed plus one).
Their convergence panel marks the full pricing run's estimate for comparison.
Path charts retain up to 500 paths for percentile bands and show up to 60;
terminal charts show a payoff curve because that engine does not simulate paths.
Use `--chart-simulations` to adjust the diagnostic sample size. The diagnostic
sample currently uses the standard-library generator regardless of pricing
backend. It is not the full set of samples underlying the reported estimate.

`monte_carlo_demo.py` is the main application entry point and `run_demo.ps1` now
launches it. `option_pricing.py` and the original engine files remain importable
and runnable as a modular backup. `visualize_outcomes.py` retains its modular
standalone command. Historical module names in the architecture notes below
refer to that preserved implementation; the same functions now live in sections
inside `monte_carlo_demo.py`.

## Open the project in VS Code

Use **File > Open Folder** and select:

```text
C:\Users\alexm\OneDrive\Documents\MonteCarlo
```

Or run:

```powershell
code "C:\Users\alexm\OneDrive\Documents\MonteCarlo"
```

This opens the same files edited by this chat; no account linking or file-sync
service is required to see saved changes. Open `monte_carlo_demo.py` in the
Explorer. Avoid unsaved edits to the same file in two tools at the same time.

In VS Code's integrated PowerShell terminal, run `.\run_demo.ps1`. Alternatively,
use **Terminal > Run Task > Monte Carlo: run demo**. With Microsoft's Python and
Python Debugger extensions installed, choose **Run and Debug > Monte Carlo:
interactive demo** and press F5. An Asian/Greeks debug configuration is included.
The workspace recommends those extensions and the optional OpenAI Codex
extension, but does not install them automatically.

The workspace's default interpreter setting points at the bundled Python already
available on this machine. If VS Code has remembered a different interpreter,
use **Python: Select Interpreter** to choose the bundled executable or a Python
3.10+ environment with the optional libraries installed. The included launch
configurations expose the project-local `.visualization-deps` folder for charts.

The optional [Codex IDE extension](https://developers.openai.com/codex/ide) lets
you work with Codex inside VS Code. Opening the same project folder is sufficient
for sharing source files; installing the extension is a separate convenience.

### Editing and rebuilding

For ordinary use, edit `monte_carlo_demo.py` directly. It is readable Python with
named sections, not an encoded bundle. `build_single_file.py` is an optional
development tool that reconstructs it from the modular backup. **Rebuilding
overwrites direct edits to the merged file**, so only rebuild intentionally.

`python -m unittest -v` checks both versions and compares seeded numerical
results, Greek estimates, pilot coefficients, and confidence intervals. Runtime
measurements are excluded from equality checks. A separate test runs a copy of
the merged file in isolation without the original project modules.

Python 3.10 or newer. Keep `pricing_common.py` and `pricing_kernels.py` beside both engine scripts.
The pricing engines work with only Python's standard library. They automatically
use NumPy acceleration when it is installed.

```powershell
python "monte carlos pricing engine_terminal engine.py"
python "monte carlo option pricing engine_path based engine.py"
python -m unittest -v
```

Edit each engine's `main()` market and contract settings to price another option.
The terminal engine samples expiry directly for European calls and puts and
includes an analytical Black–Scholes benchmark. The path engine supports European,
arithmetic Asian, and discretely monitored up-and-out options. Pricing streams
simulations; `simulate_price_paths()` explicitly collects paths for plotting.
European pricing samples expiry directly, regardless of `time_steps`.

## Greeks and variance reduction

These features are optional and require NumPy. The original calculation remains
the default (`--variance-reduction none`, no `--greeks`). The interactive menus
offer them when the selected backend is automatic or NumPy.

```powershell
.\run_demo.ps1 --engine terminal --simulations 50000 --variance-reduction both --greeks --report european_greeks.json
.\run_demo.ps1 --engine path --product asian --time-steps 252 --simulations 50000 --variance-reduction both --greeks --report asian_greeks.json
.\run_demo.ps1 --engine path --product up_and_out_barrier --barrier 130 --variance-reduction antithetic --greeks
```

Available methods: `none`, `antithetic`, `control`, and `both`.

### Where the imports belong

- `option_pricing.py` imports `advanced_pricing.estimate` only when an advanced
  feature is requested. It handles configuration, selection, and report display.
- `advanced_pricing.py` imports `greeks.scenarios` and the control/statistics
  functions from `variance_reduction.py`. It owns shared random draws, independent
  pilot and production streams, payoff transformations, and uncertainty estimates.
- `greeks.py` builds bumped, copied market/contract inputs and per-observation
  finite-difference formulas. It never mutates the original inputs or draws random
  samples. Enabling Greeks leaves the base price sample unchanged within floating
  point rounding.
- `variance_reduction.py` holds exact control expectations, pilot coefficient
  fitting, and the moments of the final estimator observations.
- Both engine functions also accept `variance_reduction="both"` and
  `pilot_simulations=2048`. The shared kernel delegates only that optional request
  to the advanced estimator. For Greek estimates and full sample accounting, use
  the unified application's `run_pricing(Configuration(..., greeks=True))` API.
- `visualize_outcomes.py` remains a consumer of the report. Its separate plain-MC
  diagnostic sample does not feed coefficients, Greeks, prices, or reported CIs.

### Mathematics and confidence intervals

All observations below are **already discounted**. For antithetics, each independent
observation is the average `(Y(Z) + Y(-Z)) / 2`. Standard error is computed across
these pair averages, never across the correlated individual paths.
`--simulations` remains the number of physical production paths; antithetic modes
require an even count of at least four. For example, 50,000 physical paths produce
25,000 independent observations.

Controls use `Y_adjusted = Y - beta * (X - E[X])`. The controls are:

| Product | Control | Known expectation |
|---|---|---|
| European | Discounted terminal stock | `S0 * exp(-q*T)` |
| Arithmetic Asian | Matching geometric Asian payoff | Exact lognormal formula for the same equally spaced future dates |
| Up-and-out barrier | Vanilla European payoff on the same path | Black-Scholes price |

The control coefficient `beta = Cov(Y,X)/Var(X)` is fitted using a separate pilot
stream, then frozen for production. With antithetics, fitting also uses pair
averages. `--pilot-simulations` defaults to 2,048 **additional physical paths**;
these samples do not enter the reported estimate or standard error. Constant
controls receive coefficient zero. Reduction is not guaranteed for every product
or pilot sample; reports show price standard errors before and after control
adjustment, for the same production observations. That comparison does not
measure the isolated benefit of antithetic sampling or include pilot runtime.

Greeks use common random numbers across base and bumped contracts. For example,
Delta is the sample mean of `(Y(S+h)-Y(S-h))/(2*h)`, and Gamma uses
`(Y(S+h)-2*Y(S)+Y(S-h))/h**2`. Their SEs are computed from these per-observation
differences; the code never adds the SEs of correlated prices. When control
variates are enabled, each Greek fits its own pilot coefficient against the
corresponding control finite difference, using its known expectation.

| Greek | Display unit | Default bump |
|---|---|---|
| Delta | Price change per $1 spot | 0.5% of spot |
| Gamma | Delta change per $1 spot | Same spot bump |
| Vega | Price change per 1 percentage point volatility | 0.001 absolute volatility |
| Rho | Price change per 1 percentage point interest rate | 0.0001 absolute rate |
| Theta | Price change per calendar day | 1/365 year |

Use `--spot-bump`, `--volatility-bump`, `--rate-bump`, and `--maturity-bump` to
check finite-difference stability. Spot bumps are constrained below the barrier.
Vega uses a forward difference when a central bump would make volatility negative.
Theta means `-dV/dT` with a fixed number of equally spaced monitoring dates;
changing maturity rescales those dates. It does not roll a fixed calendar schedule.

The confidence level remains approximately **95%**: `mean +/- 1.96*SE`, using
the number of independent production observations. Variance reduction changes
the estimator's spread, not the confidence level. Intervals exclude finite-bump
bias, model error, and monitoring assumptions. Small samples, rare knockouts or
payoffs, and discontinuous barrier Greeks can make normal intervals unreliable.
Gamma near payoff kinks and barrier Greeks need particular bump/sample-size
stability checks. Do not interpret zero sampled variance as proof of zero risk.

The tests check pair-based SEs, independent pilot fitting, Asian control formulas,
European analytical Greeks, unchanged base pricing when Greeks are enabled,
and repeated-seed price interval coverage. These are checks, not a guarantee
of exact coverage for all inputs.

Production/pilot path counts are per parameter scenario. A full Greek calculation
evaluates up to nine parameter scenarios per random realization; the JSON
metadata includes `parameter_scenarios` and `total_path_evaluations` so the added
work is visible. Batch size limits production working arrays; pilot fitting
temporarily retains pilot observations for each output.

Method references: [Columbia's variance reduction chapter](https://business.columbia.edu/sites/default/files-efs/pubfiles/4336/monte_carlo_methods_security_pricing.pdf)
and [finite-difference Greeks notes](https://www.columbia.edu/~mh2078/MonteCarlo/MCS_Greeks_MasterSlides.pdf).

## Calculation backends

Both `price_option_monte_carlo()` functions accept keyword-only options:

```python
result = price_option_monte_carlo(
    market, option, simulations=100_000,
    backend="auto",    # "numpy" requires NumPy; "python" forces the fallback
    batch_size=8192,    # working array size for the NumPy backend
)
```

Install NumPy alone with `python -m pip install numpy`, or install the plotting
requirements below. NumPy processes many paths at once, keeping only current
prices, running averages, and knockout flags. Working memory scales with batch
size rather than simulations times monitoring steps. The standard-library
fallback also avoids retaining price histories. Zero-volatility pricing evaluates
one deterministic scenario and returns zero sampling error.

Run `python benchmark_pricing.py` to compare backends on your machine. In the
development run (median of three runs, excluding NumPy import time), Asian pricing
with 10,000 paths and 252 dates fell from 1.45 s before optimization to 0.054 s
with NumPy; barrier pricing fell from 1.58 s to 0.057 s. These are measurements,
not guarantees for another machine or workload. Results are saved in
`benchmark_before.json` and `benchmark_after.json`.

## Visualize outcomes

```powershell
python -m pip install -r requirements-visualization.txt
python visualize_outcomes.py --show
python visualize_outcomes.py --product asian --output asian_outcomes.png
python visualize_outcomes.py --product up_and_out_barrier --barrier 130 --output barrier_outcomes.png
```

The optional plotting script imports:

```python
import numpy as np
import matplotlib.pyplot as plt
```

NumPy computes percentiles and handles arrays; Matplotlib draws paths, percentile
bands, histograms, and convergence charts. Use Plotly instead if you want browser
charts with zoom and hover (`python -m pip install plotly`, then
`import plotly.graph_objects as go`). Pandas is optional for tabular exports and
historical data; neither engine needs it.

The default chart uses 5,000 scenarios with 252 steps and plots 60 paths for readability.
Use the unified demo's menus or flags to change the market and contract inputs. These are separate
sample trajectories starting from a common spot, not a binomial branching tree.
For an actual two-branch-per-step tree, implement a binomial model separately.

## Interpretation and limits

- Scenarios use risk-neutral geometric Brownian motion with constant rates,
  volatility, and dividend yield. They are pricing scenarios, not forecasts.
- The path band is the pointwise 5th–95th percentile range of underlying prices.
  It is not a simultaneous path coverage band or an option-price confidence interval.
- The convergence band is an approximate normal 95% confidence interval for the
  Monte Carlo mean. Small samples and rare payoffs can make it unreliable; zero
  sampled positive payoffs does not prove an option has zero value.
- Barriers are checked at the initial spot and simulated monitoring dates only.
  Intrastep crossings are not detected. Asian averages exclude the initial spot.
  Changing steps changes these contracts' monitoring schedule.
- `time_steps` is the total over the entire maturity. For approximately daily
  monitoring over two years, use 504, not 252.
- Maturity must be positive. Up-and-out barriers must exceed the current spot;
  already knocked-out contracts are rejected by this example's API.
- A fixed seed, backend, batch size, NumPy version, and monitoring schedule make
  runs reproducible. Python and NumPy use different random streams, and NumPy
  path products assign draws differently when the batch size changes. The
  optimized European pricer also draws only expiry rather than a full path;
  its sample values therefore differ from the earlier path-based implementation.
  These changes preserve the model distribution, not identical sampled paths.
  Use `backend="python"` for the dependency-free random stream.
- A benchmark outside a 95% interval can
  occur through sampling alone; a single interval is not a correctness test.

## Code explanations

Detailed point-form explanations are kept outside the code. Start with the [source and explanation index](docs/code-notes/README.md). Each entry links the source file to its companion explanation.
