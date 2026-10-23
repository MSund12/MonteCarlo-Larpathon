# run_demo.ps1 — explanation

Source: [run_demo.ps1](../../run_demo.ps1)

- Resolve the demo path from PSScriptRoot so the launcher can find it when called from a different folder.
- Use the bundled Python runtime when available. Otherwise use python from PATH so the launcher also works on another machine with Python installed.
- Add .visualization-deps to PYTHONPATH only when the directory exists. This makes optional local plotting libraries available without requiring a global installation.
- Forward arguments with @args so command-line options reach the demo unchanged.
- Restore the original PYTHONPATH in finally, including when execution fails. Return the demo’s exit code to the calling shell.

Related files: [explanation index](README.md).
