# Charts and reports

## Numerical results

- **Price:** estimated present value of the option payoff under the selected model and inputs.
- **Standard error:** estimated sampling uncertainty in the Monte Carlo mean. It is not the spread of individual stock prices or individual payoffs.
- **95% confidence interval:** approximately `price ± 1.96 × standard error`. Under repeated sampling, this procedure aims for roughly 95% coverage of the model value when its approximation is adequate.
- **Black–Scholes benchmark:** an analytical comparison for European options under the same constant-parameter model. It is not an arithmetic Asian or barrier benchmark.
- **Elapsed time:** measured pricing runtime for that execution; performance varies by machine and configuration.
- **JSON report:** saves configuration and results, plus estimator and Greek details when requested.

More independent observations generally reduce sampling error. They do not fix incorrect inputs, model assumptions, finite-difference bias, or a coarse monitoring schedule. A single benchmark outside an interval does not establish that the implementation is wrong.

## Diagnostic charts

Most charts contain four panels:

| Panel | How to read it |
|---|---|
| Top left: paths or payoff curve | Path charts show sample trajectories, median prices, the pointwise 5th–95th percentile band, strike, and barrier where applicable. Terminal charts show a payoff curve instead. |
| Top right: terminal-price histogram | Shows how many scenarios finished in each stock-price range. |
| Bottom left: discounted-payoff histogram | Shows the distribution of present-value payoffs, including zero-payoff outcomes. |
| Bottom right: convergence | Shows how the diagnostic estimate changes as more diagnostic scenarios are included, with an approximate sampling interval. |

- The stock-path band describes the range of simulated stock prices at each date. It is not an option-price confidence interval or a band guaranteed to contain an entire path.
- Current report charts use a separate plain-Monte-Carlo diagnostic sample, normally 5,000 scenarios with pricing seed plus one.
- Path charts retain up to 500 paths for the band and display up to 60. Their histograms and convergence calculations use all diagnostic scenarios.
- The orange dashed line marks the full pricing run's estimate. Diagnostic estimates can differ because the samples are separate.
- Diagnostic confidence bands do not represent the enhanced estimator's uncertainty when variance reduction or Greeks are enabled.

| Included image | What it demonstrates |
|---|---|
| `outcomes.png` | Earlier European-call illustration: paths, expiry prices, discounted payoffs, and convergence. Its labels reflect the earlier plotting format. |
| `terminal_put_demo.png` | European put priced using the terminal engine, with its payoff curve. |
| `greeks_asian_demo.png` | Arithmetic Asian-call diagnostic chart. The filename identifies a run with Greeks; the Greek estimates themselves are in the JSON report. |
| `barrier_call_demo.png` | Up-and-out barrier call with a visible knockout threshold. |
| `single_file_demo.png` | Asian-call example with only 500 diagnostic scenarios, illustrating greater sampling uncertainty. |

These images are saved examples. Their values depend on the inputs and sampling configuration used to generate them.

## Comparing saved outputs

Check configuration before comparing reports: product, call/put, maturity, dates, backend, seed, and estimator settings all matter. Advanced runs add estimator and Greek details. Keep reports beside their charts to distinguish full pricing estimates from diagnostic samples.

A narrow interval does not mean payoffs are tightly clustered or that a market quote must be nearby. Coverage describes the statistical procedure under repeated sampling, not a guarantee for one run.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
