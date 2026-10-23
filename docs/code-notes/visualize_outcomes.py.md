# visualize_outcomes.py — explanation

Source: [visualize_outcomes.py](../../visualize_outcomes.py)

## What is happening and why

- Generate a separate diagnostic sample with pricing seed plus one. The charts illustrate the selected contract; they do not reuse every observation from the pricing estimate.
- Retain up to 500 paths for percentile bands and display up to 60. Use all diagnostic scenarios for terminal-price and discounted-payoff histograms.
- Show a payoff curve for the terminal engine because it does not generate intermediate stock-price paths.
- Calculate running diagnostic means and approximate normal sampling intervals from discounted payoffs. Skip the earliest unstable intervals, while retaining support for very small samples.
- Draw the full pricing estimate as a separate reference line. Diagnostic samples use plain Monte Carlo, so their interval is not the variance-reduced estimator’s interval.
- Select the Agg backend when no window is requested, and close the figure in finally. This supports saving charts without a display and releases plotting resources.

## Definitions in the code

- [`render_report`](../../visualize_outcomes.py#L6)
- [`main`](../../visualize_outcomes.py#L91)

## Explanations moved out of the source

- **File purpose:** Charts shared by the unified demo; the legacy plotting command remains usable.
- **render_report:** Plot an explicitly separate diagnostic sample using the selected contract.
- **Source line 20 when extracted:** A distinct seed prevents mistaking these bounded diagnostic samples for
- **Source line 21 when extracted:** the full pricing run. The report's price is displayed as a reference line.
- **Source line 28 when extracted:** Keep only a bounded path sample for the first panel. Histogram and
- **Source line 29 when extracted:** convergence data use all diagnostic scenarios, not only displayed paths.
- **Source line 67 when extracted:** Skip unstable earliest intervals while still supporting tiny samples.

Related files: [explanation index](README.md).
