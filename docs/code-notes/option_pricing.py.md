# option_pricing.py — explanation

Source: [option_pricing.py](../../option_pricing.py)

## What is happening and why

- Keep all selected inputs in Configuration so interactive menus, command-line runs, JSON reports and charts use the same contract settings.
- Load the older engine filenames through importlib because their spaces prevent ordinary Python import statements. Cache each loaded engine to avoid repeating setup.
- Validate engine-product compatibility before pricing. European options work with either engine; Asian and barrier products require the path engine.
- Send basic requests to the selected engine and requests with Greeks or variance reduction to the NumPy estimator. Explicitly reject the Python backend when enhancements require NumPy.
- Measure pricing time around the calculation, then build a report with inputs, results, backend information and an analytical benchmark where available.
- Use argparse for repeatable non-interactive commands, and prompt for values when no arguments are supplied. Keep chart generation optional so basic pricing has fewer dependencies.

## Definitions in the code

- [`load_engine`](../../option_pricing.py#L14)
- [`Configuration`](../../option_pricing.py#L30)
- [`contracts`](../../option_pricing.py#L55)
- [`run_pricing`](../../option_pricing.py#L70)
- [`print_report`](../../option_pricing.py#L104)
- [`choose`](../../option_pricing.py#L138)
- [`number`](../../option_pricing.py#L149)
- [`interactive_configuration`](../../option_pricing.py#L163)
- [`parser`](../../option_pricing.py#L202)
- [`main`](../../option_pricing.py#L233)

## Explanations moved out of the source

- **File purpose:** Unified option-pricing demo. Run without arguments for interactive menus.

Related files: [explanation index](README.md).
