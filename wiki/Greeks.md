# Greeks: sensitivity to inputs

Greeks estimate how the option price responds to small input changes:

| Greek | Reported interpretation |
|---|---|
| Delta | Price change per $1 increase in spot, locally. |
| Gamma | Change in Delta per $1 increase in spot, locally. |
| Vega | Price change per one percentage point increase in annual volatility, locally. |
| Rho | Price change per one percentage point increase in the annual interest rate, locally. |
| Theta | Price change per calendar day under the implemented time-decay convention. |

- Greeks use finite differences: rerun related contracts with small parameter bumps and compare their payoffs.
- Related scenarios share random shocks to reduce noise in their differences. Standard errors retain that dependence.
- Theta uses `−dV/dT`, holding the number of monitoring dates fixed and rescaling their spacing as maturity changes.
- Bump sizes affect estimates. Barrier discontinuities and Gamma near payoff kinks require particular care when checking stability.

## Calculation and units

For discounted payoff `Y` and absolute spot bump `h`, each random realization supplies:

```text
Delta = (Y(S+h) - Y(S-h)) / (2h)
Gamma = (Y(S+h) - 2Y(S) + Y(S-h)) / h^2
```

The program averages these observations and estimates uncertainty from their variation. Related scenarios share shocks, so their prices are correlated. Adding separate price standard errors would discard this dependence. Enabling Greeks preserves the base price sample up to floating-point rounding.

| Flag | Default and behavior |
|---|---|
| `--spot-bump` | 0.005 of spot; reduced if needed to keep the upper bumped spot below the barrier |
| `--volatility-bump` | 0.001 absolute volatility; forward difference if the downward bump would be negative |
| `--rate-bump` | 0.0001 absolute rate |
| `--maturity-bump` | 1/365 year, capped at one quarter of maturity |

Vega and Rho are reported per percentage point and Theta per calendar day. Bump sizes differ from display units. A Vega of 0.20 means about 0.20 additional option value for volatility moving from 20% to 21%, locally with other inputs fixed.

## Run and assess

```powershell
python monte_carlo_demo.py --engine path --product asian --time-steps 12 --greeks --report asian_sensitivities.json
```

Read each estimate with its own standard error and interval. Vary bumps and sample size to assess stability. Small bumps can amplify noise; large bumps measure a less local response. Gamma near payoff kinks and discontinuous barrier sensitivities require particular care.

Theta rescales the same number of dates with maturity rather than rolling a fixed calendar forward. Intervals exclude finite-difference bias. When controls are enabled, each Greek has its own pilot-fitted coefficient.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
