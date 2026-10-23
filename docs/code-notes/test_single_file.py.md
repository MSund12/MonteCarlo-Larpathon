# test_single_file.py — explanation

Source: [test_single_file.py](../../test_single_file.py)

## What is happening and why

- Inspect the standalone syntax tree for internal project imports. The generated application must not depend on the preserved modular files.
- Compare seeded standalone and modular results for every supported product and payoff type, and for both Python and NumPy when available. Remove elapsed time before equality checks because timing is not deterministic.
- Repeat the comparison with Greeks and each variance-reduction mode. This checks that consolidation preserves the statistical calculation as well as basic pricing.
- Check that both standalone engines share the same model classes and reject an incompatible terminal/Asian configuration.
- Mock menu input to exercise the standalone interactive entry point and check that it prints an option price.
- Copy only monte_carlo_demo.py to a temporary directory and run it with Python isolated mode (-I). Successful Asian pricing and JSON export demonstrate independence from other project files and PYTHONPATH.

## Definitions in the code

- [`SingleFileTests`](../../test_single_file.py#L20)
- [`test_no_project_imports`](../../test_single_file.py#L21)
- [`test_seeded_outputs_match_for_all_products`](../../test_single_file.py#L32)
- [`test_advanced_seeded_outputs_match`](../../test_single_file.py#L50)
- [`test_shared_models_and_validation`](../../test_single_file.py#L64)
- [`test_interactive_main`](../../test_single_file.py#L70)
- [`test_standalone_copy_runs_without_project_files`](../../test_single_file.py#L78)

## Explanations moved out of the source

- **File purpose:** Prove the consolidated application matches and runs without modular files.
- **Source line 71 when extracted:** Defaults choose terminal, European, call and automatic backend. The last
- **Source line 72 when extracted:** selections disable enhancements and charts for a fast complete run.

Related files: [explanation index](README.md).
