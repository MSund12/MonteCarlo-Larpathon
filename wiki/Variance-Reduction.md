# Variance reduction

Variance reduction estimates the same model value with less sampling noise. It changes how observations are combined.

## Methods

- **`none`:** no antithetic or control adjustment.
- **`antithetic`:** pair shocks `Z` and `−Z`, then average their payoffs. A pair counts as one independent observation; 50,000 physical paths yield 25,000 independent observations.
- **`control`:** adjust payoffs using a correlated quantity with a known expectation. European contracts use discounted terminal stock; Asian contracts use a matching geometric Asian payoff; barriers use a matching vanilla European payoff.
- **`both`:** combine antithetic pairing and control adjustment.

Control coefficients are fitted on an independent pilot sample, defaulting to 2,048 additional physical paths. Pilot paths are excluded from reported production means and intervals. Antithetic modes require an even production count of at least four; pilot counts must also be even when pairing is used.

```powershell
python monte_carlo_demo.py --engine path --product asian --time-steps 12 --variance-reduction both --greeks --report asian_greeks.json
```

These methods can improve precision, but improvement is not guaranteed for every input or pilot sample. Greek runs also require additional parameter-scenario evaluations.

## Control estimator

```text
Adjusted payoff = Y - beta * (X - known expectation of X)
beta = Cov(Y, X) / Var(X)
```

`Y` is the discounted target payoff; `X` is a correlated control. An independent pilot fits the coefficient, which is frozen for production. Constant controls receive coefficient zero.

| Target | Control | Known expected value |
|---|---|---|
| European | Discounted terminal stock | `S0 * exp(-q*T)` |
| Arithmetic Asian | Matching geometric Asian option payoff | Analytical value for the same future monitoring dates |
| Up-and-out barrier | Vanilla European payoff on the same path | Black-Scholes value |

The Asian control matches the target's strike, call/put direction, and dates. Its expectation is known even though geometric and arithmetic option values differ.

## Comparing precision and cost

For 50,000 antithetic production paths, uncertainty uses 25,000 independent pair averages. Counting both correlated halves as independent would misstate uncertainty. The default 2,048 pilot paths are additional work and excluded from the production estimate.

Reports compare standard errors before and after the control adjustment on the same production observations. That does not isolate the benefit of antithetics or include pilot runtime. Compare total cost and precision together.

Greek runs add parameter scenarios. Counts are per scenario; metadata includes `parameter_scenarios` and `total_path_evaluations`. Independent fitting avoids selecting coefficients on production data, but does not guarantee improvement for every sample or payoff. These methods require NumPy and retain the approximate 95% confidence level.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
