# Pricing engines and contracts

| Engine | Supported products | What it calculates |
|---|---|---|
| Terminal | European calls and puts | Samples the stock price at expiry directly. |
| Path | European, arithmetic Asian, and up-and-out barrier calls and puts | Uses the monitoring information required by the product. European pricing still samples expiry directly. |

**European options**

- A call pays `max(final stock price − strike, 0)`.
- A put pays `max(strike − final stock price, 0)`.
- Intermediate prices do not affect the payoff. Exercise is at expiry; American-style early exercise is not implemented.

**Arithmetic Asian options**

- Replace the final stock price in the payoff formula with the arithmetic average of monitored prices.
- Monitoring dates are equally spaced across the maturity.
- The average excludes the initial spot price and includes expiry.

**Up-and-out barrier options**

- Start with a European call or put payoff, but pay zero if the stock reaches or exceeds the upper barrier at a monitored date.
- The barrier must be above the initial stock price. Already knocked-out contracts are rejected by this demo.
- Monitoring is discrete. A crossing between simulated dates is not detected.

## Model and computational design

The stock follows risk-neutral geometric Brownian motion:

```text
S_next = S_current * exp((r - q - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
```

Here `r` is the rate, `q` the dividend yield, `sigma` volatility, and `Z` a standard normal shock. The risk-neutral drift `r-q` is used for pricing, not forecasting. Payoffs are discounted by `exp(-r*T)`.

The update is exact between selected dates under this constant-parameter model, but does not detect barrier crossings between dates. European pricing needs only expiry. Asian and barrier pricing uses monitoring dates.

Basic pricing streams observations instead of retaining complete histories. NumPy batches maintain current prices, running averages, or knockout flags, limiting working memory. Explicit path collection is available for charts. Increasing time steps changes Asian and barrier observation terms, not just runtime.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
