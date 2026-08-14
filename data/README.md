# Data

This project distinguishes three data roles:

- `data/raw/PS_20174392719_1491204439457_log.csv` is the locally available full PaySim source. It is intentionally ignored by Git because it is approximately 470 MB.
- `data/sample/data.csv` is the tracked working sample. It retains all 8,213 fraud rows and approximately 5% of source non-fraud rows for practical model development.
- The final validation and test periods are read from the full local source when it is available. They retain source prevalence and are not used for model or threshold selection.

PaySim is a simulated mobile-money transaction dataset. The account identifiers are simulator identifiers, not verified personal identities. See [`docs/data_sources.md`](../docs/data_sources.md) for provenance and redistribution notes.
