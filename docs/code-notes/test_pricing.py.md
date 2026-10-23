# test_pricing.py — explanation

Source: [test_pricing.py](../../test_pricing.py)

## What is happening and why

- Build explicit seeded paths and calculate their discounted payoffs independently. Compare their mean and sample standard error with the streaming Python kernel for Asian and barrier calls and puts.
- Reconstruct NumPy batches of sizes 128, 128 and 45. This checks that 301 scenarios are all included and that merging a partial final batch preserves the mean and standard error.
- Check European results with one and 252 requested time steps. Equality confirms the kernel avoids unnecessary intermediate draws for expiry-only payoffs.
- Check known Black–Scholes call and put values and put-call parity. Compare Monte Carlo prices with analytical values using a tolerance of four reported standard errors.
- Check zero volatility separately: the deterministic price must match the benchmark and sampling standard error must be zero.
- Use hand-built paths to check that Asian averaging excludes the initial spot, equality with the barrier knocks out, and surviving barrier paths retain the vanilla payoff.
- Reject nonfinite or negative volatility, invalid simulation counts, invalid backends and invalid barriers so these inputs cannot silently produce misleading estimates.

## Definitions in the code

- [`load`](../../test_pricing.py#L11)
- [`PricingTests`](../../test_pricing.py#L23)
- [`test_python_streaming_matches_explicit_paths`](../../test_pricing.py#L24)
- [`test_numpy_batch_moments_and_partial_batch`](../../test_pricing.py#L36)
- [`test_european_ignores_unneeded_time_steps`](../../test_pricing.py#L62)
- [`test_backend_validation`](../../test_pricing.py#L68)
- [`test_analytical_prices_and_parity`](../../test_pricing.py#L75)
- [`test_mc_against_analytical_with_dividends`](../../test_pricing.py#L83)
- [`test_zero_volatility`](../../test_pricing.py#L93)
- [`test_path_payoffs`](../../test_pricing.py#L101)
- [`test_validation`](../../test_pricing.py#L108)

## Explanations moved out of the source

- **File purpose:** Regression checks: python -m unittest -v
- **Source line 39 when extracted:** Reconstruct sampled paths independently to verify running averages,
- **Source line 40 when extracted:** monitoring, and statistics across a final incomplete batch.

Related files: [explanation index](README.md).
