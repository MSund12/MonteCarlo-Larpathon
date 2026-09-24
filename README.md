# MonteCarlo-Larpathon

# Monte Carlo Option Pricing Engines

## What the programs do

Both programs estimate an option's present value by simulating possible future stock prices under a risk-neutral geometric Brownian motion model. For each simulation, they calculate the option payoff at expiry, average the simulated payoffs, and discount that average back to today using the risk-free rate. They also report an estimated standard error and a 95% confidence interval to show the sampling uncertainty in the Monte Carlo estimate.

## Terminal engine

**File:** `monte carlos pricing engine_terminal engine.py`

The terminal engine simulates only the stock price at the option's expiry. It is designed for European call and put options, whose payoff depends on the stock price at expiry. Because it does not need the intermediate prices along the way, it can run many simulations without storing a full time series for each one.

The file also defines a Black–Scholes benchmark intended to compare the Monte Carlo estimate with an analytical European-option price. Its sample entry point sets up a one-year at-the-money European call, runs 100,000 simulations, and prints the estimate, confidence interval, benchmark, and difference.

**Current file status:** As written, this file has an incomplete `print_pricing_summary` function definition (the closing signature lacks a colon), so Python will stop with a syntax error before running it. In addition, `black_scholes_price` only contains a call-price return and does not implement a put-price return. The benchmark call formula also uses the call cumulative-normal term for both components, so it does not currently produce the standard Black–Scholes call formula. These are implementation issues in the current file, separate from the engine's intended design.

## Path engine

**File:** `monte carlo option pricing engine_path based engine.py`

The path engine simulates a sequence of stock prices from today through expiry for every trial. This keeps intermediate prices available so it can evaluate options whose payoff depends on the route taken by the stock, as well as standard European options. Its supported products are:

- **European:** payoff is based on the final simulated stock price.
- **Asian:** payoff is based on the arithmetic average of simulated future prices; the initial spot price is excluded.
- **Up-and-out barrier:** payoff is zero if any simulated observation reaches or exceeds the barrier. The barrier is checked at each time step, so monitoring is discrete at the selected simulation frequency.

The entry point uses 50,000 simulations and 252 time steps per path, with an Asian call as its example. It prints the estimated price, standard error, confidence interval, number of simulations, and number of time steps. Unlike the terminal engine, it does not include a Black–Scholes benchmark.

## How they compare

### Shared similarities

Both engines use the same basic risk-neutral stock-price model, accept market inputs such as spot price, risk-free rate, volatility, and dividend yield, validate key inputs, and use Monte Carlo payoffs with discounting. Both support reproducible simulations through a random seed and report a price estimate, standard error, and 95% confidence interval.

### Main differences

The terminal engine simulates one expiry price per trial and only handles European options. The path engine simulates many time points per trial and supports European, Asian, and up-and-out barrier options. The terminal engine is intended to compare its result with Black–Scholes; the path engine is intended to handle path-dependent payoffs. Their sample configurations also differ: 100,000 expiry-only trials in the terminal engine versus 50,000 paths with 252 time steps each in the path engine.

### What each does better

The terminal approach is more computationally and memory efficient for European options because it generates only the expiry price. Its Black–Scholes comparison is also a useful validation idea once the current syntax and formula issues are corrected.

The path approach is more flexible for products whose payoff depends on intermediate prices. It can model average-price Asian options and discretely monitored up-and-out barriers, which an expiry-only simulation cannot evaluate. That flexibility costs more computation and memory because every path contains multiple stock-price observations.

### When to use each

Use the **terminal engine** for a straightforward European call or put when you want an efficient Monte Carlo estimate and, after fixing its current implementation issues, a comparison against a Black–Scholes benchmark.

Use the **path engine** when pricing a European option with a path simulation, or when the product depends on the stock's intermediate prices, such as an arithmetic-average Asian option or a discretely monitored up-and-out barrier option. Choose its time-step count to reflect how often the option's path-dependent feature is monitored.
