
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
    filenames = {
        "terminal": "monte carlos pricing engine_terminal engine.py",
        "path": "monte carlo option pricing engine_path based engine.py",
    }
    if name not in filenames:
        raise ValueError("Engine must be 'terminal' or 'path'.")
    spec = importlib.util.spec_from_file_location(f"demo_{name}_engine",
                                                 Path(__file__).with_name(filenames[name]))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class Configuration:
    engine: str = "terminal"
    product: str = "european"
    option_type: str = "call"
    spot: float = 100.0
    strike: float = 100.0
    maturity: float = 1.0
    rate: float = .05
    volatility: float = .2
    dividend: float = 0.0
    barrier: float | None = None
    simulations: int = 50000
    time_steps: int = 252
    seed: int = 42
    backend: str = "auto"
    batch_size: int = 8192
    variance_reduction: str = "none"
    greeks: bool = False
    pilot_simulations: int = 2048
    spot_bump: float = .005
    volatility_bump: float = .001
    rate_bump: float = .0001
    maturity_bump: float = 1 / 365


def contracts(config):
    if config.engine == "terminal" and config.product != "european":
        raise ValueError("Asian and barrier options require the path engine.")
    engine = load_engine(config.engine)
    market = engine.MarketData(config.spot, config.rate, config.volatility, config.dividend)
    if config.engine == "terminal":
        option = engine.EuropeanOption(config.strike, config.maturity, config.option_type)
        engine.validate_inputs(market, option, config.simulations)
    else:
        option = engine.OptionContract(config.strike, config.maturity, config.option_type,
                                       config.product, config.barrier)
        engine.validate_inputs(market, option, config.simulations, config.time_steps)
    return engine, market, option


def run_pricing(config):
    if config.backend not in {"auto", "numpy", "python"}:
        raise ValueError("backend must be auto, numpy, or python.")
    engine, market, option = contracts(config)
    kwargs = dict(simulations=config.simulations, seed=config.seed,
                  backend=config.backend, batch_size=config.batch_size)
    if config.engine == "path":
        kwargs["time_steps"] = config.time_steps
    start = perf_counter()
    advanced = None
    if config.greeks or config.variance_reduction != "none":
        if config.backend == "python":
            raise ValueError("Greeks and variance reduction require NumPy; select auto or numpy.")
        from advanced_pricing import estimate
        advanced = estimate(market, option, config.simulations, config.time_steps, config.seed,
            config.batch_size, config.variance_reduction, config.greeks, config.pilot_simulations,
            config.spot_bump, config.volatility_bump, config.rate_bump, config.maturity_bump)
        result = advanced["result"]
    else:
        result = asdict(engine.price_option_monte_carlo(market, option, **kwargs))
    elapsed = perf_counter() - start
    benchmark = None
    if config.product == "european":
        benchmark = load_engine("terminal").black_scholes_price(market, option)
    backend = config.backend
    if backend == "auto":
        backend = "numpy" if importlib.util.find_spec("numpy") else "python"
    report = dict(configuration=asdict(config), backend_used=backend, result=result,
                  black_scholes_price=benchmark, elapsed_seconds=elapsed)
    if advanced is not None:
        report.update({key: advanced[key] for key in ("greeks", "estimator", "notes")})
    return report


def print_report(report):
    config, result = report["configuration"], report["result"]
    print("\n" + "=" * 62)
    print(f"{config['engine'].upper()} ENGINE | {config['product']} {config['option_type']}")
    print(f"Spot {config['spot']:g} | Strike {config['strike']:g} | Maturity {config['maturity']:g} years")
    print(f"Simulations: {result['simulations']:,} | Backend: {report['backend_used']}")
    if config["engine"] == "path" and config["product"] != "european":
        print(f"Monitoring dates: {config['time_steps']:,}")
    if config["product"] == "up_and_out_barrier":
        print(f"Up-and-out barrier: ${config['barrier']:.2f} (discrete monitoring)")
    print(f"Option price:       ${result['price']:.6f}")
    print(f"Standard error:     ${result['standard_error']:.6f}")
    print(f"Approximate 95% CI: ${result['confidence_interval_low']:.6f} to ${result['confidence_interval_high']:.6f}")
    if report["black_scholes_price"] is not None:
        print(f"Black-Scholes:      ${report['black_scholes_price']:.6f}")
    if "estimator" in report:
        estimator = report["estimator"]
        print(f"Estimator: {estimator['method']} | Independent observations: {estimator['independent_samples']:,}")
        if estimator["pilot_paths"]:
            print(f"Additional pilot paths: {estimator['pilot_paths']:,} (excluded from price and CI)")
            print(f"Control: {estimator['control_name']}")
            print(f"SE before/after control: {estimator['unadjusted_standard_error']:.6f} / {result['standard_error']:.6f}")
        if report["greeks"]:
            print("\nGreeks - finite differences with shared random numbers")
            for name, greek in report["greeks"].items():
                print(f"  {name.title():5}: {greek['estimate']: .6f} | SE {greek['standard_error']:.6f} | "
                      f"95% CI [{greek['confidence_interval_low']:.6f}, {greek['confidence_interval_high']:.6f}]")
                print(f"         {greek['unit']}")
        for note in report["notes"]:
            print(f"Note: {note}")
    print(f"Pricing time:       {report['elapsed_seconds']:.4f} seconds")
    print("=" * 62)


def choose(label, choices, default=1):
    print(f"\n{label}")
    for i, (title, value) in enumerate(choices, 1):
        print(f"  {i}. {title}")
    while True:
        answer = input(f"Selection [{default}]: ").strip() or str(default)
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1][1]
        print(f"Enter a number from 1 to {len(choices)}.")


