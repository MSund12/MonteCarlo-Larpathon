
from dataclasses import dataclass
from math import erfc, exp, log, sqrt

from pricing_common import summary_from_moments


def lognormal_option_mean(log_mean, log_variance, strike, discount, option_type):

    expected = exp(log_mean + .5 * log_variance)
    direction = 1 if option_type.lower() == "call" else -1
    if log_variance == 0:
        return discount * max(direction * (expected - strike), 0.0)
    sd = sqrt(log_variance)
    d2 = (log_mean - log(strike)) / sd
    d1 = d2 + sd
    cdf = lambda x: .5 * erfc(-x / sqrt(2))
    if direction == 1:
        return discount * (expected * cdf(d1) - strike * cdf(d2))
    return discount * (strike * cdf(-d2) - expected * cdf(-d1))


def control_mean(market, option, time_steps):

    product = getattr(option, "product_type", "european").lower()
    t, sigma = option.maturity_years, market.volatility
    if product == "european":

        return market.spot_price * exp(-market.dividend_yield * t)
    log_mean = log(market.spot_price)
    drift = market.risk_free_rate - market.dividend_yield - .5 * sigma ** 2
    if product == "asian":
        n = time_steps
        log_mean += drift * t * (n + 1) / (2 * n)
        log_variance = sigma ** 2 * t * (n + 1) * (2 * n + 1) / (6 * n ** 2)
    else:

        log_mean += drift * t
        log_variance = sigma ** 2 * t
    return lognormal_option_mean(log_mean, log_variance, option.strike_price,
                                 exp(-market.risk_free_rate * t), option.option_type)


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
            raise ValueError("Simulation produced nonfinite estimator values.")
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
