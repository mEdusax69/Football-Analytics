"""
Pig Simulation Module
----------------------
Apache Pig scripts express ETL as a chain of LOAD -> FILTER -> FOREACH
GENERATE -> STORE operations over large flat files. We simulate that
same *pipeline style* using Pandas: every step is a clearly named,
chainable transformation, and the final DataFrame is STOREd back to
disk as a cleaned CSV -- functionally equivalent to a Pig script's
output, without requiring a Hadoop cluster.
"""

import pandas as pd
import numpy as np


class PigSimulation:
    """Mimics a Pig ETL script: LOAD -> CLEAN -> TRANSFORM -> STORE."""

    def __init__(self, input_path: str):
        self.input_path = input_path
        self.df = None
        self.log = []

    # ---- LOAD ------------------------------------------------------
    def load(self):
        self.df = pd.read_csv(self.input_path)
        self._note(f"LOADED {len(self.df)} rows from {self.input_path}")
        return self

    # ---- FILTER / CLEAN --------------------------------------------
    def clean(self):
        df = self.df
        before = len(df)

        # Normalize categorical text (Pig: FOREACH ... GENERATE LOWER/TRIM)
        df["team"] = df["team"].astype(str).str.strip()
        df["position"] = df["position"].astype(str).str.strip().str.title()

        # Drop exact duplicate rows (Pig: DISTINCT)
        df = df.drop_duplicates(subset=[c for c in df.columns if c != "player_id"])

        # Fix invalid ages (Pig: FILTER BY age > 0 AND age < 45)
        df.loc[(df["age"] <= 0) | (df["age"] > 45), "age"] = np.nan

        # Clamp impossible pass accuracy values to [0, 100]
        df["pass_accuracy"] = df["pass_accuracy"].clip(lower=0, upper=100)

        # Impute missing numeric values with the position-wise median
        numeric_cols = ["pass_accuracy", "sprint_speed_kmh",
                         "market_value_million_eur", "age"]
        for col in numeric_cols:
            df[col] = df.groupby("position")[col].transform(
                lambda s: s.fillna(s.median())
            )
            df[col] = df[col].fillna(df[col].median())

        # Impute missing team with "Unknown"
        df["team"] = df["team"].replace("nan", np.nan)
        df["team"] = df["team"].fillna("Unknown")

        df["age"] = df["age"].round().astype(int)

        self.df = df.reset_index(drop=True)
        removed = before - len(df)
        self._note(f"CLEANED rows: removed {removed} duplicate/invalid rows, "
                    f"imputed missing values, normalized text fields")
        return self

    # ---- TRANSFORM (FOREACH ... GENERATE) ---------------------------
    def transform(self):
        df = self.df

        df["goals_per_match"] = (df["goals"] / df["matches_played"]).round(3)
        df["assists_per_match"] = (df["assists"] / df["matches_played"]).round(3)
        df["goal_contributions"] = df["goals"] + df["assists"]
        df["disciplinary_points"] = df["yellow_cards"] + df["red_cards"] * 2

        def performance_tier(rating):
            if rating >= 8.0:
                return "Elite"
            elif rating >= 7.0:
                return "Excellent"
            elif rating >= 6.0:
                return "Average"
            else:
                return "Below Average"

        df["performance_tier"] = df["rating"].apply(performance_tier)

        self.df = df
        self._note("TRANSFORMED: generated goals_per_match, assists_per_match, "
                    "goal_contributions, disciplinary_points, performance_tier")
        return self

    # ---- STORE -------------------------------------------------------
    def store(self, output_path: str):
        self.df.to_csv(output_path, index=False)
        self._note(f"STORED {len(self.df)} cleaned rows -> {output_path}")
        return self

    def _note(self, msg):
        self.log.append(msg)
        print(f"[Pig Simulation] {msg}")

    def run(self, output_path: str) -> pd.DataFrame:
        self.load().clean().transform().store(output_path)
        return self.df


if __name__ == "__main__":
    pipeline = PigSimulation("../data/football_players_raw.csv")
    cleaned = pipeline.run("../data/football_players_cleaned.csv")
    print(cleaned.head())
