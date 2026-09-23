"""
Football Player Performance Analytics System
===============================================
End-to-end pipeline orchestrator.

    Football Player Dataset (CSV)
            |
            v
    Pig Simulation (Pandas ETL)
            |
            v
    Hive Simulation (SQLite SQL analytics)
            |
            v
    MongoDB (NoSQL document storage)
            |
            v
    HBase Simulation (nested-dict wide-column store)
            |
            v
    Data Analysis + Streamlit Dashboard + Performance Reports

Run:
    python main.py                 # runs the ETL -> storage pipeline
    streamlit run dashboard.py     # explore the results interactively
    python generate_reports.py     # export CSV/text performance reports
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from pig_simulation import PigSimulation          # noqa: E402
from hive_simulation import HiveSimulation        # noqa: E402
from hbase_simulation import HBaseSimulation      # noqa: E402
from mongodb_simulation import PlayerNoSQLStore   # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RAW_CSV = os.path.join(DATA_DIR, "football_players_raw.csv")
CLEANED_CSV = os.path.join(DATA_DIR, "football_players_cleaned.csv")
DB_PATH = os.path.join(DATA_DIR, "football_analytics.db")
HBASE_JSON = os.path.join(DATA_DIR, "hbase_store.json")


def main():
    print("=" * 70)
    print("FOOTBALL PLAYER PERFORMANCE ANALYTICS -- PIPELINE START")
    print("=" * 70)

    if not os.path.exists(RAW_CSV):
        print(f"\nRaw dataset not found at {RAW_CSV}.")
        print("Generating a synthetic sample dataset "
              "(data/generate_raw_data.py)...")
        os.system(f'{sys.executable} "{os.path.join(DATA_DIR, "generate_raw_data.py")}"')

    # Step 1-2: Pig Simulation (ETL)
    print("\n--- STEP 1-2: Pig Simulation (Data Cleaning & ETL) ---")
    cleaned_df = PigSimulation(RAW_CSV).run(CLEANED_CSV)

    # Step 3: Hive Simulation (SQL analytics)
    print("\n--- STEP 3: Hive Simulation (SQLite SQL Analytics) ---")
    hive = HiveSimulation(DB_PATH)
    hive.load_table(CLEANED_CSV)
    print("\nSample -- Top 5 scorers:")
    print(hive.top_scorers(5).to_string(index=False))
    hive.close()

    # Step 4: MongoDB (NoSQL storage)
    print("\n--- STEP 4: MongoDB (NoSQL Storage) ---")
    store = PlayerNoSQLStore()
    store.load_from_dataframe(cleaned_df)
    print(f"Documents stored: {store.count()}")

    # HBase Simulation (wide-column nested-dict store)
    print("\n--- HBase Simulation (nested-dict player store) ---")
    hbase = HBaseSimulation().load_from_dataframe(cleaned_df)
    hbase.export_json(HBASE_JSON)

    # Step 5: Data Analysis summary
    print("\n--- STEP 5: Data Analysis Summary ---")
    print(f"Total players analyzed : {len(cleaned_df)}")
    print(f"Teams covered           : {cleaned_df['team'].nunique()}")
    print(f"Average rating          : {cleaned_df['rating'].mean():.2f}")
    print(f"Top performance tier    : "
          f"{cleaned_df['performance_tier'].value_counts().idxmax()}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE.")
    print("Next steps:")
    print("  streamlit run dashboard.py     -> interactive dashboard")
    print("  python generate_reports.py     -> export performance reports")
    print("=" * 70)


if __name__ == "__main__":
    main()
