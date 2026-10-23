
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from option_pricing import Configuration, interactive_configuration, main, run_pricing


class DemoTests(unittest.TestCase):
    def test_all_supported_engine_product_and_payoff_combinations(self):
        for engine, products in (("terminal", ["european"]),
                                 ("path", ["european", "asian", "up_and_out_barrier"])):
            for product in products:
                for kind in ("call", "put"):
                    with self.subTest(engine=engine, product=product, kind=kind):
                        config = Configuration(engine=engine, product=product, option_type=kind,
                            barrier=130 if product == "up_and_out_barrier" else None,
                            simulations=100, time_steps=12, backend="python")
                        result = run_pricing(config)
                        self.assertGreaterEqual(result["result"]["price"], 0)
                        self.assertEqual(result["result"]["simulations"], 100)
                        self.assertEqual(result["black_scholes_price"] is not None, product == "european")

    def test_terminal_rejects_path_dependent_contracts(self):
        with self.assertRaisesRegex(ValueError, "require the path engine"):
            run_pricing(Configuration(product="asian"))

    def test_report_export(self):
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()):
            path = Path(directory) / "report.json"
            code = main(["--engine", "path", "--product", "asian", "--type", "put",
                         "--simulations", "20", "--time-steps", "5", "--report", str(path)])
            self.assertEqual(code, 0)
            report = json.loads(path.read_text())
            self.assertEqual(report["configuration"]["option_type"], "put")
            self.assertEqual(report["configuration"]["product"], "asian")

    def test_interactive_menu_and_invalid_input_retry(self):
        answers = ["bad", "2", "3", "2", "-1", "100", "100", "1", ".05", ".2", "0",
                   "90", "130", "20", "12", "42", "2"]
        with patch("builtins.input", side_effect=answers), redirect_stdout(StringIO()):
            config = interactive_configuration()
        self.assertEqual(config.engine, "path")
        self.assertEqual(config.product, "up_and_out_barrier")
        self.assertEqual(config.option_type, "put")
        self.assertEqual(config.barrier, 130)
        self.assertEqual(config.backend, "python")

    def test_friendly_error(self):
        output = StringIO()
        with redirect_stderr(output):
            self.assertEqual(main(["--engine", "terminal", "--product", "asian"]), 1)
        self.assertIn("require the path engine", output.getvalue())

    @unittest.skipUnless(__import__("importlib.util").util.find_spec("numpy"), "NumPy optional")
    def test_advanced_cli_selection(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main(["--engine", "path", "--product", "asian", "--simulations", "100",
                         "--time-steps", "12", "--variance-reduction", "both", "--greeks"])
        self.assertEqual(code, 0)
        self.assertIn("Independent observations: 50", output.getvalue())
        self.assertIn("Vega", output.getvalue())


if __name__ == "__main__":
    unittest.main()
