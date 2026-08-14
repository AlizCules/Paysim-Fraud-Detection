# Data source and provenance

The project uses **PaySim**, a simulated mobile-money transaction dataset distributed through the [Kaggle PaySim dataset page](https://www.kaggle.com/datasets/ealaxi/paysim1).

The raw filename is `PS_20174392719_1491204439457_log.csv`. The local raw file was verified at 6,362,620 rows, 11 columns, step range 1-743, and 8,213 fraud rows. The tracked working sample has 325,934 rows because it retains every fraud row and samples approximately 5% of the source non-fraud population.

The raw source is not committed because it is approximately 470 MB. The source URL and file name are documented so a reviewer can place a permitted local copy under `data/raw/`. The dataset's redistribution/license terms were not independently verified in this repository; do not assume that the raw source may be republished.

PaySim is a simulation. Findings describe patterns within the simulated environment and should not be read as claims about real bank customers, real fraud losses, or production fraud operations.
