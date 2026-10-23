from types import SimpleNamespace
from math import isfinite, sqrt

def validate_count(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}.')

def validate_market_contract(market, option):
    fields = {'spot_price': market.spot_price, 'risk_free_rate': market.risk_free_rate, 'volatility': market.volatility, 'dividend_yield': market.dividend_yield, 'strike_price': option.strike_price, 'maturity_years': option.maturity_years}
    for name, value in fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or (not isfinite(value)):
            raise ValueError(f'{name} must be a finite number.')
    for name in ('spot_price', 'strike_price', 'maturity_years'):
        if fields[name] <= 0:
            raise ValueError(f'{name} must be greater than zero.')
    if market.volatility < 0:
        raise ValueError('Volatility cannot be negative.')
    if not isinstance(option.option_type, str) or option.option_type.lower() not in {'call', 'put'}:
        raise ValueError("Option type must be 'call' or 'put'.")

def summarize_payoffs(payoffs, discount):
    count, mean, m2 = (0, 0.0, 0.0)
    for payoff in payoffs:
        if not isfinite(payoff):
            raise ValueError('Simulation produced a nonfinite payoff.')
        count += 1
        delta = payoff - mean
        mean += delta / count
        m2 += delta * (payoff - mean)
    if count < 2:
        raise ValueError('At least two payoffs are required.')
    return summary_from_moments(count, mean, m2, discount)

def summary_from_moments(count, mean, m2, discount):
    if count < 2:
        raise ValueError('At least two payoffs are required.')
    if not all((isfinite(value) for value in (mean, m2, discount))) or discount <= 0:
        raise ValueError('Numerical range exceeded; check the market and contract inputs.')
    price = discount * mean
    error = discount * sqrt(max(m2, 0.0) / (count - 1) / count)
    if not isfinite(price) or not isfinite(error):
        raise ValueError('Numerical range exceeded while calculating pricing statistics.')
    return dict(price=price, standard_error=error, confidence_interval_low=price - 1.96 * error, confidence_interval_high=price + 1.96 * error, simulations=count)
from dataclasses import dataclass
from math import erfc, exp, log, sqrt

def lognormal_option_mean(log_mean, log_variance, strike, discount, option_type):
    expected = exp(log_mean + 0.5 * log_variance)
    direction = 1 if option_type.lower() == 'call' else -1
    if log_variance == 0:
        return discount * max(direction * (expected - strike), 0.0)
    sd = sqrt(log_variance)
    d2 = (log_mean - log(strike)) / sd
    d1 = d2 + sd
    cdf = lambda x: 0.5 * erfc(-x / sqrt(2))
    if direction == 1:
        return discount * (expected * cdf(d1) - strike * cdf(d2))
    return discount * (strike * cdf(-d2) - expected * cdf(-d1))

def control_mean(market, option, time_steps):
    product = getattr(option, 'product_type', 'european').lower()
    t, sigma = (option.maturity_years, market.volatility)
    if product == 'european':
        return market.spot_price * exp(-market.dividend_yield * t)
    log_mean = log(market.spot_price)
    drift = market.risk_free_rate - market.dividend_yield - 0.5 * sigma ** 2
    if product == 'asian':
        n = time_steps
        log_mean += drift * t * (n + 1) / (2 * n)
        log_variance = sigma ** 2 * t * (n + 1) * (2 * n + 1) / (6 * n ** 2)
    else:
        log_mean += drift * t
        log_variance = sigma ** 2 * t
    return lognormal_option_mean(log_mean, log_variance, option.strike_price, exp(-market.risk_free_rate * t), option.option_type)

def fit_coefficient(np, payoffs, controls):
    x = controls - controls.mean()
    y = payoffs - payoffs.mean()
    denominator = float(np.dot(x, x))
    if denominator <= np.finfo(float).eps * max(1.0, float(np.dot(controls, controls))):
        return 0.0
    return float(np.dot(x, y) / denominator)

@dataclass
class Moments:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, np, values):
        if not np.isfinite(values).all():
            raise ValueError('Simulation produced nonfinite estimator values.')
        size = len(values)
        batch_mean = float(values[0]) if np.all(values == values[0]) else float(values.mean())
        centered = values - batch_mean
        total = self.count + size
        delta = batch_mean - self.mean
        self.m2 += float(np.dot(centered, centered)) + delta ** 2 * self.count * size / total
        self.mean += delta * size / total
        self.count = total

    def summary(self):
        return summary_from_moments(self.count, self.mean, self.m2, 1.0)
from dataclasses import replace
from math import isfinite

