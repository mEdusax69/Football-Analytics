"""
HBase Simulation Module
-------------------------
HBase stores data as: row key -> column family -> column -> value.
We simulate that model with nested Python dictionaries:

    {
      "player_id": {
          "identity":    {"name": ..., "team": ..., "position": ...},
          "performance": {"goals": ..., "assists": ..., "rating": ...},
          "physical":    {"distance_km": ..., "sprint_speed_kmh": ...},
      },
      ...
    }

This gives the same "row key + column family" access pattern HBase is
known for (fast lookup by key, sparse/flexible schema per family)
without needing a running HBase/Zookeeper cluster.
"""

import pandas as pd
import json


class HBaseSimulation:
    def __init__(self):
        self.store = {}

    # ---- PUT ---------------------------------------------------------
    def put(self, row_key: str, column_family: str, data: dict):
        self.store.setdefault(row_key, {}).setdefault(column_family, {}).update(data)

    # ---- GET ---------------------------------------------------------
    def get(self, row_key: str, column_family: str = None):
        row = self.store.get(row_key)
        if row is None:
            return None
        if column_family is None:
            return row
        return row.get(column_family)

    # ---- SCAN (all rows, optionally filtered) -------------------------
    def scan(self, column_family: str = None, filter_fn=None):
        results = {}
        for row_key, families in self.store.items():
            if column_family and column_family not in families:
                continue
            if filter_fn and not filter_fn(row_key, families):
                continue
            results[row_key] = families
        return results

    # ---- DELETE --------------------------------------------------------
    def delete(self, row_key: str, column_family: str = None):
        if row_key not in self.store:
            return False
        if column_family is None:
            del self.store[row_key]
        else:
            self.store[row_key].pop(column_family, None)
        return True

    # ---- Build the store from the cleaned dataset ----------------------
    def load_from_dataframe(self, df: pd.DataFrame):
        for _, r in df.iterrows():
            row_key = f"player:{int(r['player_id'])}"
            self.put(row_key, "identity", {
                "name": r["player_name"],
                "team": r["team"],
                "position": r["position"],
                "age": int(r["age"]),
            })
            self.put(row_key, "performance", {
                "goals": int(r["goals"]),
                "assists": int(r["assists"]),
                "rating": float(r["rating"]),
                "performance_tier": r["performance_tier"],
            })
            self.put(row_key, "physical", {
                "distance_covered_km": float(r["distance_covered_km"]),
                "sprint_speed_kmh": float(r["sprint_speed_kmh"]),
                "pass_accuracy": float(r["pass_accuracy"]),
            })
        print(f"[HBase Simulation] Loaded {len(self.store)} player rows "
              f"across 3 column families (identity, performance, physical)")
        return self

    def export_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.store, f, indent=2)
        print(f"[HBase Simulation] Exported store -> {path}")


if __name__ == "__main__":
    df = pd.read_csv("../data/football_players_cleaned.csv")
    hbase = HBaseSimulation().load_from_dataframe(df)

    sample_key = list(hbase.store.keys())[0]
    print(f"\nGET {sample_key} (full row):")
    print(json.dumps(hbase.get(sample_key), indent=2))

    print(f"\nGET {sample_key} 'performance' family only:")
    print(hbase.get(sample_key, "performance"))

    elite = hbase.scan(
        column_family="performance",
        filter_fn=lambda k, fam: fam["performance"]["performance_tier"] == "Elite",
    )
    print(f"\nSCAN for Elite tier players: {len(elite)} found")

    hbase.export_json("../data/hbase_store.json")
