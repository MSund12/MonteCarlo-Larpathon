




import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCES = [
    ("VALIDATION AND STREAMING STATISTICS", "pricing_common.py", {}),
    ("CONTROL VARIATES AND ESTIMATOR MOMENTS", "variance_reduction.py", {}),
    ("GREEK SCENARIOS", "greeks.py", {}),
    ("ADVANCED ESTIMATOR", "advanced_pricing.py", {}),
    ("BASIC MONTE CARLO KERNELS", "pricing_kernels.py", {"price": "price_kernel"}),
    ("SHARED MODELS AND TERMINAL ENGINE", "monte carlos pricing engine_terminal engine.py", {
        "validate_inputs": "terminal_validate_inputs",
        "simulate_terminal_stock_prices": "simulate_terminal_stock_prices",
        "calculate_payoff": "terminal_calculate_payoff",
        "calculate_payoffs": "terminal_calculate_payoffs",
        "price_option_monte_carlo": "terminal_price_option_monte_carlo",
        "print_pricing_summary": "terminal_print_pricing_summary",
    }),
    ("PATH ENGINE", "monte carlo option pricing engine_path based engine.py", {
        "validate_inputs": "path_validate_inputs",
        "price_option_monte_carlo": "path_price_option_monte_carlo",
        "print_pricing_summary": "path_print_pricing_summary",
    }),
    ("CONFIGURATION, MENUS, AND REPORTING", "option_pricing.py", {}),
    ("OPTIONAL VISUALIZATION", "visualize_outcomes.py", {}),
]
PROJECT_MODULES = {"pricing_common", "variance_reduction", "greeks", "advanced_pricing",
                   "pricing_kernels", "option_pricing", "visualize_outcomes"}

LOADER = '''
@lru_cache(maxsize=2)
def load_engine(name):
    shared = dict(MarketData=MarketData, PricingResult=PricingResult)
    if name == "terminal":
        return SimpleNamespace(**shared, EuropeanOption=EuropeanOption,
            validate_inputs=terminal_validate_inputs,
            simulate_terminal_stock_prices=simulate_terminal_stock_prices,
            calculate_payoff=terminal_calculate_payoff,
            calculate_payoffs=terminal_calculate_payoffs,
            price_option_monte_carlo=terminal_price_option_monte_carlo,
            normal_cdf=normal_cdf, black_scholes_price=black_scholes_price,
            print_pricing_summary=terminal_print_pricing_summary)
    if name == "path":
        return SimpleNamespace(**shared, OptionContract=OptionContract,
            validate_inputs=path_validate_inputs, iter_price_paths=iter_price_paths,
            simulate_price_paths=simulate_price_paths, vanilla_payoff=vanilla_payoff,
            european_payoff=european_payoff, asian_payoff=asian_payoff,
            up_and_out_barrier_payoff=up_and_out_barrier_payoff,
            calculate_path_payoff=calculate_path_payoff,
            price_option_monte_carlo=path_price_option_monte_carlo,
            print_pricing_summary=path_print_pricing_summary)
    raise ValueError("Engine must be 'terminal' or 'path'.")
'''


class Consolidate(ast.NodeTransformer):
    def __init__(self, names):
        self.names = names

    def visit_Name(self, node):
        node.id = self.names.get(node.id, node.id)
        return node

    def visit_FunctionDef(self, node):
        node.name = self.names.get(node.name, node.name)
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        return None if node.module in PROJECT_MODULES else node


def build():
    output = ['from types import SimpleNamespace\n']
    for title, filename, names in SOURCES:
        tree = ast.parse((ROOT / filename).read_text(encoding="utf-8-sig"))
        nodes = []
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                continue
            if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test):
                continue
            if isinstance(node, ast.FunctionDef) and node.name == "main" and filename != "option_pricing.py":
                continue
            if filename.startswith("monte carlo option") and isinstance(node, ast.ClassDef) and node.name in {"MarketData", "PricingResult"}:
                continue
            if filename == "option_pricing.py" and isinstance(node, ast.FunctionDef) and node.name == "load_engine":
                nodes.extend(ast.parse(LOADER).body)
                continue
            transformed = Consolidate(names).visit(node)
            if transformed is not None:
                nodes.append(transformed)
        output.append(ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))) + "\n")
    output.append('\nif __name__ == "__main__":\n    raise SystemExit(main())\n')
    class RemoveExplanations(ast.NodeTransformer):
        def clean(self, node):
            self.generic_visit(node)
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
                if not node.body:
                    node.body.append(ast.Pass())
            return node

        visit_Module = clean
        visit_ClassDef = clean
        visit_FunctionDef = clean
        visit_AsyncFunctionDef = clean

    tree = RemoveExplanations().visit(ast.parse("\n".join(output)))
    text = ast.unparse(ast.fix_missing_locations(tree)) + "\n"
    compile(text, "monte_carlo_demo.py", "exec")
    path = ROOT / "monte_carlo_demo.py"
    path.write_text(text, encoding="utf-8")
    print(f"Created {path} ({len(text.splitlines()):,} lines)")


if __name__ == "__main__":
    build()
