
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import time


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    terminal = load("benchmark_terminal", "monte carlos pricing engine_terminal engine.py")
    path = load("benchmark_path", "monte carlo option pricing engine_path based engine.py")
    backends = ["python"]
    if importlib.util.find_spec("numpy"):
        import numpy
        backends.append("numpy")
    cases = [("terminal", terminal, terminal.EuropeanOption(100, 1, "call"), 100000, {})]
    cases += [(f"path_{product.removeprefix('up_and_out_')}", path,
               path.OptionContract(100, 1, "call", product, 130), 10000, {"time_steps": 252})
              for product in ("european", "asian", "up_and_out_barrier")]
    results = {}
    for name, engine, option, count, kwargs in cases:
        results[name] = {}
        for backend in backends:
            timings = []
            for _ in range(3):
                start = time.perf_counter()
                result = engine.price_option_monte_carlo(engine.MarketData(100, .05, .2),
                    option, count, backend=backend, **kwargs)
                timings.append(time.perf_counter() - start)
            results[name][backend] = dict(seconds=statistics.median(timings),
                                         price=result.price, standard_error=result.standard_error)
    output = json.dumps(results, indent=2)
    Path(__file__).with_name("benchmark_after.json").write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
