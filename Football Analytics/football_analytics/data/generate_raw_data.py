"""
Generates a synthetic, intentionally messy football player dataset
(football_players_raw.csv) that mimics real-world scouting/tracking
data exports -- missing values, duplicate rows, inconsistent casing,
and a couple of out-of-range values -- so the Pig/ETL simulation stage
has real cleaning work to do.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

TEAMS = [
    "Manchester City", "Real Madrid", "Bayern Munich", "Liverpool",
    "Paris SG", "Inter Milan", "Arsenal", "Barcelona",
    "Borussia Dortmund", "Napoli", "Chelsea", "Atletico Madrid",
]

POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Forward"]

FIRST_NAMES = [
    "Lucas", "Mateo", "Kai", "Diego", "Noah", "Leo", "Marco", "Jude",
    "Enzo", "Bruno", "Rafael", "Theo", "Adrian", "Victor", "Samuel",
    "Elias", "Gabriel", "Hugo", "Ivan", "Rico", "Malik", "Owen",
    "Pablo", "Tariq", "Andres", "Kevin", "Nico", "Omar", "Felix", "Yusuf",
]

LAST_NAMES = [
    "Silva", "Muller", "Garcia", "Costa", "Nakamura", "Rossi", "Adeyemi",
    "Fernandez", "Kovac", "Dubois", "Okafor", "Larsson", "Hernandez",
    "Weber", "Santos", "Diallo", "Ivanov", "Pereira", "Morales", "Haas",
]


def random_name(used):
    while True:
        name = f"{np.random.choice(FIRST_NAMES)} {np.random.choice(LAST_NAMES)}"
        if name not in used:
            used.add(name)
            return name


def generate(n_players=180):
    used_names = set()
    rows = []

    for i in range(1, n_players + 1):
        position = np.random.choice(POSITIONS, p=[0.10, 0.30, 0.35, 0.25])
        age = int(np.clip(np.random.normal(25, 4), 17, 39))
        matches = int(np.clip(np.random.normal(24, 8), 1, 38))

        # Stats vary by position to keep the data plausible
        if position == "Forward":
            goals = max(0, int(np.random.normal(0.45, 0.25) * matches))
            assists = max(0, int(np.random.normal(0.20, 0.15) * matches))
        elif position == "Midfielder":
            goals = max(0, int(np.random.normal(0.15, 0.12) * matches))
            assists = max(0, int(np.random.normal(0.28, 0.18) * matches))
        elif position == "Defender":
            goals = max(0, int(np.random.normal(0.04, 0.05) * matches))
            assists = max(0, int(np.random.normal(0.08, 0.08) * matches))
        else:  # Goalkeeper
            goals = 0
            assists = max(0, int(np.random.normal(0.01, 0.02) * matches))

        pass_accuracy = round(float(np.clip(np.random.normal(82, 7), 45, 99)), 1)
        distance_km = round(float(np.clip(np.random.normal(10.2, 1.4), 6, 14)), 2)
        sprint_speed_kmh = round(float(np.clip(np.random.normal(31, 2.5), 22, 38)), 1)
        tackles = int(np.clip(np.random.normal(1.8 if position == "Defender" else 0.8, 1.0) * matches / 3, 0, 140))
        yellow_cards = int(np.clip(np.random.poisson(3), 0, 12))
        red_cards = int(np.random.binomial(1, 0.05))
        market_value_million = round(float(np.clip(np.random.lognormal(mean=2.6, sigma=0.9), 0.5, 220)), 1)
        rating = round(float(np.clip(np.random.normal(6.8, 0.6), 4.5, 9.5)), 2)

        rows.append({
            "player_id": i,
            "player_name": random_name(used_names),
            "team": np.random.choice(TEAMS),
            "position": position,
            "age": age,
            "matches_played": matches,
            "goals": goals,
            "assists": assists,
            "pass_accuracy": pass_accuracy,
            "distance_covered_km": distance_km,
            "sprint_speed_kmh": sprint_speed_kmh,
            "tackles": tackles,
            "yellow_cards": yellow_cards,
            "red_cards": red_cards,
            "market_value_million_eur": market_value_million,
            "rating": rating,
        })

    df = pd.DataFrame(rows)

    # --- Intentionally introduce messiness for the ETL stage to fix ---

    # 1. Missing values scattered across a few columns
    for col in ["pass_accuracy", "sprint_speed_kmh", "market_value_million_eur", "team"]:
        idx = np.random.choice(df.index, size=max(1, len(df) // 25), replace=False)
        df.loc[idx, col] = np.nan

    # 2. Inconsistent text casing / whitespace in categorical columns
    messy_idx = np.random.choice(df.index, size=len(df) // 10, replace=False)
    df.loc[messy_idx, "position"] = df.loc[messy_idx, "position"].str.upper()
    messy_idx2 = np.random.choice(df.index, size=len(df) // 12, replace=False)
    df.loc[messy_idx2, "team"] = df.loc[messy_idx2, "team"].astype(str).str.strip() + "  "

    # 3. A few duplicate rows (simulating repeated export)
    dup_rows = df.sample(n=6, random_state=1)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 4. A couple of out-of-range / bad values
    df.loc[df.index[3], "age"] = -5
    df.loc[df.index[8], "pass_accuracy"] = 143.0

    df = df.sample(frac=1, random_state=7).reset_index(drop=True)  # shuffle rows
    return df


if __name__ == "__main__":
    df = generate()
    out_path = "football_players_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")
