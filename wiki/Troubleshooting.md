# Troubleshooting

Run the existing tests from the repository folder:

```powershell
python -m unittest discover -v
```

- Checks include analytical European prices, explicit-versus-streaming payoffs, batch statistics, antithetic sample accounting, independent pilot fitting, Greek calculations, report export, and standalone/modular agreement.
- Tests requiring optional dependencies can be skipped when those dependencies are unavailable. Read the final test summary.
- **Python is not found:** install or select Python 3.10+, then run from an environment where its executable is available.
- **NumPy or Matplotlib is missing:** install the requirements using the interpreter that runs the demo.
- **Asian/barrier contract rejected by terminal engine:** select `--engine path`.
- **Barrier rejected:** supply a finite barrier strictly above spot.
- **Enhancements rejected with Python backend:** install NumPy and select `auto` or `numpy`.
- **Chart differs from the reported price:** check the separate diagnostic sample size and remember that diagnostic intervals belong to that sample.
- **Results change after changing backend or batch size:** those settings can change which random draws reach each simulated path, even with the same seed.
- **GitHub Desktop shows no local changes:** committed files are visible through History or by opening the repository in an editor. Fetch and pull to download newer remote commits.

## Investigating unexpected results

Check units, call/put direction, maturity, and dates first. Then examine standard error and independent sample counts. Increase simulations or vary the seed to investigate sampling noise. For European contracts, compare against the analytical benchmark with identical inputs.

For unstable Greeks, vary bumps and sample count together. Barrier survival or knockout events can be rare and sensitive to monitoring dates. Zero observed positive payoffs do not prove a true value of zero. Review Model Assumptions before treating a difference as a software defect.

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
