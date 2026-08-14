# Limitations

- PaySim is simulated data, not real bank transaction data.
- Row-level PaySim data is not distributed with the repository; reproducibility requires a permitted local copy.
- The canonical aggregate artifacts were generated from a local full source before the current-tree data cleanup.
- The official post-transaction scope is suitable for monitoring after transaction state is available, not real-time pre-authorization.
- The selected threshold optimizes validation F1 and may not be the right operational threshold without an explicit cost model.
- `fraud_score` is not presented as a calibrated probability.
- Simulator-specific patterns and future data drift limit real-world generalization.
- No financial loss ground truth or production validation is available.
- The dataset redistribution/license status was not independently verified here.
