# variance_reduction.py — explanation

Source: [variance_reduction.py](../../variance_reduction.py)

## What is happening and why

- Calculate the known mean of a control that moves with the simulated payoff. European pricing uses discounted terminal stock with mean S0 × exp(−qT).
- Use a geometric-average Asian payoff as the arithmetic Asian control. Its lognormal mean and variance match equally spaced monitoring dates after time zero; the initial spot is excluded from the average.
- Use the matching vanilla European payoff as the barrier control. It shares the terminal payoff shape, while the barrier target also depends on survival.
- Fit beta as the centered payoff-control cross product divided by the centered control sum of squares. Return zero when the control has effectively no variation, avoiding unstable division.
- Fit on an independent pilot sample in advanced_pricing.py. Hold beta fixed during production so the reported observations do not also choose their own fitted adjustment.
- Merge batch central moments in Moments.update. Inputs are already discounted and, where selected, paired and adjusted, so summary applies no second discount.

## Definitions in the code

- [`lognormal_option_mean`](../../variance_reduction.py#L8)
- [`control_mean`](../../variance_reduction.py#L23)
- [`fit_coefficient`](../../variance_reduction.py#L44)
- [`Moments`](../../variance_reduction.py#L56)
- [`update`](../../variance_reduction.py#L61)
- [`summary`](../../variance_reduction.py#L73)

## Explanations moved out of the source

- **File purpose:** Analytical controls and estimator statistics, independent of UI and engines.
- **lognormal_option_mean:** Discounted call/put expectation for a lognormally distributed underlying.
- **control_mean:** Exact expectation of the discounted control under constant-parameter GBM.
- **fit_coefficient:** Fit beta on an independent pilot; never fit on reported pricing samples.
- **Source line 28 when extracted:** Discounted terminal stock, NOT the option's known Black-Scholes price.
- **Source line 37 when extracted:** The matching vanilla European payoff controls a barrier payoff.
- **Source line 49 when extracted:** A constant control, especially at sigma=0, contains no useful randomness.
- **Source line 74 when extracted:** Observations are already discounted, paired, and adjusted as applicable.

Related files: [explanation index](README.md).
