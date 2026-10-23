# pricing_kernels.py — explanation

Source: [pricing_kernels.py](../../pricing_kernels.py)

## What is happening and why

- Use one exact GBM step for European payoffs because only the expiry price matters. Extra monitoring dates would add work without improving this payoff under constant model parameters.
- For Asian payoffs, keep a running sum of monitored prices. For barrier payoffs, keep an alive flag. These states avoid storing a full path for every pricing scenario.
- Use bounded NumPy batches to process several scenarios at once. Merge central moments between batches so the price and uncertainty use every scenario without retaining all payoffs.
- Keep a standard-library backend so basic pricing can run without NumPy. Different backends use different random generators; the same seed does not promise matching draws across them.
- At zero volatility, evaluate one deterministic payoff and report zero sampling variance. The requested simulation count is still included in the result.
- Continue drawing shocks after a barrier knockout in the Python backend. This preserves the random stream used by later seeded paths.

## Definitions in the code

- [`price`](../../pricing_kernels.py#L8)
- [`_python_payoffs`](../../pricing_kernels.py#L45)
- [`_numpy_price`](../../pricing_kernels.py#L70)

## Explanations moved out of the source

- **File purpose:** Memory-bounded Monte Carlo kernels with an optional NumPy fast path.
- **price:** Inputs other than backend/batch_size are validated by the public engines. NumPy uses its own random generator. Reproducibility requires a fixed seed, backend, batch size, and monitoring schedule.
- **Source line 34 when extracted:** All scenarios are identical at zero volatility. Avoid simulating them.
- **Source line 49 when extracted:** European payoffs depend only on expiry; intermediate draws add no accuracy.
- **Source line 65 when extracted:** Consume the full path's draws to preserve seeded path comparability.
- **Source line 98 when extracted:** Merge batch central moments without subtracting large raw squares.

Related files: [explanation index](README.md).
