# monte carlos pricing engine_terminal engine.py — explanation

Source: [monte carlos pricing engine_terminal engine.py](../../monte%20carlos%20pricing%20engine_terminal%20engine.py)

## What is happening and why

- Use dataclasses for market inputs, the European contract and the result. Rates, volatility and dividend yield are annual decimal values; maturity is measured in years.
- Sample expiry prices with S_T = S0 × exp((r − q − sigma²/2)T + sigma sqrt(T)Z). This is the exact terminal distribution for constant-parameter risk-neutral GBM.
- Calculate call payoffs as max(S_T − K, 0) and put payoffs as max(K − S_T, 0). Discount their expected value using exp(−rT).
- Keep list-returning simulation helpers for inspection and charts. Route the public pricing call through the shared kernel for bounded-memory pricing.
- Provide a Black–Scholes benchmark for European calls and puts, including a zero-volatility case. Compare estimates against that benchmark to inspect sampling accuracy.

## Definitions in the code

- [`MarketData`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L10)
- [`EuropeanOption`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L20)
- [`PricingResult`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L30)
- [`validate_inputs`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L42)
- [`simulate_terminal_stock_prices`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L53)
- [`calculate_payoff`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L95)
- [`calculate_payoffs`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L113)
- [`price_option_monte_carlo`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L127)
- [`normal_cdf`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L158)
- [`black_scholes_price`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L164)
- [`print_pricing_summary`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L200)
- [`main`](../../monte%20carlos%20pricing%20engine_terminal%20engine.py#L249)

## Explanations moved out of the source

- **Source line 7 when extracted:** 1. DATA MODELS
- **Source line 12 when extracted:** Information about the market and underlying stock.
- **Source line 14 when extracted:** Current stock price: S0
- **Source line 15 when extracted:** Risk-free interest rate: r
- **Source line 16 when extracted:** Annual Volatility of the stock: sigma
- **Source line 17 when extracted:** Dividend yield of the stock
- **Source line 22 when extracted:** European option contract.
- **Source line 23 when extracted:** option_type must be either ''call' or 'put'.
- **Source line 25 when extracted:** Strike price: K
- **Source line 26 when extracted:** Time to expiry
- **Source line 27 when extracted:** 'call' or 'put'
- **Source line 32 when extracted:** Result returned by the Monte Carlo pricing engine.
- **Source line 34 when extracted:** Estimated option price
- **Source line 35 when extracted:** Standard error of the estimate
- **Source line 36 when extracted:** Lower bound of the 95% confidence interval
- **Source line 37 when extracted:** Upper bound of the 95% confidence interval
- **Source line 38 when extracted:** Number of Monte Carlo simulations performed
- **Source line 40 when extracted:** 2. VALIDATION
- **Source line 51 when extracted:** 3. PRICE SIMULATION
- **Source line 60 when extracted:** Generate simulated stock prices at expiry using
- **Source line 61 when extracted:** Geometric Brownian Motion under the risk-neutral measure.
- **Source line 63 when extracted:** Formula:
- **Source line 64 when extracted:** S_T = S_0 * exp((r - q - 0.5 * sigma^2) * T + sigma * sqrt(T) * Z)
- **Source line 66 when extracted:** Z is a random draw from the standard normal distribution.
- **Source line 93 when extracted:** 4. PAYOFF CALCULATION
- **Source line 100 when extracted:** Calculate one option payoff at expiry.
- **Source line 102 when extracted:** Call payoff = max(ST - K, 0)
- **Source line 103 when extracted:** Put payoff = max(K - ST, 0)
- **Source line 118 when extracted:** Apply the payoff formula across all simulations.
- **Source line 125 when extracted:** 5. MONTE CARLO PRICER
- **Source line 139 when extracted:** Main pricing function
- **Source line 141 when extracted:** Steps.
- **Source line 142 when extracted:** 1. Simulate terminal stock prices.
- **Source line 143 when extracted:** 2. Calculate each option payoff.
- **Source line 144 when extracted:** 3. Average the payoffs.
- **Source line 145 when extracted:** 4. Discount the average to present value.
- **Source line 146 when extracted:** 5. Estimate the standard error and 95% confidence interval.
- **Source line 156 when extracted:** 6. BLACK-SCHOLES BENCHMARK
- **Source line 160 when extracted:** Cumulative distribution function for a standard normal variable.
- **Source line 169 when extracted:** Analytical Black-Scholes price for European call and put options.
- **Source line 171 when extracted:** This is used to validate the Monte Carlo estimate,
- **Source line 198 when extracted:** 7. DISPLAY RESULTS
- **Source line 206 when extracted:** Keep representation separate from pricing logic.
- **Source line 247 when extracted:** 8. PROGRAM ENTRY POINT
- **Source line 251 when extracted:** Change these values to price another European option.

Related files: [explanation index](README.md).