def scenarios(market, option, enabled=False, spot_bump=0.005, volatility_bump=0.001, rate_bump=0.0001, maturity_bump=1 / 365):
    variants = {'base': (market, option)}
    formulas = {'price': {'base': 1.0}}
    details = {}
    if not enabled:
        return (variants, formulas, details)
    for name, value in (('spot_bump', spot_bump), ('volatility_bump', volatility_bump), ('rate_bump', rate_bump), ('maturity_bump', maturity_bump)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or (not isfinite(value)) or (value <= 0):
            raise ValueError(f'{name} must be finite and positive.')
    if spot_bump >= 1:
        raise ValueError('spot_bump is a relative fraction and must be below 1.')
    h = market.spot_price * spot_bump
    barrier = getattr(option, 'barrier_price', None)
    if getattr(option, 'product_type', '').lower() == 'up_and_out_barrier':
        h = min(h, 0.5 * (barrier - market.spot_price))
    if h <= 0 or market.spot_price + h == market.spot_price:
        raise ValueError('Spot bump is too small for numerical differentiation.')
    variants['spot_up'] = (replace(market, spot_price=market.spot_price + h), option)
    variants['spot_down'] = (replace(market, spot_price=market.spot_price - h), option)
    formulas['delta'] = {'spot_up': 1 / (2 * h), 'spot_down': -1 / (2 * h)}
    formulas['gamma'] = {'spot_up': 1 / h ** 2, 'base': -2 / h ** 2, 'spot_down': 1 / h ** 2}
    v = volatility_bump
    variants['vol_up'] = (replace(market, volatility=market.volatility + v), option)
    if market.volatility >= v:
        variants['vol_down'] = (replace(market, volatility=market.volatility - v), option)
        formulas['vega'] = {'vol_up': 1 / (2 * v), 'vol_down': -1 / (2 * v)}
        vega_scheme = 'central'
    else:
        formulas['vega'] = {'vol_up': 1 / v, 'base': -1 / v}
        vega_scheme = 'forward (volatility boundary)'
    r = rate_bump
    variants['rate_up'] = (replace(market, risk_free_rate=market.risk_free_rate + r), option)
    variants['rate_down'] = (replace(market, risk_free_rate=market.risk_free_rate - r), option)
    formulas['rho'] = {'rate_up': 1 / (2 * r), 'rate_down': -1 / (2 * r)}
    dt = min(maturity_bump, 0.25 * option.maturity_years)
    variants['time_up'] = (market, replace(option, maturity_years=option.maturity_years + dt))
    variants['time_down'] = (market, replace(option, maturity_years=option.maturity_years - dt))
    formulas['theta'] = {'time_down': 1 / (2 * dt), 'time_up': -1 / (2 * dt)}
    details = dict(spot_absolute=h, volatility_absolute=v, rate_absolute=r, maturity_years=dt, vega_scheme=vega_scheme, theta_convention='-dV/dT; monitoring dates rescaled with maturity')
    return (variants, formulas, details)
from math import exp, log, sqrt

def _batches(np, variants, formulas, count, steps, rng, batch_size, antithetic, control):
    for start in range(0, count, batch_size):
        size = min(batch_size, count - start)
        shape = (size, 2 if antithetic else 1)
        states = {}
        for name, (market, option) in variants.items():
            dt = option.maturity_years / steps
            states[name] = dict(stock=np.full(shape, market.spot_price, dtype=float), total=np.zeros(shape), log_total=np.zeros(shape), alive=np.ones(shape, dtype=bool), drift=(market.risk_free_rate - market.dividend_yield - 0.5 * market.volatility ** 2) * dt, diffusion=market.volatility * sqrt(dt))
        product = getattr(next(iter(variants.values()))[1], 'product_type', 'european').lower()
        for _ in range(steps):
            z = rng.standard_normal((size, 1))
            if antithetic:
                z = np.concatenate((z, -z), axis=1)
            for name, (market, option) in variants.items():
                state = states[name]
                log_increment = state['drift'] + state['diffusion'] * z
                state['stock'] *= np.exp(log_increment)
                if product == 'asian':
                    state['total'] += state['stock']
                    if control:
                        state['log_total'] += np.log(state['stock'])
                if product == 'up_and_out_barrier':
                    state['alive'] &= state['stock'] < option.barrier_price
        payoffs, controls = ({}, {})
        for name, (market, option) in variants.items():
            state = states[name]
            stock = state['stock']
            direction = 1 if option.option_type.lower() == 'call' else -1
            underlying = state['total'] / steps if product == 'asian' else stock
            discount = exp(-market.risk_free_rate * option.maturity_years)
            y = np.maximum(direction * (underlying - option.strike_price), 0) * discount
            if product == 'up_and_out_barrier':
                y *= state['alive']
            payoffs[name] = y.mean(axis=1)
            if control:
                if product == 'european':
                    x = stock * discount
                else:
                    reference = np.exp(state['log_total'] / steps) if product == 'asian' else stock
                    x = np.maximum(direction * (reference - option.strike_price), 0) * discount
                controls[name] = x.mean(axis=1)
        y_out, x_out = ({}, {})
        for label, coefficients in formulas.items():
            y_out[label] = sum((weight * payoffs[name] for name, weight in coefficients.items()))
            if control:
                x_out[label] = sum((weight * controls[name] for name, weight in coefficients.items()))
        yield (y_out, x_out)

def estimate(market, option, simulations, time_steps=1, seed=42, batch_size=8192, variance_reduction='none', greeks=False, pilot_simulations=2048, spot_bump=0.005, volatility_bump=0.001, rate_bump=0.0001, maturity_bump=1 / 365):
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError('Advanced estimators require NumPy: python -m pip install numpy') from exc
    validate_market_contract(market, option)
    validate_count(simulations, 'simulations', 2)
    validate_count(time_steps, 'time_steps', 1)
    validate_count(batch_size, 'batch_size', 1)
    if variance_reduction not in {'none', 'antithetic', 'control', 'both'}:
        raise ValueError('Unknown variance reduction method.')
    product = getattr(option, 'product_type', 'european').lower()
    if product not in {'european', 'asian', 'up_and_out_barrier'}:
        raise ValueError('Unsupported product.')
    if product == 'up_and_out_barrier':
        barrier = getattr(option, 'barrier_price', None)
        if barrier is None or not np.isfinite(barrier) or barrier <= market.spot_price:
            raise ValueError('Barrier must be finite and above spot.')
    anti = variance_reduction in {'antithetic', 'both'}
    control = variance_reduction in {'control', 'both'}
    factor = 2 if anti else 1
    if simulations % factor or simulations // factor < 2:
        raise ValueError('Antithetic pricing requires an even number of paths, at least 4.')
    if control:
        validate_count(pilot_simulations, 'pilot_simulations', 4)
        if pilot_simulations % factor:
            raise ValueError('Antithetic control fitting requires an even pilot path count.')
    variants, formulas, bumps = scenarios(market, option, greeks, spot_bump, volatility_bump, rate_bump, maturity_bump)
    steps = 1 if product == 'european' else time_steps
    main_seed = np.random.SeedSequence(seed)
    pilot_seed = main_seed.spawn(1)[0]
    beta = {name: 0.0 for name in formulas}
    expected = {name: 0.0 for name in formulas}
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        if control:
            means = {name: control_mean(m, o, steps) for name, (m, o) in variants.items()}
            expected = {label: sum((weight * means[name] for name, weight in weights.items())) for label, weights in formulas.items()}
            pilot_y = {name: [] for name in formulas}
            pilot_x = {name: [] for name in formulas}
            for y, x in _batches(np, variants, formulas, pilot_simulations // factor, steps, np.random.default_rng(pilot_seed), batch_size, anti, True):
                for name in formulas:
                    pilot_y[name].append(y[name])
                    pilot_x[name].append(x[name])
            for name in formulas:
                beta[name] = fit_coefficient(np, np.concatenate(pilot_y[name]), np.concatenate(pilot_x[name]))
        moments = {name: Moments() for name in formulas}
        raw_price = Moments()
        for y, x in _batches(np, variants, formulas, simulations // factor, steps, np.random.default_rng(main_seed), batch_size, anti, control):
            raw_price.update(np, y['price'])
            for name in formulas:
                adjusted = y[name] - beta[name] * (x[name] - expected[name]) if control else y[name]
                moments[name].update(np, adjusted)
    summaries = {name: moment.summary() for name, moment in moments.items()}
    price = summaries.pop('price')
    independent_samples = price['simulations']
    price['simulations'] = simulations
    greek_results = {}
    units = dict(delta='price per $1 spot', gamma='delta per $1 spot', vega='price per 1 percentage point volatility', rho='price per 1 percentage point interest rate', theta='price per calendar day')
    for name, summary in summaries.items():
        scale = 0.01 if name in {'vega', 'rho'} else 1 / 365 if name == 'theta' else 1
        greek_results[name] = dict(estimate=summary['price'] * scale, standard_error=summary['standard_error'] * scale, confidence_interval_low=summary['confidence_interval_low'] * scale, confidence_interval_high=summary['confidence_interval_high'] * scale, independent_samples=independent_samples, unit=units[name])
    notes = ['Intervals quantify Monte Carlo sampling uncertainty, not model error or finite-difference bias.']
    if greeks:
        notes.append('Greeks use common-random-number finite differences; check sensitivity to bump sizes.')
    if greeks and product == 'up_and_out_barrier':
        notes.append('Barrier discontinuities can make Greeks noisy, particularly Gamma; inspect bump stability and larger samples.')
    return dict(result=price, greeks=greek_results, estimator=dict(method=variance_reduction, independent_samples=independent_samples, production_paths=simulations, pilot_paths=pilot_simulations if control else 0, total_path_evaluations=(simulations + (pilot_simulations if control else 0)) * len(variants), parameter_scenarios=len(variants), control_coefficients=beta if control else {}, control_name={'european': 'discounted terminal stock', 'asian': 'geometric Asian payoff', 'up_and_out_barrier': 'vanilla European payoff'}[product] if control else None, unadjusted_price=raw_price.summary()['price'], unadjusted_standard_error=raw_price.summary()['standard_error'], bumps=bumps), notes=notes)
from math import exp, sqrt
from random import Random

def price_kernel(market, option, simulations, time_steps=1, seed=42, backend='auto', batch_size=8192, variance_reduction='none', pilot_simulations=2048):
    if backend not in {'auto', 'python', 'numpy'}:
        raise ValueError("backend must be 'auto', 'python', or 'numpy'.")
    validate_count(batch_size, 'batch_size', 1)
    if variance_reduction != 'none':
        if backend == 'python':
            raise ValueError('Variance reduction requires NumPy; select auto or numpy.')
        return estimate(market, option, simulations, time_steps, seed, batch_size, variance_reduction, pilot_simulations=pilot_simulations)['result']
    np = None
    if backend != 'python':
        try:
            import numpy as np
        except ImportError:
            if backend == 'numpy':
                raise ImportError('The NumPy backend requires: python -m pip install numpy') from None
    product = getattr(option, 'product_type', 'european').lower()
    direction = 1.0 if option.option_type.lower() == 'call' else -1.0
    discount = exp(-market.risk_free_rate * option.maturity_years)
    if market.volatility == 0:
        payoff = next(_python_payoffs(market, option, 1, time_steps, seed, product, direction))
        return summary_from_moments(simulations, payoff, 0.0, discount)
    if np is not None:
        return _numpy_price(np, market, option, simulations, time_steps, seed, batch_size, product, direction, discount)
    payoffs = _python_payoffs(market, option, simulations, time_steps, seed, product, direction)
    return summarize_payoffs(payoffs, discount)

def _python_payoffs(market, option, simulations, time_steps, seed, product, direction):
    rng = Random(seed)
    gaussian = rng.gauss
    spot, strike = (market.spot_price, option.strike_price)
    steps = 1 if product == 'european' else time_steps
    dt = option.maturity_years / steps
    drift = (market.risk_free_rate - market.dividend_yield - 0.5 * market.volatility ** 2) * dt
    diffusion = market.volatility * sqrt(dt)
    barrier = getattr(option, 'barrier_price', None)
    asian = product == 'asian'
    barrier_option = product == 'up_and_out_barrier'
    for _ in range(simulations):
        stock, total, knocked_out = (spot, 0.0, False)
        for _ in range(steps):
            stock *= exp(drift + diffusion * gaussian(0, 1))
            if asian:
                total += stock
            if barrier_option and stock >= barrier:
                knocked_out = True
        underlying = total / steps if asian else stock
        yield (0.0 if knocked_out else max(direction * (underlying - strike), 0.0))

def _numpy_price(np, market, option, simulations, time_steps, seed, batch_size, product, direction, discount):
    rng = np.random.default_rng(seed)
    steps = 1 if product == 'european' else time_steps
    dt = option.maturity_years / steps
    drift = (market.risk_free_rate - market.dividend_yield - 0.5 * market.volatility ** 2) * dt
    diffusion = market.volatility * sqrt(dt)
    count, mean, m2 = (0, 0.0, 0.0)
    with np.errstate(over='raise', invalid='raise'):
        for start in range(0, simulations, batch_size):
            size = min(batch_size, simulations - start)
            stock = np.full(size, market.spot_price, dtype=float)
            total = np.zeros(size) if product == 'asian' else None
            alive = np.ones(size, dtype=bool) if product == 'up_and_out_barrier' else None
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
from dataclasses import dataclass
from math import erfc, exp, log, sqrt
from random import Random

@dataclass
class MarketData:
    spot_price: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0

@dataclass
class EuropeanOption:
    strike_price: float
    maturity_years: float
    option_type: str

@dataclass
class PricingResult:
    price: float
    standard_error: float
    confidence_interval_low: float
    confidence_interval_high: float
    simulations: int

def terminal_validate_inputs(market: MarketData, option: EuropeanOption, simulations: int) -> None:
    validate_market_contract(market, option)
    validate_count(simulations, 'simulations', minimum=2)

def simulate_terminal_stock_prices(market: MarketData, option: EuropeanOption, simulations: int, seed: int | None=None) -> list[float]:
    terminal_validate_inputs(market, option, simulations)
    rng = Random(seed)
    S0 = market.spot_price
    r = market.risk_free_rate
    q = market.dividend_yield
    sigma = market.volatility
    T = option.maturity_years
    drift = (r - q - 0.5 * sigma ** 2) * T
    diffusion_scale = sigma * sqrt(T)
    terminal_prices = []
    for _ in range(simulations):
        Z = rng.gauss(0, 1)
        terminal_price = S0 * exp(drift + diffusion_scale * Z)
        terminal_prices.append(terminal_price)
    return terminal_prices

def terminal_calculate_payoff(terminal_prices: float, option: EuropeanOption) -> float:
    strike = option.strike_price
    option_type = option.option_type.lower()
    if option_type == 'call':
        return max(terminal_prices - strike, 0.0)
    else:
        return max(strike - terminal_prices, 0.0)

def terminal_calculate_payoffs(terminal_prices: list[float], option: EuropeanOption) -> list[float]:
    return [terminal_calculate_payoff(price, option) for price in terminal_prices]

def terminal_price_option_monte_carlo(market: MarketData, option: EuropeanOption, simulations: int=100000, seed: int | None=42, *, backend: str='auto', batch_size: int=8192, variance_reduction: str='none', pilot_simulations: int=2048) -> PricingResult:
    terminal_validate_inputs(market, option, simulations)
    return PricingResult(**price_kernel(market, option, simulations, seed=seed, backend=backend, batch_size=batch_size, variance_reduction=variance_reduction, pilot_simulations=pilot_simulations))

def normal_cdf(value: float) -> float:
    return 0.5 * erfc(-value / sqrt(2))

def black_scholes_price(market: MarketData, option: EuropeanOption) -> float:
    validate_market_contract(market, option)
    s = market.spot_price
    k = option.strike_price
    t = option.maturity_years
    r = market.risk_free_rate
    q = market.dividend_yield
    sigma = market.volatility
    if sigma == 0:
        terminal = s * exp((r - q) * t)
        return exp(-r * t) * terminal_calculate_payoff(terminal, option)
    d1 = (log(s) - log(k) + (r - q + 0.5 * sigma ** 2) * t) / (sigma * sqrt(t))
    d2 = d1 - sigma * sqrt(t)
    if option.option_type.lower() == 'call':
        return s * exp(-q * t) * normal_cdf(d1) - k * exp(-r * t) * normal_cdf(d2)
    return k * exp(-r * t) * normal_cdf(-d2) - s * exp(-q * t) * normal_cdf(-d1)

def terminal_print_pricing_summary(market: MarketData, option: EuropeanOption, monte_carlo_result: PricingResult, black_scholes_result: float) -> None:
    print('\n' + '=' * 60)
    print('MONTE CARLO OPTION PRICING ENGINE')
    print('=' * 60)
    print(f'Option type:          {option.option_type.upper()}')
    print(f'Spot price:           ${market.spot_price:.2f}')
    print(f'Strike price:         ${option.strike_price:.2f}')
    print(f'Maturity:             {option.maturity_years:.2f} years')
    print(f'Risk-free rate:       {market.risk_free_rate:.2%}')
    print(f'Volatility:           {market.volatility:.2%}')
    print(f'Simulations:          {monte_carlo_result.simulations:,}')
    print('-' * 60)
    print(f'Monte Carlo price:    ${monte_carlo_result.price:.4f}')
    print(f'Standard error:       ${monte_carlo_result.standard_error:.4f}')
    print(f'95% confidence interval: ${monte_carlo_result.confidence_interval_low:.4f} to ${monte_carlo_result.confidence_interval_high:.4f}')
    print(f'Blackâ€“Scholes price:  ${black_scholes_result:.4f}')
    difference = monte_carlo_result.price - black_scholes_result
    print(f'Difference:           ${difference:.4f}')
    within_interval = monte_carlo_result.confidence_interval_low <= black_scholes_result <= monte_carlo_result.confidence_interval_high
    if within_interval:
        print('\nValidation: Black-Scholes is within the 95% interval.')
    else:
        print('\nValidation: Benchmark lies outside this approximate interval; inspect sampling error and model assumptions.')
    print('=' * 60 + '\n')
from dataclasses import dataclass
from math import exp, sqrt
from random import Random
from math import isfinite
from collections.abc import Iterator

@dataclass
class OptionContract:
    strike_price: float
    maturity_years: float
    option_type: str
    product_type: str
    barrier_price: float | None = None

def path_validate_inputs(market: MarketData, option: OptionContract, simulations: int, time_steps: int) -> None:
    validate_market_contract(market, option)
    validate_count(simulations, 'simulations', minimum=2)
    validate_count(time_steps, 'time_steps', minimum=1)
    valid_product_types = {'european', 'asian', 'up_and_out_barrier'}
    if not isinstance(option.product_type, str):
        raise ValueError('Product type must be a string.')
    if option.product_type.lower() not in valid_product_types:
        raise ValueError("Product type must be 'european', 'asian', or 'up_and_out_barrier'.")
    if option.product_type.lower() == 'up_and_out_barrier':
        if option.barrier_price is None or isinstance(option.barrier_price, bool) or (not isinstance(option.barrier_price, (int, float))) or (not isfinite(option.barrier_price)) or (option.barrier_price <= 0):
            raise ValueError('Barrier options require a finite positive barrier price.')
        if option.barrier_price <= market.spot_price:
            raise ValueError('For this up-and-out example, the barrier must be above the current stock price.')

def iter_price_paths(market: MarketData, option: OptionContract, simulations: int, time_steps: int, seed: int | None=42) -> Iterator[list[float]]:
    path_validate_inputs(market, option, simulations, time_steps)
    rng = Random(seed)
    time_increment = option.maturity_years / time_steps
    risk_neutral_growth = (market.risk_free_rate - market.dividend_yield - 0.5 * market.volatility ** 2) * time_increment
    volatility_step_size = market.volatility * sqrt(time_increment)
    for _ in range(simulations):
        current_path = [market.spot_price]
        current_stock_price = market.spot_price
        for _ in range(time_steps):
            random_normal_shock = rng.gauss(0, 1)
            current_stock_price *= exp(risk_neutral_growth + volatility_step_size * random_normal_shock)
            current_path.append(current_stock_price)
        yield current_path

def simulate_price_paths(market: MarketData, option: OptionContract, simulations: int, time_steps: int, seed: int | None=42) -> list[list[float]]:
    return list(iter_price_paths(market, option, simulations, time_steps, seed))

def vanilla_payoff(stock_price: float, option: OptionContract) -> float:
    if option.option_type.lower() == 'call':
        return max(stock_price - option.strike_price, 0.0)
    return max(option.strike_price - stock_price, 0.0)

def european_payoff(price_path: list[float], option: OptionContract) -> float:
    terminal_stock_price = price_path[-1]
    return vanilla_payoff(terminal_stock_price, option)

def asian_payoff(price_path: list[float], option: OptionContract) -> float:
    monitored_prices = price_path[1:]
    average_stock_price = sum(monitored_prices) / len(monitored_prices)
    return vanilla_payoff(average_stock_price, option)

def up_and_out_barrier_payoff(price_path: list[float], option: OptionContract) -> float:
    barrier_was_hit = any((stock_price >= option.barrier_price for stock_price in price_path))
    if barrier_was_hit:
        return 0.0
    terminal_stock_price = price_path[-1]
    return vanilla_payoff(terminal_stock_price, option)

def calculate_path_payoff(price_path: list[float], option: OptionContract) -> float:
    product_type = option.product_type.lower()
    if product_type == 'european':
        return european_payoff(price_path, option)
    if product_type == 'asian':
        return asian_payoff(price_path, option)
    if product_type == 'up_and_out_barrier':
        return up_and_out_barrier_payoff(price_path, option)
    raise ValueError('Unsupported product type.')

def path_price_option_monte_carlo(market: MarketData, option: OptionContract, simulations: int=50000, time_steps: int=252, seed: int | None=42, *, backend: str='auto', batch_size: int=8192, variance_reduction: str='none', pilot_simulations: int=2048) -> PricingResult:
    path_validate_inputs(market=market, option=option, simulations=simulations, time_steps=time_steps)
    return PricingResult(**price_kernel(market, option, simulations, time_steps, seed, backend=backend, batch_size=batch_size, variance_reduction=variance_reduction, pilot_simulations=pilot_simulations))

def path_print_pricing_summary(market: MarketData, option: OptionContract, result: PricingResult, time_steps: int) -> None:
    print('\n' + '=' * 60)
    print('PATH-BASED MONTE CARLO OPTION PRICING ENGINE')
    print('=' * 60)
    print(f'Product:              {option.product_type}')
    print(f'Option type:          {option.option_type.upper()}')
    print(f'Spot price:           ${market.spot_price:.2f}')
    print(f'Strike price:         ${option.strike_price:.2f}')
    print(f'Maturity:             {option.maturity_years:.2f} years')
    print(f'Volatility:           {market.volatility:.2%}')
    print(f'Simulations:          {result.simulations:,}')
    print(f'Time steps per path:  {time_steps:,}')
    if option.barrier_price is not None:
        print(f'Barrier price:        ${option.barrier_price:.2f}')
    print('-' * 60)
    print(f'Monte Carlo price:    ${result.price:.4f}')
    print(f'Standard error:       ${result.standard_error:.4f}')
    print(f'95% confidence interval: ${result.confidence_interval_low:.4f} to ${result.confidence_interval_high:.4f}')
    print('=' * 60 + '\n')
import argparse
from dataclasses import asdict, dataclass
from functools import lru_cache
import importlib.util
import json
from math import isfinite
from pathlib import Path
import sys
from time import perf_counter

@lru_cache(maxsize=2)
def load_engine(name):
    shared = dict(MarketData=MarketData, PricingResult=PricingResult)
    if name == 'terminal':
        return SimpleNamespace(**shared, EuropeanOption=EuropeanOption, validate_inputs=terminal_validate_inputs, simulate_terminal_stock_prices=simulate_terminal_stock_prices, calculate_payoff=terminal_calculate_payoff, calculate_payoffs=terminal_calculate_payoffs, price_option_monte_carlo=terminal_price_option_monte_carlo, normal_cdf=normal_cdf, black_scholes_price=black_scholes_price, print_pricing_summary=terminal_print_pricing_summary)
    if name == 'path':
        return SimpleNamespace(**shared, OptionContract=OptionContract, validate_inputs=path_validate_inputs, iter_price_paths=iter_price_paths, simulate_price_paths=simulate_price_paths, vanilla_payoff=vanilla_payoff, european_payoff=european_payoff, asian_payoff=asian_payoff, up_and_out_barrier_payoff=up_and_out_barrier_payoff, calculate_path_payoff=calculate_path_payoff, price_option_monte_carlo=path_price_option_monte_carlo, print_pricing_summary=path_print_pricing_summary)
    raise ValueError("Engine must be 'terminal' or 'path'.")

@dataclass
class Configuration:
    engine: str = 'terminal'
    product: str = 'european'
    option_type: str = 'call'
    spot: float = 100.0
    strike: float = 100.0
    maturity: float = 1.0
    rate: float = 0.05
    volatility: float = 0.2
    dividend: float = 0.0
    barrier: float | None = None
    simulations: int = 50000
    time_steps: int = 252
    seed: int = 42
    backend: str = 'auto'
    batch_size: int = 8192
    variance_reduction: str = 'none'
    greeks: bool = False
    pilot_simulations: int = 2048
    spot_bump: float = 0.005
    volatility_bump: float = 0.001
    rate_bump: float = 0.0001
    maturity_bump: float = 1 / 365

def contracts(config):
    if config.engine == 'terminal' and config.product != 'european':
        raise ValueError('Asian and barrier options require the path engine.')
    engine = load_engine(config.engine)
    market = engine.MarketData(config.spot, config.rate, config.volatility, config.dividend)
    if config.engine == 'terminal':
        option = engine.EuropeanOption(config.strike, config.maturity, config.option_type)
        engine.validate_inputs(market, option, config.simulations)
    else:
        option = engine.OptionContract(config.strike, config.maturity, config.option_type, config.product, config.barrier)
        engine.validate_inputs(market, option, config.simulations, config.time_steps)
    return (engine, market, option)

def run_pricing(config):
    if config.backend not in {'auto', 'numpy', 'python'}:
        raise ValueError('backend must be auto, numpy, or python.')
    engine, market, option = contracts(config)
    kwargs = dict(simulations=config.simulations, seed=config.seed, backend=config.backend, batch_size=config.batch_size)
    if config.engine == 'path':
        kwargs['time_steps'] = config.time_steps
    start = perf_counter()
    advanced = None
    if config.greeks or config.variance_reduction != 'none':
        if config.backend == 'python':
            raise ValueError('Greeks and variance reduction require NumPy; select auto or numpy.')
        advanced = estimate(market, option, config.simulations, config.time_steps, config.seed, config.batch_size, config.variance_reduction, config.greeks, config.pilot_simulations, config.spot_bump, config.volatility_bump, config.rate_bump, config.maturity_bump)
        result = advanced['result']
    else:
        result = asdict(engine.price_option_monte_carlo(market, option, **kwargs))
    elapsed = perf_counter() - start
    benchmark = None
    if config.product == 'european':
        benchmark = load_engine('terminal').black_scholes_price(market, option)
    backend = config.backend
    if backend == 'auto':
        backend = 'numpy' if importlib.util.find_spec('numpy') else 'python'
    report = dict(configuration=asdict(config), backend_used=backend, result=result, black_scholes_price=benchmark, elapsed_seconds=elapsed)
    if advanced is not None:
        report.update({key: advanced[key] for key in ('greeks', 'estimator', 'notes')})
    return report

def print_report(report):
    config, result = (report['configuration'], report['result'])
    print('\n' + '=' * 62)
    print(f"{config['engine'].upper()} ENGINE | {config['product']} {config['option_type']}")
    print(f"Spot {config['spot']:g} | Strike {config['strike']:g} | Maturity {config['maturity']:g} years")
    print(f"Simulations: {result['simulations']:,} | Backend: {report['backend_used']}")
    if config['engine'] == 'path' and config['product'] != 'european':
        print(f"Monitoring dates: {config['time_steps']:,}")
    if config['product'] == 'up_and_out_barrier':
        print(f"Up-and-out barrier: ${config['barrier']:.2f} (discrete monitoring)")
    print(f"Option price:       ${result['price']:.6f}")
    print(f"Standard error:     ${result['standard_error']:.6f}")
    print(f"Approximate 95% CI: ${result['confidence_interval_low']:.6f} to ${result['confidence_interval_high']:.6f}")
    if report['black_scholes_price'] is not None:
        print(f"Black-Scholes:      ${report['black_scholes_price']:.6f}")
    if 'estimator' in report:
        estimator = report['estimator']
        print(f"Estimator: {estimator['method']} | Independent observations: {estimator['independent_samples']:,}")
        if estimator['pilot_paths']:
            print(f"Additional pilot paths: {estimator['pilot_paths']:,} (excluded from price and CI)")
            print(f"Control: {estimator['control_name']}")
            print(f"SE before/after control: {estimator['unadjusted_standard_error']:.6f} / {result['standard_error']:.6f}")
        if report['greeks']:
            print('\nGreeks - finite differences with shared random numbers')
            for name, greek in report['greeks'].items():
                print(f"  {name.title():5}: {greek['estimate']: .6f} | SE {greek['standard_error']:.6f} | 95% CI [{greek['confidence_interval_low']:.6f}, {greek['confidence_interval_high']:.6f}]")
                print(f"         {greek['unit']}")
        for note in report['notes']:
            print(f'Note: {note}')
    print(f"Pricing time:       {report['elapsed_seconds']:.4f} seconds")
    print('=' * 62)

def choose(label, choices, default=1):
    print(f'\n{label}')
    for i, (title, value) in enumerate(choices, 1):
        print(f'  {i}. {title}')
    while True:
        answer = input(f'Selection [{default}]: ').strip() or str(default)
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][1]
        print(f'Enter a number from 1 to {len(choices)}.')

def number(label, default, integer=False, minimum=None, strict=False):
    while True:
        answer = input(f'{label} [{default}]: ').strip() or str(default)
        try:
            value = int(answer) if integer else float(answer)
            if not isfinite(value) or (minimum is not None and (value <= minimum if strict else value < minimum)):
                raise ValueError
            return value
        except ValueError:
            bound = '' if minimum is None else f" {('greater than' if strict else 'at least')} {minimum}"
            print(f"Enter a finite {('integer' if integer else 'number')}{bound}.")

def interactive_configuration():
    print('MONTE CARLO OPTION PRICING DEMO')
    config = Configuration()
    config.engine = choose('Choose pricing engine', [('Terminal — European options using the expiry price', 'terminal'), ('Path based — European, Asian, or up-and-out barrier', 'path')])
    if config.engine == 'path':
        config.product = choose('Choose option product', [('European', 'european'), ('Arithmetic-average Asian', 'asian'), ('Up-and-out barrier', 'up_and_out_barrier')])
    config.option_type = choose('Choose option type', [('Call', 'call'), ('Put', 'put')])
    config.spot = number('Spot price', 100, minimum=0, strict=True)
    config.strike = number('Strike price', 100, minimum=0, strict=True)
    config.maturity = number('Maturity in years', 1, minimum=0, strict=True)
    print('Enter annual rates as decimals: 0.05 = 5%; 0.20 = 20% volatility.')
    config.rate = number('Risk-free rate', 0.05)
    config.volatility = number('Volatility', 0.2, minimum=0)
    config.dividend = number('Dividend yield', 0)
    if config.product == 'up_and_out_barrier':
        config.barrier = number('Barrier price', round(config.spot * 1.3, 4), minimum=config.spot, strict=True)
    config.simulations = number('Simulations', 50000, integer=True, minimum=2)
    if config.engine == 'path':
        config.time_steps = number('Total monitoring dates over maturity', 252, integer=True, minimum=1)
    config.seed = number('Random seed', 42, integer=True, minimum=0)
    config.backend = choose('Calculation backend', [('Automatic (NumPy when available)', 'auto'), ('Python standard library', 'python'), ('NumPy', 'numpy')])
    if config.backend != 'python':
        config.variance_reduction = choose('Variance reduction (requires NumPy)', [('None — plain Monte Carlo', 'none'), ('Antithetic pairs', 'antithetic'), ('Control variate with separate pilot', 'control'), ('Antithetic + control variate', 'both')])
        if config.variance_reduction in {'antithetic', 'both'}:
            while config.simulations < 4 or config.simulations % 2:
                print('Antithetic sampling needs an even number of physical paths, at least 4.')
                config.simulations = number('Simulations', 50000, integer=True, minimum=4)
        config.greeks = choose('Calculate Greeks (extra computation)', [('No', False), ('Yes', True)])
    return config

def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument('--interactive', action='store_true')
    result.add_argument('--engine', choices=['terminal', 'path'], default='terminal')
    result.add_argument('--product', choices=['european', 'asian', 'up_and_out_barrier'], default='european')
    result.add_argument('--type', dest='option_type', choices=['call', 'put'], default='call')
    for name, default in [('spot', 100), ('strike', 100), ('maturity', 1), ('rate', 0.05), ('volatility', 0.2), ('dividend', 0)]:
        result.add_argument(f'--{name}', type=float, default=default)
    result.add_argument('--barrier', type=float)
    result.add_argument('--simulations', type=int, default=50000)
    result.add_argument('--time-steps', type=int, default=252)
    result.add_argument('--seed', type=int, default=42)
    result.add_argument('--backend', choices=['auto', 'python', 'numpy'], default='auto')
    result.add_argument('--batch-size', type=int, default=8192)
    result.add_argument('--variance-reduction', choices=['none', 'antithetic', 'control', 'both'], default='none')
    result.add_argument('--greeks', action='store_true', help='Estimate Delta, Gamma, Vega, Rho and Theta')
    result.add_argument('--pilot-simulations', type=int, default=2048, help='Additional independent paths for control fitting')
    result.add_argument('--spot-bump', type=float, default=0.005, help='Relative spot bump for Delta/Gamma')
    result.add_argument('--volatility-bump', type=float, default=0.001)
    result.add_argument('--rate-bump', type=float, default=0.0001)
    result.add_argument('--maturity-bump', type=float, default=1 / 365)
    result.add_argument('--chart', '--output', dest='chart', help='Save a PNG diagnostic chart')
    result.add_argument('--show', action='store_true', help='Open the chart window')
    result.add_argument('--chart-simulations', type=int, default=5000, help='Independent diagnostic sample size (default: 5000)')
    result.add_argument('--report', help='Save inputs and pricing results as JSON')
    return result

def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    args = parser().parse_args(arguments)
    interactive = args.interactive or not arguments
    try:
        config = interactive_configuration() if interactive else Configuration(**{name: getattr(args, name) for name in Configuration.__dataclass_fields__})
        report = run_pricing(config)
        print_report(report)
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
            print(f'Report saved: {Path(args.report).resolve()}')
        chart = args.chart
        if interactive and (not chart):
            chart = choose('Visualization', [('Skip charts', None), ('Save charts to outcomes.png', 'outcomes.png')])
        if chart or args.show:
            render_report(config, report, chart or 'outcomes.png', args.show, args.chart_simulations)
        return 0
    except (ValueError, ImportError, OSError, OverflowError, FloatingPointError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print('\nDemo closed.')
        return 0
from pathlib import Path
import sys

def render_report(config, report, output='outcomes.png', show=False, sample_size=5000):
    validate_count(sample_size, 'chart_simulations', 2)
    try:
        import numpy as np
        import matplotlib
        if not show:
            matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError('Charts require NumPy and Matplotlib. Run: python -m pip install -r requirements-visualization.txt') from exc
    engine, market, option = contracts(config)
    chart_seed = config.seed + 1
    paths = None
    if config.engine == 'terminal':
        terminal = np.asarray(engine.simulate_terminal_stock_prices(market, option, sample_size, chart_seed))
        payoffs = np.asarray(engine.calculate_payoffs(terminal, option))
    else:
        path_sample = []
        terminal, payoffs = (np.empty(sample_size), np.empty(sample_size))
        for i, path in enumerate(engine.iter_price_paths(market, option, sample_size, config.time_steps, chart_seed)):
            terminal[i] = path[-1]
            payoffs[i] = engine.calculate_path_payoff(path, option)
            if i < 500:
                path_sample.append(path)
        paths = np.asarray(path_sample)
    payoffs *= np.exp(-market.risk_free_rate * option.maturity_years)
    count = np.arange(1, sample_size + 1)
    running = np.cumsum(payoffs) / count
    m2 = np.cumsum((payoffs[1:] - running[:-1]) * (payoffs[1:] - running[1:]))
    se = np.sqrt(np.maximum(m2, 0) / (count[1:] - 1) / count[1:])
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout='constrained')
    ax = axes[0, 0]
    if paths is not None:
        times = np.linspace(0, config.maturity, paths.shape[1])
        p05, median, p95 = np.percentile(paths, [5, 50, 95], axis=0)
        ax.plot(times, paths[:60].T, alpha=0.25, linewidth=0.6)
        ax.fill_between(times, p05, p95, color='royalblue', alpha=0.17, label='5th–95th percentiles')
        ax.plot(times, median, color='navy', label='Median')
        ax.axhline(config.strike, color='black', linestyle=':', label='Strike')
        if config.product == 'up_and_out_barrier':
            ax.axhline(config.barrier, color='red', linestyle='--', label='Knockout barrier')
        ax.set(title=f'Paths: showing {min(60, len(paths))}; band from {len(paths):,}', xlabel='Years', ylabel='Stock price ($)')
    else:
        expiry = np.linspace(min(terminal.min(), config.strike * 0.5), max(terminal.max(), config.strike * 1.5), 250)
        direction = 1 if config.option_type == 'call' else -1
        ax.plot(expiry, np.maximum(direction * (expiry - config.strike), 0), color='navy', label=f'{config.option_type.title()} payoff')
        ax.axvline(config.strike, color='black', linestyle=':', label='Strike')
        ax.set(title='Terminal engine: payoff at expiry', xlabel='Stock price at expiry ($)', ylabel='Payoff ($)')
    ax.legend(fontsize=8)
    axes[0, 1].hist(terminal, bins=60, color='royalblue', alpha=0.8)
    axes[0, 1].set(title='Diagnostic terminal prices', xlabel='Stock price at expiry ($)', ylabel='Number of scenarios')
    axes[1, 0].hist(payoffs, bins=60, color='teal', alpha=0.8)
    axes[1, 0].set(title='Diagnostic discounted payoffs', xlabel='Present value of payoff ($)', ylabel='Number of scenarios')
    ax = axes[1, 1]
    start = min(99, sample_size - 2)
    ax.plot(count[start:], running[start:], color='navy', label='Diagnostic sample mean')
    indices = np.arange(max(start, 1), sample_size)
    ax.fill_between(count[indices], running[indices] - 1.96 * se[indices - 1], running[indices] + 1.96 * se[indices - 1], alpha=0.2, label='Approximate 95% sample CI')
    ax.axhline(report['result']['price'], color='darkorange', linestyle='--', label='Full pricing run estimate')
    ax.set(title='Diagnostic convergence', xlabel='Diagnostic scenarios', ylabel='Option price ($)')
    ax.legend(fontsize=8)
    fig.suptitle(f'{config.engine} engine | {config.product} {config.option_type}\nSeparate diagnostic sample: {sample_size:,}, seed {chart_seed} | Risk-neutral scenarios')
    if getattr(config, 'variance_reduction', 'none') != 'none' or getattr(config, 'greeks', False):
        fig.supxlabel("Diagnostic samples use plain MC; their band is not the enhanced estimator's confidence interval.", fontsize=9)
    try:
        fig.savefig(output, dpi=150)
        print(f'Chart saved: {Path(output).resolve()}')
        if show:
            plt.show()
    finally:
        plt.close(fig)
    return Path(output)
if __name__ == '__main__':
    raise SystemExit(main())
