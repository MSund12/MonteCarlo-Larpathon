
import importlib.util
from pathlib import Path
import sys
import unittest
from math import exp
from statistics import mean, stdev
from importlib.util import find_spec


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


t = load("terminal_engine", "monte carlos pricing engine_terminal engine.py")
p = load("path_engine_test", "monte carlo option pricing engine_path based engine.py")


class PricingTests(unittest.TestCase):
    def test_python_streaming_matches_explicit_paths(self):
        market = p.MarketData(100, .05, .2, .01)
        for product in ("asian", "up_and_out_barrier"):
            for kind in ("call", "put"):
                option = p.OptionContract(100, 1, kind, product, 120)
                paths = p.simulate_price_paths(market, option, 1000, 12, 17)
                values = [p.calculate_path_payoff(path, option) * exp(-.05) for path in paths]
                result = p.price_option_monte_carlo(market, option, 1000, 12, 17, backend="python")
                self.assertAlmostEqual(result.price, mean(values))
                self.assertAlmostEqual(result.standard_error, stdev(values) / 1000 ** .5)

    @unittest.skipUnless(find_spec("numpy"), "Optional NumPy is not installed")
    def test_numpy_batch_moments_and_partial_batch(self):
        import numpy as np
        market = p.MarketData(100, .05, .2)


        for product in ("european", "asian", "up_and_out_barrier"):
            for kind in ("call", "put"):
                option = p.OptionContract(100, 1, kind, product, 120)
                rng = np.random.default_rng(19)
                paths = []
                steps = 1 if product == "european" else 12
                for size in (128, 128, 45):
                    stock = np.full(size, 100.0)
                    batch = [stock.copy()]
                    for _ in range(steps):
                        stock = stock * np.exp(.03 / steps + .2 / steps ** .5 * rng.standard_normal(size))
                        batch.append(stock.copy())
                    paths.extend(np.array(batch).T.tolist())
                values = [p.calculate_path_payoff(path, option) * exp(-.05) for path in paths]
                result = p.price_option_monte_carlo(market, option, 301, 12, 19, backend="numpy", batch_size=128)
                self.assertEqual(result.simulations, 301)
                self.assertAlmostEqual(result.price, mean(values))
                self.assertAlmostEqual(result.standard_error, stdev(values) / 301 ** .5)
                self.assertEqual(result, p.price_option_monte_carlo(market, option, 301, 12, 19,
                                                                   backend="numpy", batch_size=128))

    def test_european_ignores_unneeded_time_steps(self):
        market = p.MarketData(100, .05, .2)
        option = p.OptionContract(100, 1, "call", "european")
        self.assertEqual(p.price_option_monte_carlo(market, option, 200, 1, backend="python"),
                         p.price_option_monte_carlo(market, option, 200, 252, backend="python"))

    def test_backend_validation(self):
        market = t.MarketData(100, .05, .2)
        option = t.EuropeanOption(100, 1, "call")
        for kwargs in ({"backend": "invalid"}, {"batch_size": 0}, {"batch_size": True}):
            with self.assertRaises(ValueError):
                t.price_option_monte_carlo(market, option, 10, **kwargs)

    def test_analytical_prices_and_parity(self):
        m = t.MarketData(100, .05, .2)
        call = t.black_scholes_price(m, t.EuropeanOption(100, 1, "call"))
        put = t.black_scholes_price(m, t.EuropeanOption(100, 1, "put"))
        self.assertAlmostEqual(call, 10.450583572185565)
        self.assertAlmostEqual(put, 5.573526022256971)
        self.assertAlmostEqual(call - put, 100 - 100 * exp(-.05))

    def test_mc_against_analytical_with_dividends(self):
        for kind in ("call", "put"):
            m = t.MarketData(100, .03, .25, .02)
            o = t.EuropeanOption(105, 1.5, kind)
            expected = t.black_scholes_price(m, o)
            r = t.price_option_monte_carlo(m, o, 30000, 42)
            self.assertLess(abs(r.price - expected), 4 * r.standard_error)
            pr = p.price_option_monte_carlo(m, p.OptionContract(105, 1.5, kind, "european"), 30000, 1, 42)
            self.assertEqual(r, t.PricingResult(**vars(pr)))

    def test_zero_volatility(self):
        m = t.MarketData(100, .05, 0)
        for kind in ("call", "put"):
            o = t.EuropeanOption(100, 1, kind)
            result = t.price_option_monte_carlo(m, o, 10)
            self.assertAlmostEqual(result.price, t.black_scholes_price(m, o))
            self.assertEqual(result.standard_error, 0)

    def test_path_payoffs(self):
        asian = p.OptionContract(100, 1, "call", "asian")
        self.assertEqual(p.calculate_path_payoff([100, 110, 130], asian), 20)
        barrier = p.OptionContract(100, 1, "call", "UP_AND_OUT_BARRIER", 120)
        self.assertEqual(p.calculate_path_payoff([100, 120, 110], barrier), 0)
        self.assertEqual(p.calculate_path_payoff([100, 115, 110], barrier), 10)

    def test_validation(self):
        for engine, option in ((t, t.EuropeanOption(100, 1, "call")),
                               (p, p.OptionContract(100, 1, "call", "european"))):
            for bad in (float("nan"), float("inf"), -1):
                with self.assertRaises(ValueError):
                    engine.price_option_monte_carlo(engine.MarketData(100, .05, bad), option, 2)
            for bad_count in (True, 1, 2.5):
                with self.assertRaises(ValueError):
                    engine.price_option_monte_carlo(engine.MarketData(100, .05, .2), option, bad_count)
        for barrier in (None, float("nan"), 90):
            with self.assertRaises(ValueError):
                p.price_option_monte_carlo(p.MarketData(100, .05, .2),
                    p.OptionContract(100, 1, "call", "UP_AND_OUT_BARRIER", barrier), 2, 1)


if __name__ == "__main__":
    unittest.main()
