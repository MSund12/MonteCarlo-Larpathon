
from math import isfinite, sqrt


def validate_count(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}.")


def validate_market_contract(market, option):
    fields = {
        "spot_price": market.spot_price,
        "risk_free_rate": market.risk_free_rate,
        "volatility": market.volatility,
        "dividend_yield": market.dividend_yield,
        "strike_price": option.strike_price,
        "maturity_years": option.maturity_years,
    }
    for name, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError(f"{name} must be a finite number.")
    for name in ("spot_price", "strike_price", "maturity_years"):
        if fields[name] <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    if market.volatility < 0:
        raise ValueError("Volatility cannot be negative.")
    if not isinstance(option.option_type, str) or option.option_type.lower() not in {"call", "put"}:
        raise ValueError("Option type must be 'call' or 'put'.")


def summarize_payoffs(payoffs, discount):

    count, mean, m2 = 0, 0.0, 0.0
    for payoff in payoffs:
        if not isfinite(payoff):
            raise ValueError("Simulation produced a nonfinite payoff.")
        count += 1
        delta = payoff - mean
        mean += delta / count
        m2 += delta * (payoff - mean)
    if count < 2:
        raise ValueError("At least two payoffs are required.")
    return summary_from_moments(count, mean, m2, discount)


def summary_from_moments(count, mean, m2, discount):

    if count < 2:
        raise ValueError("At least two payoffs are required.")
    if not all(isfinite(value) for value in (mean, m2, discount)) or discount <= 0:
        raise ValueError("Numerical range exceeded; check the market and contract inputs.")
    price = discount * mean
    error = discount * sqrt(max(m2, 0.0) / (count - 1) / count)
    if not isfinite(price) or not isfinite(error):
        raise ValueError("Numerical range exceeded while calculating pricing statistics.")
    return dict(price=price, standard_error=error,
                confidence_interval_low=price - 1.96 * error,
                confidence_interval_high=price + 1.96 * error,
                simulations=count)
