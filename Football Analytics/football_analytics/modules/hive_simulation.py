"""
Hive Simulation Module
-----------------------
Hive lets analysts run SQL over data stored in HDFS. We simulate that
same experience with SQLite: the cleaned CSV is loaded into a local
.db file as a proper table, and all analytics are expressed as plain
SQL (GROUP BY, HAVING, window-style ranking, joins-ready schema) --
the same queries would run unmodified on a real Hive warehouse.
"""

import sqlite3
import pandas as pd


class HiveSimulation:
    TABLE_NAME = "players"

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    # ---- LOAD (Hive: LOAD DATA INPATH ... INTO TABLE) -----------------
    def load_table(self, csv_path: str):
        df = pd.read_csv(csv_path)
        df.to_sql(self.TABLE_NAME, self.conn, if_exists="replace", index=False)
        print(f"[Hive Simulation] Loaded {len(df)} rows into table "
              f"'{self.TABLE_NAME}' ({self.db_path})")
        return self

    def query(self, sql: str) -> pd.DataFrame:
        return pd.read_sql_query(sql, self.conn)

    # ---- Canned analytical queries -------------------------------------
    def top_scorers(self, limit=10):
        sql = f"""
        SELECT player_name, team, position, goals, matches_played,
               goals_per_match
        FROM {self.TABLE_NAME}
        ORDER BY goals DESC
        LIMIT {limit};
        """
        return self.query(sql)

    def top_by_rating(self, limit=10):
        sql = f"""
        SELECT player_name, team, position, rating, performance_tier
        FROM {self.TABLE_NAME}
        ORDER BY rating DESC
        LIMIT {limit};
        """
        return self.query(sql)

    def team_summary(self):
        sql = f"""
        SELECT team,
               COUNT(*) AS squad_size,
               ROUND(AVG(rating), 2) AS avg_rating,
               SUM(goals) AS total_goals,
               SUM(assists) AS total_assists,
               ROUND(AVG(market_value_million_eur), 1) AS avg_market_value_m,
               ROUND(SUM(market_value_million_eur), 1) AS total_squad_value_m
        FROM {self.TABLE_NAME}
        GROUP BY team
        ORDER BY avg_rating DESC;
        """
        return self.query(sql)

    def position_summary(self):
        sql = f"""
        SELECT position,
               COUNT(*) AS num_players,
               ROUND(AVG(rating), 2) AS avg_rating,
               ROUND(AVG(pass_accuracy), 1) AS avg_pass_accuracy,
               ROUND(AVG(distance_covered_km), 2) AS avg_distance_km
        FROM {self.TABLE_NAME}
        GROUP BY position
        ORDER BY avg_rating DESC;
        """
        return self.query(sql)

    def disciplinary_watchlist(self, min_points=6):
        sql = f"""
        SELECT player_name, team, position, yellow_cards, red_cards,
               disciplinary_points
        FROM {self.TABLE_NAME}
        WHERE disciplinary_points >= {min_points}
        ORDER BY disciplinary_points DESC;
        """
        return self.query(sql)

    def undervalued_talents(self, limit=10):
        """High rating, comparatively low market value."""
        sql = f"""
        SELECT player_name, team, position, rating, market_value_million_eur
        FROM {self.TABLE_NAME}
        WHERE rating >= 7.2
        ORDER BY market_value_million_eur ASC
        LIMIT {limit};
        """
        return self.query(sql)

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    hive = HiveSimulation("../data/football_analytics.db")
    hive.load_table("../data/football_players_cleaned.csv")

    print("\nTop scorers:\n", hive.top_scorers(5))
    print("\nTeam summary:\n", hive.team_summary().head())
    print("\nPosition summary:\n", hive.position_summary())
    print("\nDisciplinary watchlist:\n", hive.disciplinary_watchlist().head())
    hive.close()
