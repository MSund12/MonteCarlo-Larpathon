
from math import exp, sqrt
from random import Random

from pricing_common import summarize_payoffs, summary_from_moments, validate_count


def price(market, option, simulations, time_steps=1, seed=42,
          backend="auto", batch_size=8192, variance_reduction="none", pilot_simulations=2048):





    if backend not in {"auto", "python", "numpy"}:
        raise ValueError("backend must be 'auto', 'python', or 'numpy'.")
    validate_count(batch_size, "batch_size", 1)
    if variance_reduction != "none":
        if backend == "python":
            raise ValueError("Variance reduction requires NumPy; select auto or numpy.")
        from advanced_pricing import estimate
        return estimate(market, option, simulations, time_steps, seed, batch_size,
                        variance_reduction, pilot_simulations=pilot_simulations)["result"]
    np = None
    if backend != "python":
        try:
            import numpy as np
        except ImportError:
            if backend == "numpy":
                raise ImportError("The NumPy backend requires: python -m pip install numpy") from None
    product = getattr(option, "product_type", "european").lower()
    direction = 1.0 if option.option_type.lower() == "call" else -1.0
    discount = exp(-market.risk_free_rate * option.maturity_years)

    if market.volatility == 0:
        payoff = next(_python_payoffs(market, option, 1, time_steps, seed, product, direction))
        return summary_from_moments(simulations, payoff, 0.0, discount)
    if np is not None:
        return _numpy_price(np, market, option, simulations, time_steps, seed,
                            batch_size, product, direction, discount)
    payoffs = _python_payoffs(market, option, simulations, time_steps, seed, product, direction)
    return summarize_payoffs(payoffs, discount)


def _python_payoffs(market, option, simulations, time_steps, seed, product, direction):
    rng = Random(seed)
    gaussian = rng.gauss
    spot, strike = market.spot_price, option.strike_price

    steps = 1 if product == "european" else time_steps
    dt = option.maturity_years / steps
    drift = (market.risk_free_rate - market.dividend_yield - .5 * market.volatility ** 2) * dt
    diffusion = market.volatility * sqrt(dt)
    barrier = getattr(option, "barrier_price", None)
    asian = product == "asian"
    barrier_option = product == "up_and_out_barrier"
    for _ in range(simulations):
        stock, total, knocked_out = spot, 0.0, False
        for _ in range(steps):
            stock *= exp(drift + diffusion * gaussian(0, 1))
            if asian:
                total += stock
            if barrier_option and stock >= barrier:
                knocked_out = True

        underlying = total / steps if asian else stock
        yield 0.0 if knocked_out else max(direction * (underlying - strike), 0.0)


def _numpy_price(np, market, option, simulations, time_steps, seed,
                 batch_size, product, direction, discount):
    rng = np.random.default_rng(seed)
    steps = 1 if product == "european" else time_steps
    dt = option.maturity_years / steps
    drift = (market.risk_free_rate - market.dividend_yield - .5 * market.volatility ** 2) * dt
    diffusion = market.volatility * sqrt(dt)
    count, mean, m2 = 0, 0.0, 0.0
    with np.errstate(over="raise", invalid="raise"):
        for start in range(0, simulations, batch_size):
            size = min(batch_size, simulations - start)
            stock = np.full(size, market.spot_price, dtype=float)
            total = np.zeros(size) if product == "asian" else None
            alive = np.ones(size, dtype=bool) if product == "up_and_out_barrier" else None
            for _ in range(steps):
                shocks = rng.standard_normal(size)
                shocks *= diffusion
                shocks += drift
                np.exp(shocks, out=shocks)
                stock *= shocks
                if total is not None:
                    total += stock
                if alive is not None:
                    alive &= stock < option.barrier_price
            underlying = total / steps if total is not None else stock
            payoffs = np.maximum(direction * (underlying - option.strike_price), 0.0)
            if alive is not None:
                payoffs *= alive

            batch_mean = float(payoffs.mean())
            centered = payoffs - batch_mean
            batch_m2 = float(np.dot(centered, centered))
            new_count = count + size
            delta = batch_mean - mean
            m2 += batch_m2 + delta * delta * count * size / new_count
            mean += delta * size / new_count
            count = new_count
    return summary_from_moments(count, mean, m2, discount)
