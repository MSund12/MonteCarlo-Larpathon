# monte_carlo_demo.py — explanation

Source: [monte_carlo_demo.py](../../monte_carlo_demo.py)

## What is happening and why

- Combine the modular implementation into one runnable file so the demo can be copied and run without the other project Python files. NumPy and Matplotlib remain external optional dependencies.
- Use the same validation, kernels, scenario formulas and estimator accounting as the modular version. The single-file tests compare seeded outputs between both implementations.
- Use separate terminal_ and path_ function names where the original engines overlap. load_engine selects those definitions through SimpleNamespace instead of loading another file.
- Start with main for menus or command-line arguments, then follow run_pricing to the selected estimator. The shared statistical pipeline is discounting, antithetic averaging if selected, Greek differences, pilot-fitted adjustment and moment accumulation.
- Use the linked modular companion documents for detailed reasons behind the statistical and plotting decisions. The symbol list below identifies the corresponding definitions inside this standalone copy.

## Definitions in the code

- [`validate_count`](../../monte_carlo_demo.py#L4)
- [`validate_market_contract`](../../monte_carlo_demo.py#L8)
- [`summarize_payoffs`](../../monte_carlo_demo.py#L21)
- [`summary_from_moments`](../../monte_carlo_demo.py#L34)
- [`lognormal_option_mean`](../../monte_carlo_demo.py#L47)
- [`control_mean`](../../monte_carlo_demo.py#L60)
- [`fit_coefficient`](../../monte_carlo_demo.py#L76)
- [`Moments`](../../monte_carlo_demo.py#L85)
- [`scenarios`](../../monte_carlo_demo.py#L107)
- [`_batches`](../../monte_carlo_demo.py#L149)
- [`estimate`](../../monte_carlo_demo.py#L197)
- [`price_kernel`](../../monte_carlo_demo.py#L267)
- [`_python_payoffs`](../../monte_carlo_demo.py#L293)
- [`_numpy_price`](../../monte_carlo_demo.py#L315)
- [`MarketData`](../../monte_carlo_demo.py#L356)
- [`EuropeanOption`](../../monte_carlo_demo.py#L363)
- [`PricingResult`](../../monte_carlo_demo.py#L369)
- [`terminal_validate_inputs`](../../monte_carlo_demo.py#L376)
- [`simulate_terminal_stock_prices`](../../monte_carlo_demo.py#L380)
- [`terminal_calculate_payoff`](../../monte_carlo_demo.py#L397)
- [`terminal_calculate_payoffs`](../../monte_carlo_demo.py#L405)
- [`terminal_price_option_monte_carlo`](../../monte_carlo_demo.py#L408)
- [`normal_cdf`](../../monte_carlo_demo.py#L412)
- [`black_scholes_price`](../../monte_carlo_demo.py#L415)
- [`terminal_print_pricing_summary`](../../monte_carlo_demo.py#L432)
- [`OptionContract`](../../monte_carlo_demo.py#L463)
- [`path_validate_inputs`](../../monte_carlo_demo.py#L470)
- [`iter_price_paths`](../../monte_carlo_demo.py#L485)
- [`simulate_price_paths`](../../monte_carlo_demo.py#L500)
- [`vanilla_payoff`](../../monte_carlo_demo.py#L503)
- [`european_payoff`](../../monte_carlo_demo.py#L508)
- [`asian_payoff`](../../monte_carlo_demo.py#L512)
- [`up_and_out_barrier_payoff`](../../monte_carlo_demo.py#L517)
- [`calculate_path_payoff`](../../monte_carlo_demo.py#L524)
- [`path_price_option_monte_carlo`](../../monte_carlo_demo.py#L534)
- [`path_print_pricing_summary`](../../monte_carlo_demo.py#L538)
- [`load_engine`](../../monte_carlo_demo.py#L568)
- [`Configuration`](../../monte_carlo_demo.py#L577)
- [`contracts`](../../monte_carlo_demo.py#L601)
- [`run_pricing`](../../monte_carlo_demo.py#L614)
- [`print_report`](../../monte_carlo_demo.py#L642)
- [`choose`](../../monte_carlo_demo.py#L674)
- [`number`](../../monte_carlo_demo.py#L684)
- [`interactive_configuration`](../../monte_carlo_demo.py#L696)
- [`parser`](../../monte_carlo_demo.py#L726)
- [`main`](../../monte_carlo_demo.py#L753)
- [`render_report`](../../monte_carlo_demo.py#L779)
- [`update`](../../monte_carlo_demo.py#L90)
- [`summary`](../../monte_carlo_demo.py#L102)

## Explanations moved out of the source

- **File purpose:** Standalone Monte Carlo option-pricing demo (Python 3.10+). Run: python monte_carlo_demo.py Contains both engines, Greeks, antithetic/control variates, menus, JSON export, and optional charts. No other project Python file is needed at runtime. NumPy is optional for basic pricing and required for advanced estimators. Matplotlib and NumPy are required for charts. Statistical pipeline: shared draws -> discounted payoffs -> pair averages -> Greek differences -> independent-pilot control adjustment -> sampling intervals. Antithetic pairs count as single observations. Pilot samples are excluded. Intervals exclude model error and finite-difference bias. Diagnostic charts use a separate plain-Monte-Carlo sample, clearly identified in the figure. Consolidated from the modular backup by build_single_file.py. Edit this file directly for normal use; rebuilding explicitly replaces this file.
- **summarize_payoffs:** Welford sample variance; O(1) storage and an approximate normal 95% CI.
- **summary_from_moments:** Convert sample central moments to a discounted estimate and normal CI.
- **lognormal_option_mean:** Discounted call/put expectation for a lognormally distributed underlying.
- **control_mean:** Exact expectation of the discounted control under constant-parameter GBM.
- **fit_coefficient:** Fit beta on an independent pilot; never fit on reported pricing samples.
- **scenarios:** Return scenarios plus linear formulas applied to per-observation payoffs. Theta is -dV/dT with a fixed number of equally spaced monitoring dates. Vega/rho are per unit (1.00) volatility/rate; report scaling is separate.
- **estimate:** Return pricing, Greek intervals, and explicit independent-sample accounting. `simulations` always means physical production paths. Antithetic modes require an even count; their independent sample count is simulations // 2. Pilot simulations are ADDITIONAL physical paths, excluded from reported estimates.
- **price_kernel:** Inputs other than backend/batch_size are validated by the public engines. NumPy uses its own random generator. Reproducibility requires a fixed seed, backend, batch size, and monitoring schedule.
- **OptionContract:** product_type choices: "european" "asian" "up_and_out_barrier" option_type choices: "call" "put" barrier_price is only needed for up-and-out barrier options.
- **iter_price_paths:** Simulate many possible stock-price paths. Each path looks like: [S0, S1, S2, ..., ST] Example with 4 time steps: [100.00, 103.20, 98.50, 101.40, 107.80] Geometric Brownian Motion formula: S(t + dt) = S(t) * exp( (r - q - 0.5 * sigma^2) * dt + sigma * sqrt(dt) * Z )
- **simulate_price_paths:** Collect paths for visualization; pricing itself streams one path at a time.
- **vanilla_payoff:** Standard European call/put payoff.
- **european_payoff:** European options only use the final stock price.
- **asian_payoff:** Arithmetic-average Asian option. The initial stock price is excluded from the average. Only monitored future prices are included.
- **up_and_out_barrier_payoff:** If the stock price ever reaches or exceeds the barrier, the option becomes worthless ("knocked out"). This is discrete monitoring: the barrier is checked at each simulated time step.
- **calculate_path_payoff:** Send each path to the correct payoff rule.
- **path_price_option_monte_carlo:** Price supported products with bounded memory and optional NumPy acceleration. 252 time steps represents approximately one trading year of daily monitoring.
- **load_engine:** Select functions already in this file; never import other project files.
- **render_report:** Plot an explicitly separate diagnostic sample using the selected contract.
- **Source line 22 when extracted:** VALIDATION AND STREAMING STATISTICS
- **Source line 72 when extracted:** CONTROL VARIATES AND ESTIMATOR MOMENTS
- **Source line 141 when extracted:** GREEK SCENARIOS
- **Source line 195 when extracted:** ADVANCED ESTIMATOR
- **Source line 324 when extracted:** BASIC MONTE CARLO KERNELS
- **Source line 422 when extracted:** SHARED MODELS AND TERMINAL ENGINE
- **Source line 533 when extracted:** PATH ENGINE
- **Source line 696 when extracted:** CONFIGURATION, MENUS, AND REPORTING
- **Source line 922 when extracted:** OPTIONAL VISUALIZATION

Related files: [explanation index](README.md).

Modular explanations: [input validation and statistics](pricing_common.py.md), [basic kernels](pricing_kernels.py.md), [Greek scenarios](greeks.py.md), [controls](variance_reduction.py.md), [advanced estimator](advanced_pricing.py.md), [menus and reports](option_pricing.py.md), [charts](visualize_outcomes.py.md).
