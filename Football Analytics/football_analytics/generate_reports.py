"""
Performance Reports
----------------------
Final pipeline stage: exports human-readable, shareable analytics
reports (CSV + text summary) from the Hive-simulation SQL layer.
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from hive_simulation import HiveSimulation  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "reports")
CLEANED_CSV = os.path.join(DATA_DIR, "football_players_cleaned.csv")
DB_PATH = os.path.join(DATA_DIR, "football_analytics.db")


def generate_reports():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    hive = HiveSimulation(DB_PATH)
    hive.load_table(CLEANED_CSV)

    reports = {
        "top_scorers": hive.top_scorers(15),
        "top_rated_players": hive.top_by_rating(15),
        "team_summary": hive.team_summary(),
        "position_summary": hive.position_summary(),
        "disciplinary_watchlist": hive.disciplinary_watchlist(),
        "undervalued_talents": hive.undervalued_talents(15),
    }

    for name, table in reports.items():
        path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        table.to_csv(path, index=False)
        print(f"[Reports] Wrote {path} ({len(table)} rows)")

    # Combined text summary
    summary_path = os.path.join(OUTPUT_DIR, "performance_report.txt")
    with open(summary_path, "w") as f:
        f.write("FOOTBALL PLAYER PERFORMANCE ANALYTICS -- SUMMARY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        f.write("TOP 10 SCORERS\n" + "-" * 30 + "\n")
        f.write(reports["top_scorers"].head(10).to_string(index=False) + "\n\n")

        f.write("TOP 10 RATED PLAYERS\n" + "-" * 30 + "\n")
        f.write(reports["top_rated_players"].head(10).to_string(index=False) + "\n\n")

        f.write("TEAM SUMMARY\n" + "-" * 30 + "\n")
        f.write(reports["team_summary"].to_string(index=False) + "\n\n")

        f.write("POSITION SUMMARY\n" + "-" * 30 + "\n")
        f.write(reports["position_summary"].to_string(index=False) + "\n\n")

        f.write("DISCIPLINARY WATCHLIST\n" + "-" * 30 + "\n")
        f.write(reports["disciplinary_watchlist"].to_string(index=False) + "\n\n")

        f.write("UNDERVALUED TALENTS (rating >= 7.2)\n" + "-" * 30 + "\n")
        f.write(reports["undervalued_talents"].to_string(index=False) + "\n")

    print(f"[Reports] Wrote combined summary -> {summary_path}")
    hive.close()


if __name__ == "__main__":
    generate_reports()
