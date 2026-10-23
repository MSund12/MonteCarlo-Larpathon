from dataclasses import dataclass
from math import erfc, exp, log, sqrt
from random import Random
from pricing_common import validate_market_contract, validate_count
from pricing_kernels import price as price_kernel



@dataclass
class MarketData:



    spot_price: float
    risk_free_rate: float
    volatility: float
    dividend_yield: float = 0.0

@dataclass
class EuropeanOption:




    strike_price: float
    maturity_years: float
    option_type: str

@dataclass 
class PricingResult:



    price: float
    standard_error: float
    confidence_interval_low: float
    confidence_interval_high: float
    simulations: int



def validate_inputs(
        market: MarketData,
        option: EuropeanOption,
        simulations: int
) -> None:

    validate_market_contract(market, option)
    validate_count(simulations, "simulations", minimum=2)



def simulate_terminal_stock_prices(
        market: MarketData,
        option: EuropeanOption,
        simulations: int,
        seed: int | None = None
) -> list[float]:









    validate_inputs(market, option, simulations)
    rng = Random(seed)

    S0 = market.spot_price
    r = market.risk_free_rate
    q = market.dividend_yield
    sigma = market.volatility
    T = option.maturity_years

    drift = (r - q - 0.5 * sigma ** 2) * T
    diffusion_scale = sigma * sqrt(T)

    terminal_prices = []

    for _ in range(simulations):
        Z = rng.gauss(0,1)

        terminal_price = S0 * exp(
            drift + diffusion_scale * Z
        ) 

        terminal_prices.append(terminal_price)

    return terminal_prices



def calculate_payoff(
        terminal_prices: float,
        option: EuropeanOption
) -> float:






    strike = option.strike_price
    option_type = option.option_type.lower()

    if option_type == "call":
        return max(terminal_prices - strike, 0.0)
    else:
        return max(strike - terminal_prices, 0.0)

def calculate_payoffs(
        terminal_prices: list[float],
    option: EuropeanOption
)   -> list[float]:



    return [ 
        calculate_payoff(price, option)
        for price in terminal_prices
    ]



def price_option_monte_carlo(
        market: MarketData,
        option: EuropeanOption,
        simulations: int = 100_000,
        seed: int | None = 42,
        *,
        backend: str = "auto",
        batch_size: int = 8192,
        variance_reduction: str = "none",
        pilot_simulations: int = 2048,
) -> PricingResult:










    validate_inputs(market, option, simulations)

    return PricingResult(**price_kernel(
        market, option, simulations, seed=seed,
        backend=backend, batch_size=batch_size,
        variance_reduction=variance_reduction, pilot_simulations=pilot_simulations,
    ))



def normal_cdf(value: float) -> float:



    return 0.5 * erfc(-value / sqrt(2))

def black_scholes_price(
        market: MarketData,
        option: EuropeanOption
) -> float:





    validate_market_contract(market, option)
    s = market.spot_price
    k = option.strike_price
    t = option.maturity_years
    r = market.risk_free_rate
    q = market.dividend_yield
    sigma = market.volatility

    if sigma == 0:
        terminal = s * exp((r - q) * t)
        return exp(-r * t) * calculate_payoff(terminal, option)

    d1 = (
        (log(s) - log(k)) + (r - q + 0.5 * sigma ** 2) * t
    ) / (sigma * sqrt(t))

    d2 = d1 - sigma * sqrt(t)

    if option.option_type.lower() == "call":
        return (
            s * exp(-q * t) * normal_cdf(d1) - k * exp(-r * t) * normal_cdf(d2)
        )

    return k * exp(-r * t) * normal_cdf(-d2) - s * exp(-q * t) * normal_cdf(-d1)



def print_pricing_summary(
        market: MarketData,
        option: EuropeanOption,
        monte_carlo_result: PricingResult,
        black_scholes_result: float
) -> None:


    print("\n" + "=" * 60)
    print("MONTE CARLO OPTION PRICING ENGINE")
    print("=" * 60)

    print(f"Option type:          {option.option_type.upper()}")
    print(f"Spot price:           ${market.spot_price:.2f}")
    print(f"Strike price:         ${option.strike_price:.2f}")
    print(f"Maturity:             {option.maturity_years:.2f} years")
    print(f"Risk-free rate:       {market.risk_free_rate:.2%}")
    print(f"Volatility:           {market.volatility:.2%}")
    print(f"Simulations:          {monte_carlo_result.simulations:,}")

    print("-" * 60)

    print(f"Monte Carlo price:    ${monte_carlo_result.price:.4f}")
    print(f"Standard error:       ${monte_carlo_result.standard_error:.4f}")
    print(
        "95% confidence interval: "
        f"${monte_carlo_result.confidence_interval_low:.4f} "
        f"to ${monte_carlo_result.confidence_interval_high:.4f}"
    )
    print(f"Blackâ€“Scholes price:  ${black_scholes_result:.4f}")

    difference = monte_carlo_result.price - black_scholes_result
    print(f"Difference:           ${difference:.4f}")

    within_interval = (
        monte_carlo_result.confidence_interval_low
        <= black_scholes_result
        <= monte_carlo_result.confidence_interval_high
    )

    if within_interval: 
        print("\nValidation: Black-Scholes is within the 95% interval.")
    else:
        print("\nValidation: Benchmark lies outside this approximate interval; inspect sampling error and model assumptions.")

    print("=" * 60 + "\n")



def main() -> None:



    market = MarketData(
        spot_price = 100.00,
        risk_free_rate = 0.05,
        volatility = 0.20,
        dividend_yield = 0.00
    )

    option = EuropeanOption(
        strike_price = 100.00,
        maturity_years = 1.0,
        option_type = "call"
    )

    monte_carlo_result = price_option_monte_carlo(
        market = market,
        option = option,
        simulations = 100_000,
        seed = 42
    )

    black_scholes_result = black_scholes_price(
        market = market,
        option = option
    )

    print_pricing_summary(
        market = market,
        option = option,
        monte_carlo_result = monte_carlo_result,
        black_scholes_result = black_scholes_result
    )

if __name__ == "__main__":
    main()