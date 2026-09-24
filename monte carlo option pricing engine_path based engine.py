"""
Path-Based Monte Carlo Option Pricing Engine — Blueprint

Products supported:
    1. European options
    2. Asian options using arithmetic-average price
    3. Up-and-out barrier options

Run:
    python path_option_pricing_sketch.py

No external packages required.
"""

from dataclasses import dataclass
from math import exp, sqrt
from random import Random
from statistics import stdev

# 1. INPUT MODELS

@dataclass
class MarketData:
    spot_price: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0


@dataclass
class OptionContract:
    """
    product_type choices:
        "european"
        "asian"
        "up_and_out_barrier"

    option_type choices:
        "call"
        "put"

    barrier_price is only needed for up-and-out barrier options.
    """

    strike_price: float
    maturity_years: float
    option_type: str
    product_type: str

    barrier_price: float | None = None


@dataclass
class PricingResult:
    price: float
    standard_error: float
    confidence_interval_low: float
    confidence_interval_high: float
    simulations: int

# 2. INPUT VALIDATION

def validate_inputs(
    market: MarketData,
    option: OptionContract,
    simulations: int,
    time_steps: int
) -> None:

    valid_option_types = {"call", "put"}

    valid_product_types = {
        "european",
        "asian",
        "up_and_out_barrier"
    }

    if market.spot_price <= 0:
        raise ValueError("Spot price must be greater than zero.")

    if market.volatility < 0:
        raise ValueError("Volatility cannot be negative.")

    if option.strike_price <= 0:
        raise ValueError("Strike price must be greater than zero.")

    if option.maturity_years <= 0:
        raise ValueError("Maturity must be greater than zero.")

    if option.option_type.lower() not in valid_option_types:
        raise ValueError("Option type must be 'call' or 'put'.")

    if option.product_type.lower() not in valid_product_types:
        raise ValueError(
            "Product type must be 'european', 'asian', "
            "or 'up_and_out_barrier'."
        )

    if simulations < 2:
        raise ValueError("Use at least 2 simulations.")

    if time_steps < 1:
        raise ValueError("Use at least 1 time step.")

    if option.product_type == "up_and_out_barrier":
        if option.barrier_price is None:
            raise ValueError(
                "Barrier options require a barrier price."
            )

        if option.barrier_price <= market.spot_price:
            raise ValueError(
                "For this up-and-out example, the barrier "
                "must be above the current stock price."
            )

# 3. FULL STOCK-PRICE PATH SIMULATOR

def simulate_price_paths(
    market: MarketData,
    option: OptionContract,
    simulations: int,
    time_steps: int,
    seed: int | None = 42
) -> list[list[float]]:
    """
    Simulate many possible stock-price paths.

    Each path looks like:
        [S0, S1, S2, ..., ST]

    Example with 4 time steps:
        [100.00, 103.20, 98.50, 101.40, 107.80]

    Geometric Brownian Motion formula:
        S(t + dt) = S(t) * exp(
            (r - q - 0.5 * sigma^2) * dt
            + sigma * sqrt(dt) * Z
        )
    """

    rng = Random(seed)

    time_increment = option.maturity_years / time_steps

    risk_neutral_growth = (
        market.risk_free_rate
        - market.dividend_yield
        - 0.5 * market.volatility ** 2
    ) * time_increment

    volatility_step_size = (
        market.volatility * sqrt(time_increment)
    )

    all_paths = []

    for _ in range(simulations):
        current_path = [market.spot_price]
        current_stock_price = market.spot_price

        for _ in range(time_steps):
            random_normal_shock = rng.gauss(0, 1)

            current_stock_price *= exp(
                risk_neutral_growth
                + volatility_step_size * random_normal_shock
            )

            current_path.append(current_stock_price)

        all_paths.append(current_path)

    return all_paths

# 4. PAYOFF FUNCTIONS

def vanilla_payoff(
    stock_price: float,
    option: OptionContract
) -> float:
    """
    Standard European call/put payoff.
    """

    if option.option_type.lower() == "call":
        return max(stock_price - option.strike_price, 0.0)

    return max(option.strike_price - stock_price, 0.0)


def european_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:
    """
    European options only use the final stock price.
    """

    terminal_stock_price = price_path[-1]

    return vanilla_payoff(terminal_stock_price, option)


def asian_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:
    """
    Arithmetic-average Asian option.

    The initial stock price is excluded from the average.
    Only monitored future prices are included.
    """

    monitored_prices = price_path[1:]

    average_stock_price = (
        sum(monitored_prices) / len(monitored_prices)
    )

    return vanilla_payoff(average_stock_price, option)


