
import ast
from contextlib import redirect_stdout
from dataclasses import asdict
from importlib.util import find_spec
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import monte_carlo_demo as standalone
import option_pricing as modular


class SingleFileTests(unittest.TestCase):
    def test_no_project_imports(self):
        tree = ast.parse(Path(standalone.__file__).read_text(encoding="utf-8"))
        forbidden = {"pricing_common", "pricing_kernels", "advanced_pricing", "greeks",
                     "variance_reduction", "option_pricing", "visualize_outcomes"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, forbidden)
            if isinstance(node, ast.Import):
                for name in node.names:
                    self.assertNotIn(name.name, forbidden)

    def test_seeded_outputs_match_for_all_products(self):
        backends = ["python", "numpy"] if find_spec("numpy") else ["python"]
        for engine, products in (("terminal", ["european"]),
                                 ("path", ["european", "asian", "up_and_out_barrier"])):
            for product in products:
                for kind in ("call", "put"):
                    for backend in backends:
                        with self.subTest(engine=engine, product=product, kind=kind, backend=backend):
                            config = modular.Configuration(engine=engine, product=product, option_type=kind,
                                backend=backend, simulations=300, time_steps=12, batch_size=64,
                                barrier=130 if product == "up_and_out_barrier" else None)
                            before = modular.run_pricing(config)
                            after = standalone.run_pricing(standalone.Configuration(**asdict(config)))
                            before.pop("elapsed_seconds")
                            after.pop("elapsed_seconds")
                            self.assertEqual(before, after)

    @unittest.skipUnless(find_spec("numpy"), "Optional NumPy unavailable")
    def test_advanced_seeded_outputs_match(self):
        for product in ("european", "asian", "up_and_out_barrier"):
            for method in ("none", "antithetic", "control", "both"):
                for kind in ("call", "put"):
                    with self.subTest(product=product, method=method, kind=kind):
                        config = modular.Configuration(engine="path", product=product, option_type=kind,
                            variance_reduction=method, greeks=True, simulations=300, pilot_simulations=100,
                            time_steps=12, batch_size=64, barrier=130 if product == "up_and_out_barrier" else None)
                        before = modular.run_pricing(config)
                        after = standalone.run_pricing(standalone.Configuration(**asdict(config)))
                        before.pop("elapsed_seconds")
                        after.pop("elapsed_seconds")
                        self.assertEqual(before, after)

    def test_shared_models_and_validation(self):
        self.assertIs(standalone.load_engine("terminal").MarketData, standalone.load_engine("path").MarketData)
        self.assertIs(standalone.load_engine("terminal").PricingResult, standalone.load_engine("path").PricingResult)
        with self.assertRaises(ValueError):
            standalone.run_pricing(standalone.Configuration(engine="terminal", product="asian"))

    def test_interactive_main(self):


        answers = ["1", "1", "100", "100", "1", ".05", ".2", "0", "20", "42", "1", "1", "1", "1"]
        with patch("builtins.input", side_effect=answers), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(standalone.main([]), 0)
        self.assertIn("Option price:", output.getvalue())

    def test_standalone_copy_runs_without_project_files(self):
        with TemporaryDirectory() as directory:
            script = Path(directory) / "monte_carlo_demo.py"
            shutil.copyfile(standalone.__file__, script)
            report = Path(directory) / "report.json"
            process = subprocess.run([sys.executable, "-I", str(script), "--engine", "path",
                "--product", "asian", "--simulations", "100", "--time-steps", "12",
                "--backend", "python", "--report", str(report)], cwd=directory,
                capture_output=True, text=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(report.read_text())["configuration"]["product"], "asian")


if __name__ == "__main__":
    unittest.main()
