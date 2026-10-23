# benchmark_pricing.py — explanation

Source: [benchmark_pricing.py](../../benchmark_pricing.py)

## What is happening and why

- Compare terminal European and path European, Asian and barrier cases using fixed market inputs. Include NumPy only when it is installed.
- Import NumPy before timing so its initial import cost does not dominate the comparison. Run each case three times and report the median elapsed time.
- Save timings, prices and standard errors to benchmark_after.json. These timings depend on the machine and environment; the saved before/after reports are historical measurements.

## Definitions in the code

- [`load`](../../benchmark_pricing.py#L10)
- [`main`](../../benchmark_pricing.py#L18)

## Explanations moved out of the source

- **File purpose:** Reproducible timing comparison: python benchmark_pricing.py (NumPy optional).
- **Source line 23 when extracted:** Warm import before timing.

Related files: [explanation index](README.md).
