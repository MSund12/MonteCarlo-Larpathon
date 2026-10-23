# greeks.py — explanation

Source: [greeks.py](../../greeks.py)

## What is happening and why

- Create modified copies of the market and contract with dataclasses.replace. This keeps the original input unchanged while defining the scenarios needed for sensitivity calculations.
- Calculate Delta using (V(S+h) − V(S−h))/(2h), and Gamma using (V(S+h) − 2V(S) + V(S−h))/h². The spot bump is relative to spot and is reduced near an upper barrier.
- Use central differences for Vega and Rho where possible. If a downward volatility bump would be negative, use a forward difference for Vega instead.
- Define Theta as −dV/dT. Use a maturity bump no larger than a quarter of the remaining maturity, so the downward scenario still has positive time to expiry.
- Return coefficient dictionaries rather than simulate here. The estimator applies those coefficients to observations sharing the same shocks, so covariance is retained in Greek standard errors.
- This file uses Vega and Rho per unit change and Theta per year. advanced_pricing.py converts their reported values and intervals to one percentage point and one calendar day.

## Definitions in the code

- [`scenarios`](../../greeks.py#L6)

## Explanations moved out of the source

- **File purpose:** Finite-difference scenarios. Contains no random draws or price mutations.
- **scenarios:** Return scenarios plus linear formulas applied to per-observation payoffs. Theta is -dV/dT with a fixed number of equally spaced monitoring dates. Vega/rho are per unit (1.00) volatility/rate; report scaling is separate.

Related files: [explanation index](README.md).
