# pricing_common.py — explanation

Source: [pricing_common.py](../../pricing_common.py)

## What is happening and why

- Check market inputs before simulation. Spot, strike and maturity must be positive; volatility can be zero. Rates and dividend yields can be negative, but all numeric inputs must be finite.
- Reject Boolean values explicitly. Python treats bool as a subclass of int, which would otherwise allow True to pass as a simulation count or market input.
- Use Welford updates to keep the count, mean and sum of squared deviations without storing every payoff. This also avoids subtracting two large raw sums when calculating variance.
- Calculate standard error as discount × sqrt(M2 / ((n − 1) × n)). The interval is price ± 1.96 × standard error; it describes approximate sampling uncertainty under the model.

## Definitions in the code

- [`validate_count`](../../pricing_common.py#L5)
- [`validate_market_contract`](../../pricing_common.py#L10)
- [`summarize_payoffs`](../../pricing_common.py#L31)
- [`summary_from_moments`](../../pricing_common.py#L46)

## Explanations moved out of the source

- **File purpose:** Shared validation and streaming statistics for the two pricing engines.
- **summarize_payoffs:** Welford sample variance; O(1) storage and an approximate normal 95% CI.
- **summary_from_moments:** Convert sample central moments to a discounted estimate and normal CI.

Related files: [explanation index](README.md).
