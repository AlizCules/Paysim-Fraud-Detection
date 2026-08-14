# Data

PaySim row-level data is **not distributed with this repository**. Obtain a permitted copy from the documented [Kaggle PaySim dataset page](https://www.kaggle.com/datasets/ealaxi/paysim1) and place it at:

```text
data/raw/PS_20174392719_1491204439457_log.csv
```

The raw file is ignored by Git because it is approximately 470 MB. The pipeline refuses to silently fall back to a missing or unverified sample and emits a clear download/location error when the raw file is absent.

`data/sample/` is retained only for this instruction file; CSV files in that directory are ignored. PaySim is a simulated mobile-money transaction dataset. See [`docs/data_sources.md`](../docs/data_sources.md) for provenance, license metadata, redistribution status, and historical exposure notes.
