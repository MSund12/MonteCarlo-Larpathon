
from dataclasses import replace
from math import isfinite


def scenarios(market, option, enabled=False, spot_bump=.005,
              volatility_bump=.001, rate_bump=.0001, maturity_bump=1 / 365):





    variants = {"base": (market, option)}
    formulas = {"price": {"base": 1.0}}
    details = {}
    if not enabled:
        return variants, formulas, details
    for name, value in (("spot_bump", spot_bump), ("volatility_bump", volatility_bump),
                        ("rate_bump", rate_bump), ("maturity_bump", maturity_bump)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive.")
    if spot_bump >= 1:
        raise ValueError("spot_bump is a relative fraction and must be below 1.")
    h = market.spot_price * spot_bump
    barrier = getattr(option, "barrier_price", None)
    if getattr(option, "product_type", "").lower() == "up_and_out_barrier":
        h = min(h, .5 * (barrier - market.spot_price))
    if h <= 0 or market.spot_price + h == market.spot_price:
        raise ValueError("Spot bump is too small for numerical differentiation.")
    variants["spot_up"] = (replace(market, spot_price=market.spot_price + h), option)
    variants["spot_down"] = (replace(market, spot_price=market.spot_price - h), option)
    formulas["delta"] = {"spot_up": 1 / (2 * h), "spot_down": -1 / (2 * h)}
    formulas["gamma"] = {"spot_up": 1 / h ** 2, "base": -2 / h ** 2, "spot_down": 1 / h ** 2}
    v = volatility_bump
    variants["vol_up"] = (replace(market, volatility=market.volatility + v), option)
    if market.volatility >= v:
        variants["vol_down"] = (replace(market, volatility=market.volatility - v), option)
        formulas["vega"] = {"vol_up": 1 / (2 * v), "vol_down": -1 / (2 * v)}
        vega_scheme = "central"
    else:
        formulas["vega"] = {"vol_up": 1 / v, "base": -1 / v}
        vega_scheme = "forward (volatility boundary)"
    r = rate_bump
    variants["rate_up"] = (replace(market, risk_free_rate=market.risk_free_rate + r), option)
    variants["rate_down"] = (replace(market, risk_free_rate=market.risk_free_rate - r), option)
    formulas["rho"] = {"rate_up": 1 / (2 * r), "rate_down": -1 / (2 * r)}
    dt = min(maturity_bump, .25 * option.maturity_years)
    variants["time_up"] = (market, replace(option, maturity_years=option.maturity_years + dt))
    variants["time_down"] = (market, replace(option, maturity_years=option.maturity_years - dt))
    formulas["theta"] = {"time_down": 1 / (2 * dt), "time_up": -1 / (2 * dt)}
    details = dict(spot_absolute=h, volatility_absolute=v, rate_absolute=r,
                   maturity_years=dt, vega_scheme=vega_scheme,
                   theta_convention="-dV/dT; monitoring dates rescaled with maturity")
    return variants, formulas, details
