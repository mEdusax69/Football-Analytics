"""
Streamlit Dashboard
---------------------
Interactive charts and KPIs for the Football Player Performance
Analytics System. Reads the cleaned dataset (produced by the Pig
simulation stage) and layers the Hive-style SQL analytics on top.

Run with:
    streamlit run dashboard.py
"""

import sys
import os
import pandas as pd
import streamlit as st

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from hive_simulation import HiveSimulation  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CLEANED_CSV = os.path.join(DATA_DIR, "football_players_cleaned.csv")
DB_PATH = os.path.join(DATA_DIR, "football_analytics.db")

st.set_page_config(page_title="Football Player Performance Analytics",
                    layout="wide", page_icon="⚽")

st.title("⚽ Football Player Performance Analytics")
st.caption("Big Data pipeline: Pig (Pandas ETL) → Hive (SQLite) → "
           "MongoDB (NoSQL) → HBase (nested store) → Streamlit")


@st.cache_data
def load_data():
    df = pd.read_csv(CLEANED_CSV)
    return df


@st.cache_resource
def get_hive():
    hive = HiveSimulation(DB_PATH)
    hive.load_table(CLEANED_CSV)
    return hive


if not os.path.exists(CLEANED_CSV):
    st.error("Cleaned dataset not found. Run `python main.py` first to "
             "execute the ETL pipeline.")
    st.stop()

df = load_data()
hive = get_hive()

# ---------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------
st.sidebar.header("Filters")
teams = sorted(df["team"].unique())
positions = sorted(df["position"].unique())

selected_teams = st.sidebar.multiselect("Team", teams, default=teams)
selected_positions = st.sidebar.multiselect("Position", positions, default=positions)
min_age, max_age = int(df["age"].min()), int(df["age"].max())
age_range = st.sidebar.slider("Age range", min_age, max_age, (min_age, max_age))

filtered = df[
    df["team"].isin(selected_teams)
    & df["position"].isin(selected_positions)
    & df["age"].between(age_range[0], age_range[1])
]

# ---------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Players", len(filtered))
k2.metric("Avg Rating", f"{filtered['rating'].mean():.2f}" if len(filtered) else "-")
k3.metric("Total Goals", int(filtered["goals"].sum()))
k4.metric("Total Assists", int(filtered["assists"].sum()))
k5.metric("Avg Market Value (€M)",
          f"{filtered['market_value_million_eur'].mean():.1f}" if len(filtered) else "-")

st.divider()

# ---------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Scorers")
    top_scorers = filtered.sort_values("goals", ascending=False).head(10)
    st.bar_chart(top_scorers.set_index("player_name")["goals"])

with col2:
    st.subheader("Average Rating by Team")
    team_rating = filtered.groupby("team")["rating"].mean().sort_values(ascending=False)
    st.bar_chart(team_rating)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Performance Tier Distribution")
    tier_counts = filtered["performance_tier"].value_counts()
    st.bar_chart(tier_counts)

with col4:
    st.subheader("Pass Accuracy vs Rating")
    st.scatter_chart(filtered, x="pass_accuracy", y="rating", color="position")

st.subheader("Distance Covered vs Sprint Speed")
st.scatter_chart(filtered, x="distance_covered_km", y="sprint_speed_kmh", color="position")

st.divider()

# ---------------------------------------------------------------------
# Hive-style SQL analytics tables
# ---------------------------------------------------------------------
st.subheader("Team Summary (Hive/SQL analytics)")
st.dataframe(hive.team_summary(), use_container_width=True)

st.subheader("Undervalued Talents (rating ≥ 7.2, lowest market value)")
st.dataframe(hive.undervalued_talents(15), use_container_width=True)

st.subheader("Disciplinary Watchlist")
st.dataframe(hive.disciplinary_watchlist(), use_container_width=True)

st.divider()
st.subheader("Full Player Table")
st.dataframe(filtered, use_container_width=True)
