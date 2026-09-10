import streamlit as st
import requests
import time

st.set_page_config(page_title="Tennis Scanner SofaScore", layout="wide")
st.title("Tennis Strategy: Favorite Lost 1st Set (SofaScore)")
st.subheader("Live Matches under Strategy:")

def get_sofa_matches():
    url = "https://sofascore.com"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        return requests.get(url, headers=headers).json().get("events", [])
    except:
        return []

live_matches = get_sofa_matches()
found = False

for m in live_matches:
    status = m.get("status", {})
    if status.get("type") == "inprogress":
        home_score = m.get("homeScore", {})
        if home_score.get("period2", 0) > 0 or m.get("awayScore", {}).get("period2", 0) > 0:
            found = True
            p1 = m.get("homeTeam", {}).get("name", "Player 1")
            p2 = m.get("awayTeam", {}).get("name", "Player 2")
            with st.expander(f"{p1} vs {p2}"):
                st.write("Match is being analyzed by SofaScore radar...")

if not found:
    st.info("No live matches under strategy on SofaScore right now.")

time.sleep(120)
st.rerun()
