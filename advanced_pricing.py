







from math import exp, log, sqrt

from greeks import scenarios
from pricing_common import validate_count, validate_market_contract
from variance_reduction import Moments, control_mean, fit_coefficient


def _batches(np, variants, formulas, count, steps, rng, batch_size, antithetic, control):
    for start in range(0, count, batch_size):
        size = min(batch_size, count - start)
        shape = (size, 2 if antithetic else 1)
        states = {}
        for name, (market, option) in variants.items():
            dt = option.maturity_years / steps
            states[name] = dict(stock=np.full(shape, market.spot_price, dtype=float),
                total=np.zeros(shape), log_total=np.zeros(shape), alive=np.ones(shape, dtype=bool),
                drift=(market.risk_free_rate - market.dividend_yield - .5 * market.volatility ** 2) * dt,
                diffusion=market.volatility * sqrt(dt))
        product = getattr(next(iter(variants.values()))[1], "product_type", "european").lower()
        for _ in range(steps):
            z = rng.standard_normal((size, 1))
            if antithetic:
                z = np.concatenate((z, -z), axis=1)
            for name, (market, option) in variants.items():
                state = states[name]
                log_increment = state["drift"] + state["diffusion"] * z
                state["stock"] *= np.exp(log_increment)
                if product == "asian":
                    state["total"] += state["stock"]
                    if control:

                        state["log_total"] += np.log(state["stock"])
                if product == "up_and_out_barrier":
                    state["alive"] &= state["stock"] < option.barrier_price
        payoffs, controls = {}, {}
        for name, (market, option) in variants.items():
            state = states[name]
            stock = state["stock"]
            direction = 1 if option.option_type.lower() == "call" else -1
            underlying = state["total"] / steps if product == "asian" else stock
            discount = exp(-market.risk_free_rate * option.maturity_years)
            y = np.maximum(direction * (underlying - option.strike_price), 0) * discount
            if product == "up_and_out_barrier":
                y *= state["alive"]

            payoffs[name] = y.mean(axis=1)
            if control:
                if product == "european":
                    x = stock * discount
                else:
                    reference = np.exp(state["log_total"] / steps) if product == "asian" else stock
                    x = np.maximum(direction * (reference - option.strike_price), 0) * discount
                controls[name] = x.mean(axis=1)
        y_out, x_out = {}, {}
        for label, coefficients in formulas.items():
            y_out[label] = sum(weight * payoffs[name] for name, weight in coefficients.items())
            if control:
                x_out[label] = sum(weight * controls[name] for name, weight in coefficients.items())
        yield y_out, x_out


def estimate(market, option, simulations, time_steps=1, seed=42, batch_size=8192,
             variance_reduction="none", greeks=False, pilot_simulations=2048,
             spot_bump=.005, volatility_bump=.001, rate_bump=.0001, maturity_bump=1 / 365):






    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError("Advanced estimators require NumPy: python -m pip install numpy") from exc
    validate_market_contract(market, option)
    validate_count(simulations, "simulations", 2)
    validate_count(time_steps, "time_steps", 1)
    validate_count(batch_size, "batch_size", 1)
    if variance_reduction not in {"none", "antithetic", "control", "both"}:
        raise ValueError("Unknown variance reduction method.")
    product = getattr(option, "product_type", "european").lower()
    if product not in {"european", "asian", "up_and_out_barrier"}:
        raise ValueError("Unsupported product.")
    if product == "up_and_out_barrier":
        barrier = getattr(option, "barrier_price", None)
        if barrier is None or not np.isfinite(barrier) or barrier <= market.spot_price:
            raise ValueError("Barrier must be finite and above spot.")
    anti = variance_reduction in {"antithetic", "both"}
    control = variance_reduction in {"control", "both"}
    factor = 2 if anti else 1
    if simulations % factor or simulations // factor < 2:
        raise ValueError("Antithetic pricing requires an even number of paths, at least 4.")
    if control:
        validate_count(pilot_simulations, "pilot_simulations", 4)
        if pilot_simulations % factor:
            raise ValueError("Antithetic control fitting requires an even pilot path count.")
    variants, formulas, bumps = scenarios(market, option, greeks, spot_bump,
                                          volatility_bump, rate_bump, maturity_bump)
    steps = 1 if product == "european" else time_steps

    main_seed = np.random.SeedSequence(seed)
    pilot_seed = main_seed.spawn(1)[0]
    beta = {name: 0.0 for name in formulas}
    expected = {name: 0.0 for name in formulas}
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        if control:
            means = {name: control_mean(m, o, steps) for name, (m, o) in variants.items()}
            expected = {label: sum(weight * means[name] for name, weight in weights.items())
                        for label, weights in formulas.items()}
            pilot_y = {name: [] for name in formulas}
            pilot_x = {name: [] for name in formulas}
            for y, x in _batches(np, variants, formulas, pilot_simulations // factor, steps,
                                 np.random.default_rng(pilot_seed), batch_size, anti, True):
                for name in formulas:
                    pilot_y[name].append(y[name])
                    pilot_x[name].append(x[name])
            for name in formulas:
                beta[name] = fit_coefficient(np, np.concatenate(pilot_y[name]), np.concatenate(pilot_x[name]))
        moments = {name: Moments() for name in formulas}
        raw_price = Moments()
        for y, x in _batches(np, variants, formulas, simulations // factor, steps,
                             np.random.default_rng(main_seed), batch_size, anti, control):
            raw_price.update(np, y["price"])
            for name in formulas:
                adjusted = y[name] - beta[name] * (x[name] - expected[name]) if control else y[name]
                moments[name].update(np, adjusted)
    summaries = {name: moment.summary() for name, moment in moments.items()}
    price = summaries.pop("price")
    independent_samples = price["simulations"]
    price["simulations"] = simulations
    greek_results = {}
    units = dict(delta="price per $1 spot", gamma="delta per $1 spot",
                 vega="price per 1 percentage point volatility",
                 rho="price per 1 percentage point interest rate", theta="price per calendar day")
    for name, summary in summaries.items():
        scale = .01 if name in {"vega", "rho"} else 1 / 365 if name == "theta" else 1
        greek_results[name] = dict(estimate=summary["price"] * scale,
            standard_error=summary["standard_error"] * scale,
            confidence_interval_low=summary["confidence_interval_low"] * scale,
            confidence_interval_high=summary["confidence_interval_high"] * scale,
            independent_samples=independent_samples, unit=units[name])
    notes = ["Intervals quantify Monte Carlo sampling uncertainty, not model error or finite-difference bias."]
    if greeks:
        notes.append("Greeks use common-random-number finite differences; check sensitivity to bump sizes.")
    if greeks and product == "up_and_out_barrier":
        notes.append("Barrier discontinuities can make Greeks noisy, particularly Gamma; inspect bump stability and larger samples.")
    return dict(result=price, greeks=greek_results,
        estimator=dict(method=variance_reduction, independent_samples=independent_samples,
            production_paths=simulations, pilot_paths=pilot_simulations if control else 0,
            total_path_evaluations=(simulations + (pilot_simulations if control else 0)) * len(variants),
            parameter_scenarios=len(variants), control_coefficients=beta if control else {},
            control_name={"european": "discounted terminal stock", "asian": "geometric Asian payoff",
                          "up_and_out_barrier": "vanilla European payoff"}[product] if control else None,
            unadjusted_price=raw_price.summary()["price"],
            unadjusted_standard_error=raw_price.summary()["standard_error"], bumps=bumps), notes=notes)
