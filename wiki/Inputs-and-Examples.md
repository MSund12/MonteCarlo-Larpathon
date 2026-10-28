# Inputs and examples

| Input | Meaning | Default |
|---|---|---|
| Spot | Current underlying stock price | 100 |
| Strike | Contract's exercise price | 100 |
| Maturity | Time to expiry, in years | 1 |
| Rate | Annual continuously compounded risk-free rate, as a decimal | 0.05 |
| Volatility | Annual volatility, as a decimal | 0.20 |
| Dividend | Annual continuous dividend yield, as a decimal | 0 |
| Simulations | Number of physical production paths | 50,000 |
| Time steps | Total monitoring intervals over the full maturity | 252 |
| Seed | Starting value for the random generator | 42 |
| Backend | `auto`, `python`, or `numpy` | `auto` |

- Enter 5% as `0.05` and 20% as `0.20`.
- `auto` uses NumPy when available and the standard-library backend otherwise for basic pricing. Enhancements require NumPy.
- Time steps cover the entire contract: 252 steps over two years are not 252 steps per year.
- For repeatable results, keep the seed, backend, batch size, monitoring schedule, and relevant library versions fixed. Different backends need not produce identical samples.

European call with an exported report:

```powershell
python monte_carlo_demo.py --engine terminal --type call --simulations 100000 --report european_call.json
```

Asian call with 12 monitoring dates and a saved chart:

```powershell
python monte_carlo_demo.py --engine path --product asian --type call --time-steps 12 --chart asian_call.png --report asian_call.json
```

Barrier call with a $130 upper barrier:

```powershell
python monte_carlo_demo.py --engine path --product up_and_out_barrier --type call --barrier 130 --chart barrier_call.png
```

Use `--show` to display a chart and `--help` to list the available arguments. Relative output paths are resolved from the directory where the command is launched. Choose new output names to retain existing examples.

## Precision and fair comparisons

`--batch-size` defaults to 8192 and controls NumPy working batches. For ordinary independent Monte Carlo observations, halving standard error typically takes four times as many observations.

Keep contract terms and monitoring dates fixed when comparing estimators. Save separate reports and compare standard error, sample counts, and runtime alongside price. A higher or lower estimate alone does not indicate a better estimator. Record Greek bump sizes when comparing sensitivities.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
