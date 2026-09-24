from dataclasses import dataclass
from math import erf, exp, log, sqrt
from random import Random, random
from statistics import stdev

# 1. DATA MODELS

@dataclass
class MarketData:

    # Information about the market and underlying stock.

    spot_price: float                # Current stock price: S0
    risk_free_rate: float            # Risk-free interest rate: r 
    volatility: float                # Annual Volatility of the stock: sigma
    dividend_yield: float = 0.0      # Dividend yield of the stock

@dataclass
class EuropeanOption:

    # European option contract.
    # option_type must be either ''call' or 'put'.

    strike_price: float              # Strike price: K
    maturity_years: float            # Time to expiry 
    option_type: str                 # 'call' or 'put'

@dataclass 
class PricingResult:

    # Result returned by the Monte Carlo pricing engine.

    price: float                    # Estimated option price
    standard_error: float           # Standard error of the estimate
    confidence_interval_low: float  # Lower bound of the 95% confidence interval
    confidence_interval_high: float # Upper bound of the 95% confidence interval
    simulations: int                # Number of Monte Carlo simulations performed

# 2. VALIDATION 

def validate_inputs(
        market: MarketData,
        option: EuropeanOption,
        simulations: int
) -> None:

    # Catch invalid inputs early instead of returning misleading prices.

    if market.spot_price <= 0:
        raise ValueError("spot price must be greater than 0")

    if market.volatility < 0:
        raise ValueError("Volatility cannot be negative")

    if option.strike_price <= 0:
        raise ValueError("Strike price must be greater than 0")

    if option.maturity_years <= 0:
        raise ValueError("Maturity must be greater than 0")

    if option.option_type.lower() not in {"call", "put"}:
        raise ValueError("Option type must be either 'call' or 'put'")

    if simulations < 2:
        raise ValueError("Use at least 2 simulations")

# 3. PRICE SIMULATION

def simulate_terminal_stock_prices(
        market: MarketData,
        option: EuropeanOption,
        simulations: int,
        seed: int | None = None
) -> list[float]:

    # Generate simulated stock prices at expiry using
    # Geometric Brownian Motion under the risk-neutral measure.

    # Formula: 
    # S_T = S_0 * exp((r - q - 0.5 * sigma^2) * T + sigma * sqrt(T) * Z)

    # Z is a random draw from the standard normal distribution.

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

# 4. PAYOFF CALCULATION

def calculate_payoff(
        terminal_prices: float,
        option: EuropeanOption
) -> float:

    # Calculate one option payoff at expiry.

    # Call payoff = max(ST - K, 0)
    # Put payoff = max(K - ST), 0)

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

    # Apply the payoff formula across all simulations.

    return [ 
        calculate_payoff(price, option)
        for price in terminal_prices
    ]

# 5. MONTE CARLO PRICER

def price_option_monte_carlo(
        market: MarketData,
        option: EuropeanOption,
        simulations: int = 100_000,
        seed: int | None = 42
) -> PricingResult:

    # Main pricing function

    # Steps.
    #   1. Simulate terminal stock prices.
    #   2. Calculate each option payoff.
    #   3. Average the payoffs.
    #   4. Discount the average to present value.
    #   5. Estimate the standard error and 95% confidence interval.

    validate_inputs(market, option, simulations)

    terminal_prices = simulate_terminal_stock_prices(
        market = market,
        option = option,
        simulations = simulations,
        seed = seed
    )

    payoffs = calculate_payoffs(
        terminal_prices = terminal_prices,
        option = option
    )

    average_payoff = sum(payoffs) / simulations

    discount_error = exp(
        -market.risk_free_rate * option.maturity_years
    )

    option_price = average_payoff * discount_error

    payoff_standard_deviation = stdev(payoffs)

    standard_error = ( 
        discount_error * payoff_standard_deviation / sqrt(simulations)
    )

    confidence_interval_low = option_price - 1.96 * standard_error
    confidence_interval_high = option_price + 1.96 * standard_error

    return PricingResult(
        price = option_price,
        standard_error = standard_error,
        confidence_interval_low = confidence_interval_low,
        confidence_interval_high = confidence_interval_high,
        simulations = simulations
    )

# 6. BLACK-SCHOLES BENCHMARK

def normal_cdf(value: float) -> float:

    # Cumulative distribution function for a standard normal variable.

    return 0.5 * (1 + erf(value / sqrt(2)))

def black_scholes_price(
        market: MarketData,
        option: EuropeanOption
) -> float:

    # Analytical Black-Scholes price for European call and put options.

    # This is used to validate the Monte Carlo estimate,

    s = market.spot_price
    k = option.strike_price
    t = option.maturity_years
    r = market.risk_free_rate
    q = market.dividend_yield
    sigma = market.volatility

    if sigma == 0:
        raise ValueError(
            "Black-Scholes benchmark requires volatility > 0 "
        )

    d1 = (
        log(s / k) + (r - q + 0.5 * sigma ** 2) * t
    ) / (sigma * sqrt(t))

    d2 = d1 - sigma * sqrt(t)

    if option.option_type.lower() == "call":
        return (
            s * exp(-q * t) * normal_cdf(d1) - s * exp(-q * t) * normal_cdf(-d1)
        )

# 7. DISPLAY RESULTS

def print_pricing_summary(
        market: MarketData,
        option: EuropeanOption,
        monte_carlo_result: PricingResult,
        black_scholes_result: float
)
    # Keep representation separate from pricing logic.

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
    print(f"Black–Scholes price:  ${black_scholes_result:.4f}")

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
        print("\nValidation: Increase simulations and test again.")

    print("=" * 60 + "\n")

# 8. PROGRAM ENTRY POINT

def main() -> None:

    # Change these values to price another European option.

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