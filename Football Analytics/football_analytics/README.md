# Football Player Performance Analytics System using Big Data Technologies

Analyzes football player performance data using Big Data concepts,
simulated with lightweight, locally-runnable tools so the whole
project runs on a laptop with no cluster setup:

| Big Data Tool | Simulated With |
|---|---|
| Apache Pig (ETL)  | Pandas (`modules/pig_simulation.py`) |
| Hive (SQL analytics) | SQLite (`modules/hive_simulation.py`) |
| HBase (wide-column store) | Nested dictionaries (`modules/hbase_simulation.py`) |
| MongoDB (NoSQL storage) | `pymongo` if a MongoDB server is available, otherwise an equivalent JSON-backed document store (`modules/mongodb_simulation.py`) |
| Dashboard | Streamlit (`dashboard.py`) |

## Workflow

1. Football Player Dataset (CSV)
2. Data Cleaning & ETL (Pandas — Pig Simulation)
3. SQLite (Hive Simulation)
4. MongoDB (NoSQL Storage)
5. Data Analysis
6. Streamlit Dashboard
7. Performance Reports

## Project Structure

```
football_analytics/
├── data/
│   ├── generate_raw_data.py        # generates the synthetic raw dataset
│   ├── football_players_raw.csv    # raw, messy input data
│   ├── football_players_cleaned.csv# output of the Pig/ETL stage
│   ├── football_analytics.db       # SQLite DB (Hive simulation)
│   ├── hbase_store.json            # exported HBase-style nested store
│   └── mongo_players.json          # NoSQL document store (fallback backend)
├── modules/
│   ├── pig_simulation.py           # ETL: load, clean, transform, store
│   ├── hive_simulation.py          # SQLite-backed SQL analytics
│   ├── hbase_simulation.py         # nested-dict wide-column simulation
│   └── mongodb_simulation.py       # CRUD NoSQL storage (Mongo or local sim)
├── dashboard.py                    # Streamlit dashboard
├── generate_reports.py             # exports CSV + text performance reports
├── main.py                         # runs the full pipeline end-to-end
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Run the pipeline

```bash
# 1. Run the full ETL -> SQLite -> MongoDB -> HBase pipeline
python main.py

# 2. Launch the interactive dashboard
streamlit run dashboard.py

# 3. Export performance reports (CSV + text summary)
python generate_reports.py
```

## Modules

- **Pig Simulation** — Data cleaning and preprocessing. Loads the raw
  CSV, removes duplicates, fixes invalid values, imputes missing data
  by position, and engineers features (`goals_per_match`,
  `performance_tier`, etc).
- **Hive Simulation** — SQL queries and analytics over the cleaned
  data using SQLite: top scorers, team summaries, position summaries,
  a disciplinary watchlist, and an "undervalued talent" query.
- **HBase Simulation** — Player data as nested dictionaries keyed by
  `player:<id>`, organized into `identity`, `performance`, and
  `physical` column families, supporting `put`/`get`/`scan`/`delete`.
- **MongoDB** — Full CRUD (create/read/update/delete) over player
  documents. Uses a real MongoDB server via `pymongo` if one is
  reachable at `mongodb://localhost:27017/`; otherwise transparently
  falls back to a JSON-backed local document store with the same
  query semantics (`$gt`, `$lt`, `$in`, `$ne`, dict-equality).
- **Dashboard** — Streamlit app with sidebar filters (team, position,
  age), KPI cards, bar/scatter charts, and the Hive SQL analytics
  tables rendered live.

## Notes on the Dataset

`data/generate_raw_data.py` generates a synthetic 180-player dataset
across 12 clubs and 4 positions, with realistic per-position stat
distributions. It intentionally includes messy data (missing values,
duplicate rows, inconsistent text casing, an invalid age, an
out-of-range pass-accuracy value) so the Pig/ETL stage has genuine
cleaning work to demonstrate. Swap in a real player dataset by
replacing `data/football_players_raw.csv` with the same column
schema.
