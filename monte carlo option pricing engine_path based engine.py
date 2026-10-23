













from dataclasses import dataclass
from math import exp, sqrt
from random import Random
from pricing_common import validate_market_contract, validate_count
from pricing_kernels import price as price_kernel
from math import isfinite
from collections.abc import Iterator



@dataclass
class MarketData:
    spot_price: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0


@dataclass
class OptionContract:













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



def validate_inputs(
    market: MarketData,
    option: OptionContract,
    simulations: int,
    time_steps: int
) -> None:

    validate_market_contract(market, option)
    validate_count(simulations, "simulations", minimum=2)
    validate_count(time_steps, "time_steps", minimum=1)
    valid_product_types = {"european", "asian", "up_and_out_barrier"}
    if not isinstance(option.product_type, str):
        raise ValueError("Product type must be a string.")

    if option.product_type.lower() not in valid_product_types:
        raise ValueError(
            "Product type must be 'european', 'asian', "
            "or 'up_and_out_barrier'."
        )

    if option.product_type.lower() == "up_and_out_barrier":
        if (option.barrier_price is None
                or isinstance(option.barrier_price, bool)
                or not isinstance(option.barrier_price, (int, float))
                or not isfinite(option.barrier_price)
                or option.barrier_price <= 0):
            raise ValueError("Barrier options require a finite positive barrier price.")

        if option.barrier_price <= market.spot_price:
            raise ValueError(
                "For this up-and-out example, the barrier "
                "must be above the current stock price."
            )



def iter_price_paths(
    market: MarketData,
    option: OptionContract,
    simulations: int,
    time_steps: int,
    seed: int | None = 42
) -> Iterator[list[float]]:
















    validate_inputs(market, option, simulations, time_steps)
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

        yield current_path

def simulate_price_paths(
    market: MarketData,
    option: OptionContract,
    simulations: int,
    time_steps: int,
    seed: int | None = 42,
) -> list[list[float]]:

    return list(iter_price_paths(market, option, simulations, time_steps, seed))



def vanilla_payoff(
    stock_price: float,
    option: OptionContract
) -> float:




    if option.option_type.lower() == "call":
        return max(stock_price - option.strike_price, 0.0)

    return max(option.strike_price - stock_price, 0.0)


def european_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:




    terminal_stock_price = price_path[-1]

    return vanilla_payoff(terminal_stock_price, option)


def asian_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:







    monitored_prices = price_path[1:]

    average_stock_price = (
        sum(monitored_prices) / len(monitored_prices)
    )

    return vanilla_payoff(average_stock_price, option)


def up_and_out_barrier_payoff(
    price_path: list[float],
    option: OptionContract
) -> float:








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




    product_type = option.product_type.lower()

    if product_type == "european":
        return european_payoff(price_path, option)

    if product_type == "asian":
        return asian_payoff(price_path, option)

    if product_type == "up_and_out_barrier":
        return up_and_out_barrier_payoff(price_path, option)

    raise ValueError("Unsupported product type.")



def price_option_monte_carlo(
    market: MarketData,
    option: OptionContract,
    simulations: int = 50_000,
    time_steps: int = 252,
    seed: int | None = 42,
        *,
        backend: str = "auto",
        batch_size: int = 8192,
        variance_reduction: str = "none",
        pilot_simulations: int = 2048,
) -> PricingResult:







    validate_inputs(
        market=market,
        option=option,
        simulations=simulations,
        time_steps=time_steps
    )

    return PricingResult(**price_kernel(
        market, option, simulations, time_steps, seed,
        backend=backend, batch_size=batch_size,
        variance_reduction=variance_reduction, pilot_simulations=pilot_simulations,
    ))



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



def main() -> None:




    market = MarketData(
        spot_price = 100.00,
        risk_free_rate = 0.05,
        volatility = 0.20,
        dividend_yield = 0.00
    )

    option = OptionContract(
        strike_price = 100.00,
        maturity_years = 1.00,
        option_type = "call",
        product_type = "asian"



    )

    simulations = 50_000
    time_steps = 252

    result = price_option_monte_carlo(
        market = market,
        option = option,
        simulations = simulations,
        time_steps = time_steps,
        seed=42
    )

    print_pricing_summary(
        market = market,
        option = option,
        result = result,
        time_steps = time_steps
    )

if __name__ == "__main__":
    main()
