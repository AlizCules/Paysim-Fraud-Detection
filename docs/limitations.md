# Limitations

- PaySim is simulated data, not real bank transaction data.
- The working training sample has a different fraud prevalence from the full source because negatives were downsampled.
- The raw source is ignored by Git because it exceeds the normal single-file limit; reproducibility requires a permitted local copy.
- The official post-transaction scope is suitable for monitoring after transaction state is available, not real-time pre-authorization.
- The selected threshold optimizes validation F1 and may not be the right operational threshold without an explicit cost model.
- `fraud_score` is not presented as a calibrated probability.
- Simulator-specific patterns and future data drift limit real-world generalization.
- No financial loss ground truth or production validation is available.
- The dataset redistribution/license status was not independently verified here.
