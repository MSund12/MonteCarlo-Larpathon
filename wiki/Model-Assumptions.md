# Model assumptions and scope

- Stock scenarios follow geometric Brownian motion with constant risk-free rate, dividend yield, and volatility.
- Spot, strike, and maturity must be positive. Volatility may be zero but cannot be negative; numeric inputs must be finite.
- The project supports the contracts described above, not early exercise, stochastic volatility, jump processes, or continuously monitored barrier corrections.
- Asian averages and barrier checks follow the selected discrete monitoring schedule. Changing time steps changes that schedule and can change the contract value being estimated.
- Confidence intervals describe approximate sampling uncertainty under the chosen model. They exclude model error, finite-difference bias, and differences from alternative monitoring conventions.
- Small samples and rare payoffs can produce misleadingly small sample variance. No observed positive payoffs does not establish a true value of zero.
- Benchmark timings are historical measurements, not promised performance on every computer.

## Distinguishing uncertainty sources

| Source | What can address it |
|---|---|
| Sampling error | More independent observations or effective variance reduction |
| Greek finite-difference bias | Bump-size stability checks and appropriate derivative methods |
| Monitoring convention | Matching contractual observation dates |
| Model or input error | Reviewing assumptions, calibration, or supplied inputs |

Only sampling uncertainty appears in the reported intervals. More simulations cannot correct unsuitable assumptions or an incorrect monitoring schedule. The project provides transparent experiments for the supported contracts; market-data calibration and production suitability are separate considerations.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
