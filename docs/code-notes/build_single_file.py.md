# build_single_file.py — explanation

Source: [build_single_file.py](../../build_single_file.py)

## What is happening and why

- Parse modular sources into Python syntax trees rather than join their text blindly. Remove internal project imports and duplicate shared model definitions.
- Rename overlapping terminal and path functions before merging. Replace the dynamic engine loader with a SimpleNamespace pointing at functions already in the standalone file.
- Exclude secondary main functions and module entry-point blocks. Keep the unified application main so the generated file has one user-facing entry point.
- Remove explanatory docstrings from the generated syntax tree and let ast.unparse write comment-free code. This keeps a future rebuild consistent with the companion-document layout.
- Compile the generated text before saving. Rebuilding explicitly overwrites monte_carlo_demo.py; edits intended to survive regeneration belong in the modular source.

## Definitions in the code

- [`Consolidate`](../../build_single_file.py#L62)
- [`build`](../../build_single_file.py#L78)
- [`__init__`](../../build_single_file.py#L63)
- [`visit_Name`](../../build_single_file.py#L66)
- [`visit_FunctionDef`](../../build_single_file.py#L70)
- [`visit_ImportFrom`](../../build_single_file.py#L74)
- [`RemoveExplanations`](../../build_single_file.py#L100)
- [`clean`](../../build_single_file.py#L101)

## Explanations moved out of the source

- **File purpose:** Build a readable, standalone demo from the preserved modular implementation. This is a development tool, not a runtime dependency. It removes project imports, resolves duplicate engine names, and writes ordinary Python definitions.
- **Source line 104 when extracted:** Section headers replace redundant module docstrings.
- **Source line 110 when extracted:** Identical models are defined once in the merged file.

Related files: [explanation index](README.md).
