# advanced_pricing.py — explanation

Source: [advanced_pricing.py](../../advanced_pricing.py)

## What is happening and why

- Reuse each normal shock across the base and bumped parameter scenarios. This common-random-number approach reduces noise in differences and retains their covariance.
- For antithetic sampling, generate Z and −Z and average their payoffs before accumulating statistics. One pair is one independent observation; N physical paths therefore provide N/2 observations.
- Calculate Greek differences per observation before computing their moments. Combining separate price standard errors would discard the dependence between paired scenarios.
- Create a child random stream for the pilot and keep production on the parent seed sequence. Pilot paths fit control coefficients and are excluded from production estimates and intervals.
- Adjust each observation as Y − beta × (X − E[X]). Apply this to each requested price or Greek using its matching control difference and known mean.
- Track physical paths, independent observations, pilot paths and parameter scenarios separately. total_path_evaluations counts production plus pilot paths across all parameter scenarios.
- Scale Vega and Rho by 0.01 and Theta by 1/365, including standard errors and both interval endpoints. Delta and Gamma need no report scaling.
- Treat the intervals as Monte Carlo sampling intervals. They do not measure finite-difference bias, model error or errors caused by a finite barrier monitoring schedule.

## Definitions in the code

- [`_batches`](../../advanced_pricing.py#L16)
- [`estimate`](../../advanced_pricing.py#L70)

## Explanations moved out of the source

- **File purpose:** Opt-in variance reduction and paired finite-difference Greeks using NumPy. shared shocks -> discounted payoffs -> antithetic averages -> Greek differences -> fixed pilot control adjustment -> moments of independent observations No standard errors are combined across dependent prices. Legacy kernels remain unchanged; this module never imports the application or visualization modules.
- **estimate:** Return pricing, Greek intervals, and explicit independent-sample accounting. `simulations` always means physical production paths. Antithetic modes require an even count; their independent sample count is simulations // 2. Pilot simulations are ADDITIONAL physical paths, excluded from reported estimates.
- **Source line 39 when extracted:** log(S_j), not log of the arithmetic running average.
- **Source line 53 when extracted:** Each row is ONE independent observation, even with two paths.
- **Source line 108 when extracted:** Independent child streams, stable whether Greeks/control are enabled or not.

Related files: [explanation index](README.md).
