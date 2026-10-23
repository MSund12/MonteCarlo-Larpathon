
from pathlib import Path
import sys


def render_report(config, report, output="outcomes.png", show=False, sample_size=5000):

    from pricing_common import validate_count
    from option_pricing import contracts
    validate_count(sample_size, "chart_simulations", 2)
    try:
        import numpy as np
        import matplotlib
        if not show:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError("Charts require NumPy and Matplotlib. Run: python -m pip install -r requirements-visualization.txt") from exc
    engine, market, option = contracts(config)


    chart_seed = config.seed + 1
    paths = None
    if config.engine == "terminal":
        terminal = np.asarray(engine.simulate_terminal_stock_prices(market, option, sample_size, chart_seed))
        payoffs = np.asarray(engine.calculate_payoffs(terminal, option))
    else:


        path_sample = []
        terminal, payoffs = np.empty(sample_size), np.empty(sample_size)
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
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout="constrained")
    ax = axes[0, 0]
    if paths is not None:
        times = np.linspace(0, config.maturity, paths.shape[1])
        p05, median, p95 = np.percentile(paths, [5, 50, 95], axis=0)
        ax.plot(times, paths[:60].T, alpha=.25, linewidth=.6)
        ax.fill_between(times, p05, p95, color="royalblue", alpha=.17, label="5th–95th percentiles")
        ax.plot(times, median, color="navy", label="Median")
        ax.axhline(config.strike, color="black", linestyle=":", label="Strike")
        if config.product == "up_and_out_barrier":
            ax.axhline(config.barrier, color="red", linestyle="--", label="Knockout barrier")
        ax.set(title=f"Paths: showing {min(60, len(paths))}; band from {len(paths):,}", xlabel="Years", ylabel="Stock price ($)")
    else:
        expiry = np.linspace(min(terminal.min(), config.strike * .5), max(terminal.max(), config.strike * 1.5), 250)
        direction = 1 if config.option_type == "call" else -1
        ax.plot(expiry, np.maximum(direction * (expiry - config.strike), 0), color="navy", label=f"{config.option_type.title()} payoff")
        ax.axvline(config.strike, color="black", linestyle=":", label="Strike")
        ax.set(title="Terminal engine: payoff at expiry", xlabel="Stock price at expiry ($)", ylabel="Payoff ($)")
    ax.legend(fontsize=8)
    axes[0, 1].hist(terminal, bins=60, color="royalblue", alpha=.8)
    axes[0, 1].set(title="Diagnostic terminal prices", xlabel="Stock price at expiry ($)", ylabel="Number of scenarios")
    axes[1, 0].hist(payoffs, bins=60, color="teal", alpha=.8)
    axes[1, 0].set(title="Diagnostic discounted payoffs", xlabel="Present value of payoff ($)", ylabel="Number of scenarios")
    ax = axes[1, 1]

    start = min(99, sample_size - 2)
    ax.plot(count[start:], running[start:], color="navy", label="Diagnostic sample mean")
    indices = np.arange(max(start, 1), sample_size)
    ax.fill_between(count[indices], running[indices] - 1.96 * se[indices - 1],
                    running[indices] + 1.96 * se[indices - 1], alpha=.2,
                    label="Approximate 95% sample CI")
    ax.axhline(report["result"]["price"], color="darkorange", linestyle="--", label="Full pricing run estimate")
    ax.set(title="Diagnostic convergence", xlabel="Diagnostic scenarios", ylabel="Option price ($)")
    ax.legend(fontsize=8)
    fig.suptitle(f"{config.engine} engine | {config.product} {config.option_type}\n"
                 f"Separate diagnostic sample: {sample_size:,}, seed {chart_seed} | Risk-neutral scenarios")
    if getattr(config, "variance_reduction", "none") != "none" or getattr(config, "greeks", False):
        fig.supxlabel("Diagnostic samples use plain MC; their band is not the enhanced estimator's confidence interval.", fontsize=9)
    try:
        fig.savefig(output, dpi=150)
        print(f"Chart saved: {Path(output).resolve()}")
        if show:
            plt.show()
    finally:
        plt.close(fig)
    return Path(output)


def main():
    from option_pricing import main as unified_main
    return unified_main(["--engine", "path", "--chart", "outcomes.png", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
