# Project overview

MonteCarlo-Larpathon is a Python project that estimates option prices using Monte Carlo simulation. It generates stock-price scenarios, calculates the payoff for each scenario, and discounts the average payoff to estimate a value today.

- Start with `monte_carlo_demo.py`. It contains the complete runnable application.
- Use the interactive menus or command-line arguments to select a contract and market inputs.
- Inspect prices, sampling uncertainty, optional Greeks, JSON reports, and charts.
- The modular Python files expose the same core calculations in smaller pieces for reading and development.
- The model uses risk-neutral scenarios with constant parameters. Its simulated stock prices are pricing scenarios, not market forecasts.

## How pricing works

Choose a contract, generate stock-price scenarios, calculate each payoff, then discount and average the payoffs. A European call with strike 100 pays 20 if the stock finishes at 120 and zero if it finishes at 90. Many scenarios provide a price estimate and a measure of sampling uncertainty.

## Reading routes

Start with Getting Started, Pricing Engines, and Charts and Reports. For technical review, continue with Greeks, Variance Reduction, and Model Assumptions. Developers can use Testing and Code Guide.

## Pages

- [Project overview](Home.md)
- [Getting started](Getting-Started.md)
- [Pricing engines and contracts](Pricing-Engines.md)
- [Inputs and examples](Inputs-and-Examples.md)
- [Greeks: sensitivity to inputs](Greeks.md)
- [Variance reduction](Variance-Reduction.md)
- [Charts and reports](Charts-and-Reports.md)
- [Testing and code guide](Testing-and-Code-Guide.md)
- [Troubleshooting](Troubleshooting.md)
- [Model assumptions and scope](Model-Assumptions.md)

---
[Home](Home.md) · [Getting Started](Getting-Started.md) · [Code Guide](Testing-and-Code-Guide.md) · [Model Assumptions](Model-Assumptions.md)