def number(label, default, integer=False, minimum=None, strict=False):
    while True:
        answer = input(f"{label} [{default}]: ").strip() or str(default)
        try:
            value = int(answer) if integer else float(answer)
            if not isfinite(value) or (minimum is not None and
                    (value <= minimum if strict else value < minimum)):
                raise ValueError
            return value
        except ValueError:
            bound = "" if minimum is None else f" {'greater than' if strict else 'at least'} {minimum}"
            print(f"Enter a finite {'integer' if integer else 'number'}{bound}.")


def interactive_configuration():
    print("MONTE CARLO OPTION PRICING DEMO")
    config = Configuration()
    config.engine = choose("Choose pricing engine", [
        ("Terminal — European options using the expiry price", "terminal"),
        ("Path based — European, Asian, or up-and-out barrier", "path")])
    if config.engine == "path":
        config.product = choose("Choose option product", [
            ("European", "european"), ("Arithmetic-average Asian", "asian"),
            ("Up-and-out barrier", "up_and_out_barrier")])
    config.option_type = choose("Choose option type", [("Call", "call"), ("Put", "put")])
    config.spot = number("Spot price", 100, minimum=0, strict=True)
    config.strike = number("Strike price", 100, minimum=0, strict=True)
    config.maturity = number("Maturity in years", 1, minimum=0, strict=True)
    print("Enter annual rates as decimals: 0.05 = 5%; 0.20 = 20% volatility.")
    config.rate = number("Risk-free rate", .05)
    config.volatility = number("Volatility", .20, minimum=0)
    config.dividend = number("Dividend yield", 0)
    if config.product == "up_and_out_barrier":
        config.barrier = number("Barrier price", round(config.spot * 1.3, 4),
                                minimum=config.spot, strict=True)
    config.simulations = number("Simulations", 50000, integer=True, minimum=2)
    if config.engine == "path":
        config.time_steps = number("Total monitoring dates over maturity", 252, integer=True, minimum=1)
    config.seed = number("Random seed", 42, integer=True, minimum=0)
    config.backend = choose("Calculation backend", [("Automatic (NumPy when available)", "auto"),
                                                    ("Python standard library", "python"), ("NumPy", "numpy")])
    if config.backend != "python":
        config.variance_reduction = choose("Variance reduction (requires NumPy)", [
            ("None — plain Monte Carlo", "none"), ("Antithetic pairs", "antithetic"),
            ("Control variate with separate pilot", "control"), ("Antithetic + control variate", "both")])
        if config.variance_reduction in {"antithetic", "both"}:
            while config.simulations < 4 or config.simulations % 2:
                print("Antithetic sampling needs an even number of physical paths, at least 4.")
                config.simulations = number("Simulations", 50000, integer=True, minimum=4)
        config.greeks = choose("Calculate Greeks (extra computation)", [("No", False), ("Yes", True)])
    return config


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--interactive", action="store_true")
    result.add_argument("--engine", choices=["terminal", "path"], default="terminal")
    result.add_argument("--product", choices=["european", "asian", "up_and_out_barrier"], default="european")
    result.add_argument("--type", dest="option_type", choices=["call", "put"], default="call")
    for name, default in [("spot", 100), ("strike", 100), ("maturity", 1), ("rate", .05),
                          ("volatility", .2), ("dividend", 0)]:
        result.add_argument(f"--{name}", type=float, default=default)
    result.add_argument("--barrier", type=float)
    result.add_argument("--simulations", type=int, default=50000)
    result.add_argument("--time-steps", type=int, default=252)
    result.add_argument("--seed", type=int, default=42)
    result.add_argument("--backend", choices=["auto", "python", "numpy"], default="auto")
    result.add_argument("--batch-size", type=int, default=8192)
    result.add_argument("--variance-reduction", choices=["none", "antithetic", "control", "both"], default="none")
    result.add_argument("--greeks", action="store_true", help="Estimate Delta, Gamma, Vega, Rho and Theta")
    result.add_argument("--pilot-simulations", type=int, default=2048,
                        help="Additional independent paths for control fitting")
    result.add_argument("--spot-bump", type=float, default=.005, help="Relative spot bump for Delta/Gamma")
    result.add_argument("--volatility-bump", type=float, default=.001)
    result.add_argument("--rate-bump", type=float, default=.0001)
    result.add_argument("--maturity-bump", type=float, default=1 / 365)
    result.add_argument("--chart", "--output", dest="chart", help="Save a PNG diagnostic chart")
    result.add_argument("--show", action="store_true", help="Open the chart window")
    result.add_argument("--chart-simulations", type=int, default=5000,
                        help="Independent diagnostic sample size (default: 5000)")
    result.add_argument("--report", help="Save inputs and pricing results as JSON")
    return result


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    args = parser().parse_args(arguments)
    interactive = args.interactive or not arguments
    try:
        config = interactive_configuration() if interactive else Configuration(**{
            name: getattr(args, name) for name in Configuration.__dataclass_fields__})
        report = run_pricing(config)
        print_report(report)
        if args.report:
            Path(args.report).write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            print(f"Report saved: {Path(args.report).resolve()}")
        chart = args.chart
        if interactive and not chart:
            chart = choose("Visualization", [("Skip charts", None),
                                              ("Save charts to outcomes.png", "outcomes.png")])
        if chart or args.show:
            from visualize_outcomes import render_report
            render_report(config, report, chart or "outcomes.png", args.show, args.chart_simulations)
        return 0
    except (ValueError, ImportError, OSError, OverflowError, FloatingPointError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nDemo closed.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
