
from dataclasses import replace
from importlib.util import find_spec
from math import erf, exp, log, pi, sqrt
from statistics import mean, stdev
import unittest

from option_pricing import Configuration, contracts, load_engine, run_pricing


@unittest.skipUnless(find_spec("numpy"), "Advanced estimators require NumPy")
class EstimatorTests(unittest.TestCase):
    def test_antithetic_interval_uses_pair_averages(self):
        import numpy as np
        config = Configuration(simulations=10, seed=13, batch_size=3, variance_reduction="antithetic")
        result = run_pricing(config)
        rng = np.random.default_rng(13)
        z = rng.standard_normal(5)
        plus = np.maximum(100 * np.exp(.03 + .2 * z) - 100, 0) * exp(-.05)
        minus = np.maximum(100 * np.exp(.03 - .2 * z) - 100, 0) * exp(-.05)
        paired = (plus + minus) / 2
        self.assertAlmostEqual(result["result"]["price"], mean(paired))
        self.assertAlmostEqual(result["result"]["standard_error"], stdev(paired) / sqrt(5))
        self.assertEqual(result["estimator"]["independent_samples"], 5)
        self.assertEqual(result["result"]["simulations"], 10)

    def test_control_pilot_and_main_are_separate(self):
        import numpy as np
        config = Configuration(simulations=18, pilot_simulations=12, seed=9,
                               batch_size=4, variance_reduction="both")
        report = run_pricing(config)
        main_seed = np.random.SeedSequence(9)
        pilot_seed = main_seed.spawn(1)[0]

        def draws(seed, count):
            z = np.random.default_rng(seed).standard_normal(count)
            plus = 100 * np.exp(.03 + .2 * z)
            minus = 100 * np.exp(.03 - .2 * z)
            y = (np.maximum(plus - 100, 0) + np.maximum(minus - 100, 0)) * exp(-.05) / 2
            x = (plus + minus) * exp(-.05) / 2
            return y, x

        py, px = draws(pilot_seed, 6)
        beta = np.cov(px, py, ddof=1)[0, 1] / np.var(px, ddof=1)
        y, x = draws(main_seed, 9)
        expected = y - beta * (x - 100)
        self.assertAlmostEqual(report["estimator"]["control_coefficients"]["price"], beta)
        self.assertAlmostEqual(report["result"]["price"], mean(expected))
        self.assertAlmostEqual(report["result"]["standard_error"], stdev(expected) / 3)
        self.assertEqual(report["estimator"]["pilot_paths"], 12)

    def test_greek_intervals_use_correlated_path_differences(self):
        import numpy as np
        config = Configuration(simulations=200, batch_size=31, seed=11,
                               variance_reduction="antithetic", greeks=True)
        report = run_pricing(config)
        z = np.random.default_rng(11).standard_normal(100)
        factors = np.exp(.03 + .2 * np.column_stack((z, -z)))
        base = np.maximum(100 * factors - 100, 0) * exp(-.05)
        up = np.maximum(100.5 * factors - 100, 0) * exp(-.05)
        down = np.maximum(99.5 * factors - 100, 0) * exp(-.05)
        delta_samples = ((up - down) / 1.0).mean(axis=1)
        gamma_samples = ((up - 2 * base + down) / .5 ** 2).mean(axis=1)
        for name, samples in (("delta", delta_samples), ("gamma", gamma_samples)):
            self.assertAlmostEqual(report["greeks"][name]["estimate"], mean(samples))
            self.assertAlmostEqual(report["greeks"][name]["standard_error"], stdev(samples) / 10)

    def test_geometric_control_matches_direct_lognormal_expectation(self):
        from variance_reduction import control_mean
        config = Configuration(engine="path", product="asian", rate=.03, dividend=.01,
                               volatility=.25, maturity=1.5, time_steps=12)
        _, m, o = contracts(config)
        n, t, sig = 12, 1.5, .25

        import numpy as np
        times = np.arange(1, n + 1) * t / n
        mu = log(100) + (.03 - .01 - .5 * sig ** 2) * times.mean()
        variance = (sig ** 2 * np.minimum.outer(times, times)).mean()
        sd = sqrt(variance)
        d2 = (mu - log(100)) / sd
        cdf = lambda z: .5 * (1 + erf(z / sqrt(2)))
        expected = exp(-.03 * t) * (exp(mu + variance / 2) * cdf(d2 + sd) - 100 * cdf(d2))
        self.assertAlmostEqual(control_mean(m, o, n), expected)

        config.time_steps, config.variance_reduction = 1, "both"
        report = run_pricing(config)
        self.assertLess(report["result"]["standard_error"], 1e-10)
        _, m, o = contracts(config)
        self.assertAlmostEqual(report["result"]["price"], load_engine("terminal").black_scholes_price(m, o))

    def test_greeks_against_analytical_values(self):
        config = Configuration(spot=100, strike=105, maturity=1.5, rate=.03,
            dividend=.01, volatility=.24, simulations=60000, variance_reduction="both", greeks=True)
        for kind in ("call", "put"):
            config.option_type = kind
            report = run_pricing(config)
            s, k, t, r, q, sig = 100, 105, 1.5, .03, .01, .24
            d1 = (log(s / k) + (r - q + .5 * sig ** 2) * t) / (sig * sqrt(t))
            d2 = d1 - sig * sqrt(t)
            cdf = lambda x: .5 * (1 + erf(x / sqrt(2)))
            pdf = exp(-d1 ** 2 / 2) / sqrt(2 * pi)
            sign = 1 if kind == "call" else -1
            expected = dict(delta=sign * exp(-q * t) * cdf(sign * d1),
                gamma=exp(-q * t) * pdf / (s * sig * sqrt(t)),
                vega=s * exp(-q * t) * pdf * sqrt(t) * .01,
                rho=sign * k * t * exp(-r * t) * cdf(sign * d2) * .01,
                theta=(-s * exp(-q * t) * pdf * sig / (2 * sqrt(t))
                    - sign * r * k * exp(-r * t) * cdf(sign * d2)
                    + sign * q * s * exp(-q * t) * cdf(sign * d1)) / 365)
            for name, target in expected.items():
                with self.subTest(kind=kind, greek=name):
                    estimate = report["greeks"][name]
                    self.assertLess(abs(estimate["estimate"] - target),
                                    4.5 * estimate["standard_error"] + 2e-5)

    def test_greeks_do_not_change_base_price(self):
        for method in ("none", "antithetic", "control", "both"):
            config = Configuration(engine="path", product="asian", simulations=400,
                time_steps=12, variance_reduction=method, pilot_simulations=100)
            without = run_pricing(config)
            with_greeks = run_pricing(replace(config, greeks=True))
            for field in without["result"]:
                self.assertAlmostEqual(without["result"][field], with_greeks["result"][field], places=12)

    def test_repeated_seed_coverage_and_standard_errors(self):
        target = load_engine("terminal").black_scholes_price(
            load_engine("terminal").MarketData(100, .05, .2),
            load_engine("terminal").EuropeanOption(100, 1, "call"))
        for method in ("none", "antithetic", "control", "both"):
            errors = []
            coverage = 0
            for seed in range(60):
                config = Configuration(simulations=4096, seed=seed,
                    variance_reduction=method, greeks=method == "none", pilot_simulations=1024)

                result = run_pricing(config)["result"]
                errors.append((result["price"] - target) / result["standard_error"])
                coverage += result["confidence_interval_low"] <= target <= result["confidence_interval_high"]
            with self.subTest(method=method):
                self.assertLess(abs(mean(errors)), .5)
                self.assertGreater(mean(z * z for z in errors), .5)
                self.assertLess(mean(z * z for z in errors), 1.8)
                self.assertGreaterEqual(coverage, 50)

    def test_barrier_modes_and_boundaries(self):
        for method in ("antithetic", "control", "both"):
            config = Configuration(engine="path", product="up_and_out_barrier", barrier=100.1,
                simulations=1000, time_steps=12, variance_reduction=method, greeks=True)
            report = run_pricing(config)
            self.assertLess(report["estimator"]["bumps"]["spot_absolute"], .1)
            self.assertTrue(any("discontinuities" in note for note in report["notes"]))
        zero = run_pricing(Configuration(volatility=0, variance_reduction="both", greeks=True))
        self.assertEqual(zero["result"]["standard_error"], 0)
        self.assertEqual(zero["estimator"]["bumps"]["vega_scheme"], "forward (volatility boundary)")

    def test_invalid_advanced_settings(self):
        for config in (Configuration(variance_reduction="antithetic", simulations=3),
                       Configuration(variance_reduction="both", pilot_simulations=5),
                       Configuration(variance_reduction="both", backend="python"),
                       Configuration(greeks=True, spot_bump=0)):
            with self.assertRaises(ValueError):
                run_pricing(config)

    def test_engine_api_accepts_variance_reduction(self):
        engine = load_engine("terminal")
        market = engine.MarketData(100, .05, .2)
        option = engine.EuropeanOption(100, 1, "call")
        result = engine.price_option_monte_carlo(market, option, 1000, variance_reduction="both")
        self.assertEqual(result.simulations, 1000)


if __name__ == "__main__":
    unittest.main()
