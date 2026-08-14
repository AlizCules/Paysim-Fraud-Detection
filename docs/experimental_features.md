# Experimental features excluded from the official benchmark

The earlier notebooks contained train-window aggregates such as transaction counts by account and day. A row could receive information from transactions that occurred later in the same training window. These features are not included in the canonical benchmark.

The earlier `is_fraud_peak_hour` rule was chosen from fraud-oriented EDA and is therefore target-informed. `day_bucket_risk` is directly target-derived. Both are excluded. They may be revisited only with point-in-time, train-only logic and a documented feature-learning step.
