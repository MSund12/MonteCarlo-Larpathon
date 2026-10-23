# test_estimators.py — explanation

Source: [test_estimators.py](../../test_estimators.py)

## What is happening and why

- Reconstruct antithetic pair averages directly and compare their mean and standard error with the estimator. This checks that uncertainty uses independent pairs rather than individual dependent paths.
- Reconstruct pilot and production random streams to check the control adjustment. Pilot observations must fit beta without entering the reported production moments.
- Construct Greek differences from correlated scenario payoffs and compare the resulting intervals. This detects errors that would arise from ignoring covariance between bumped prices.
- Construct the monitored log-price covariance matrix independently to verify the geometric Asian control mean. With one monitoring date, geometric and arithmetic averages coincide.
- Compare estimated Greeks with analytical European sensitivities and check that enabling Greeks preserves the base price for each estimator mode.
- Repeat pricing over 60 seeds for each variance-reduction mode. Check standardized-error mean, mean squared standardized error and coverage of the analytical price; requiring at least 50 covered intervals allows for randomness in coverage itself.
- Exercise near-barrier bumps, zero volatility, forward Vega at the volatility boundary and invalid advanced settings. Also check that the engine API accepts variance reduction directly.

## Definitions in the code

- [`EstimatorTests`](../../test_estimators.py#L12)
- [`test_antithetic_interval_uses_pair_averages`](../../test_estimators.py#L13)
- [`test_control_pilot_and_main_are_separate`](../../test_estimators.py#L27)
- [`test_greek_intervals_use_correlated_path_differences`](../../test_estimators.py#L52)
- [`test_geometric_control_matches_direct_lognormal_expectation`](../../test_estimators.py#L68)
- [`test_greeks_against_analytical_values`](../../test_estimators.py#L91)
- [`test_greeks_do_not_change_base_price`](../../test_estimators.py#L116)
- [`test_repeated_seed_coverage_and_standard_errors`](../../test_estimators.py#L125)
- [`test_barrier_modes_and_boundaries`](../../test_estimators.py#L145)
- [`test_invalid_advanced_settings`](../../test_estimators.py#L156)
- [`test_engine_api_accepts_variance_reduction`](../../test_estimators.py#L164)
- [`draws`](../../test_estimators.py#L35)

## Explanations moved out of the source

- **File purpose:** Estimator correctness, independent sampling units, and uncertainty checks.
- **Source line 74 when extracted:** Independently construct the covariance matrix of monitored log prices.
- **Source line 84 when extracted:** One monitoring date makes arithmetic and geometric products identical.
- **Source line 135 when extracted:** Enable Greeks for "none" to exercise the advanced unadjusted estimator.
- **Source line 143 when extracted:** Coverage is itself random.

Related files: [explanation index](README.md).