def up_and_out_barrier_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:
    """
    If the stock price ever reaches or exceeds the barrier,
    the option becomes worthless ("knocked out").

    This is discrete monitoring: the barrier is checked at
    each simulated time step.
    """

    barrier_was_hit = any(
        stock_price >= option.barrier_price
        for stock_price in price_path
    )

    if barrier_was_hit:
        return 0.0

    terminal_stock_price = price_path[-1]

    return vanilla_payoff(terminal_stock_price, option)


def calculate_path_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:
    """
    Send each path to the correct payoff rule.
    """

    product_type = option.product_type.lower()

    if product_type == "european":
        return european_payoff(price_path, option)

    if product_type == "asian":
        return asian_payoff(price_path, option)

    if product_type == "up_and_out_barrier":
        return up_and_out_barrier_payoff(price_path, option)

    raise ValueError("Unsupported product type.")

# 5. MONTE CARLO PRICING ENGINE

def price_option_monte_carlo(
    market: MarketData,
    option: OptionContract,
    simulations: int = 50_000,
    time_steps: int = 252,
    seed: int | None = 42
) -> PricingResult:
    """
    Price any supported option product using full stock paths.

    252 time steps represents approximately one trading year
    of daily monitoring.
    """

    validate_inputs(
        market=market,
        option=option,
        simulations=simulations,
        time_steps=time_steps
    )

    simulated_paths = simulate_price_paths(
        market=market,
        option=option,
        simulations=simulations,
        time_steps=time_steps,
        seed=seed
    )

    path_payoffs = [
        calculate_path_payoff(path, option)
        for path in simulated_paths
    ]

    average_payoff = sum(path_payoffs) / simulations

    present_value_discount = exp(
        -market.risk_free_rate * option.maturity_years
    )

    estimated_price = (
        present_value_discount * average_payoff
    )

    payoff_standard_deviation = stdev(path_payoffs)

    standard_error = (
        present_value_discount
        * payoff_standard_deviation
        / sqrt(simulations)
    )

    confidence_interval_low = (
        estimated_price - 1.96 * standard_error
    )

    confidence_interval_high = (
        estimated_price + 1.96 * standard_error
    )

    return PricingResult(
        price=estimated_price,
        standard_error=standard_error,
        confidence_interval_low=confidence_interval_low,
        confidence_interval_high=confidence_interval_high,
        simulations=simulations
    )

# 6. RESULT DISPLAY

def print_pricing_summary(
    market: MarketData,
    option: OptionContract,
    result: PricingResult,
    time_steps: int
) -> None:

    print("\n" + "=" * 60)
    print("PATH-BASED MONTE CARLO OPTION PRICING ENGINE")
    print("=" * 60)

    print(f"Product:              {option.product_type}")
    print(f"Option type:          {option.option_type.upper()}")
    print(f"Spot price:           ${market.spot_price:.2f}")
    print(f"Strike price:         ${option.strike_price:.2f}")
    print(f"Maturity:             {option.maturity_years:.2f} years")
    print(f"Volatility:           {market.volatility:.2%}")
    print(f"Simulations:          {result.simulations:,}")
    print(f"Time steps per path:  {time_steps:,}")

    if option.barrier_price is not None:
        print(f"Barrier price:        ${option.barrier_price:.2f}")

    print("-" * 60)

    print(f"Monte Carlo price:    ${result.price:.4f}")
    print(f"Standard error:       ${result.standard_error:.4f}")

    print(
        "95% confidence interval: "
        f"${result.confidence_interval_low:.4f} "
        f"to ${result.confidence_interval_high:.4f}"
    )

    print("=" * 60 + "\n")

# 7. PROGRAM ENTRY POINT

def main() -> None:
    """
    Change only this section to test different contracts.
    """

    market = MarketData(
        spot_price=100.00,
        risk_free_rate=0.05,
        volatility=0.20,
        dividend_yield=0.00
    )

    option = OptionContract(
        strike_price=100.00,
        maturity_years=1.00,
        option_type="call",
        product_type="asian"

        # For a barrier option, add:
        # barrier_price=130.00
    )

    simulations = 50_000
    time_steps = 252

    result = price_option_monte_carlo(
        market=market,
        option=option,
        simulations=simulations,
        time_steps=time_steps,
        seed=42
    )

    print_pricing_summary(
        market=market,
        option=option,
        result=result,
        time_steps=time_steps
    )

if __name__ == "__main__":
    main()
