# test_demo.py — explanation

Source: [test_demo.py](../../test_demo.py)

## What is happening and why

- Run every supported engine, product and call/put combination with small deterministic runs. Check nonnegative prices, requested simulation counts and availability of European benchmarks.
- Provide invalid menu selections and then valid replacements through mocked input. Check that retrying produces the intended barrier put configuration.
- Export an Asian put report into a temporary directory, read the JSON back, and check that the selected product and option type survived export.
- Check incompatible terminal/Asian input both as a Python error and as a command-line error with exit code 1.
- Run the advanced command-line selection with both variance-reduction methods and Greeks. Check that 100 physical antithetic paths are reported as 50 independent observations.

## Definitions in the code

- [`DemoTests`](../../test_demo.py#L13)
- [`test_all_supported_engine_product_and_payoff_combinations`](../../test_demo.py#L14)
- [`test_terminal_rejects_path_dependent_contracts`](../../test_demo.py#L28)
- [`test_report_export`](../../test_demo.py#L32)
- [`test_interactive_menu_and_invalid_input_retry`](../../test_demo.py#L42)
- [`test_friendly_error`](../../test_demo.py#L53)
- [`test_advanced_cli_selection`](../../test_demo.py#L60)

## Explanations moved out of the source

- **File purpose:** Integration checks for the unified selection and execution workflow.

Related files: [explanation index](README.md).
