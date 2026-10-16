import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="EcoTwin",
    page_icon="🌱",
    layout="wide"
)

st.subheader("📷 Live Camera Occupancy")

@st.cache_data(ttl=1)
def read_occupancy():
    path = Path("occupancy.json")
    if path.exists():
        try:
            return int(json.loads(path.read_text()).get("occupancy", 0))
        except (ValueError, json.JSONDecodeError):
            return None
    return None

count = read_occupancy()

if count is not None:
    st.metric("People Detected", count)
else:
    st.info("Start person_count.py to receive camera data.")

st.title("🌱 EcoTwin — Green Building Digital Twin")
st.caption("Smart occupancy and energy monitoring prototype")
st.subheader("📷 Live Camera Occupancy")

file_path = Path("occupancy.json")

if file_path.exists():
    try:
        data = json.loads(file_path.read_text())
        live_count = int(data.get("occupancy", 0))
        st.metric("People Detected by Camera", live_count)
    except (ValueError, json.JSONDecodeError):
        st.info("Waiting for valid camera data...")
else:
    live_count = 0
    st.info("Camera data nahi mila. Pehle person_count.py run karo.")

# Demo data — abhi simulated hai
rooms = pd.DataFrame({
    "Room": ["Classroom 1", "Classroom 2", "Computer Lab", "Staff Room"],
    "Occupancy": [12, 0, 8, 2],
    "Lights": ["ON", "ON", "ON", "OFF"],
    "Power (W)": [240, 240, 500, 100]
})


st.subheader("🏢 Digital Twin — Building Floor Plan")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Classroom 1")
    st.metric("Occupancy", int(rooms.loc[0, "Occupancy"]))
    st.write("🟢 Occupied" if rooms.loc[0, "Occupancy"] > 0 else "⚪ Empty")

with col2:
    st.markdown("### Classroom 2")
    st.metric("Occupancy", int(rooms.loc[1, "Occupancy"]))
    st.write("🟢 Occupied" if rooms.loc[1, "Occupancy"] > 0 else "⚪ Empty")

col3, col4 = st.columns(2)

with col3:
    st.markdown("### Computer Lab")
    st.metric("Occupancy", int(rooms.loc[2, "Occupancy"]))
    st.write("🟢 Occupied" if rooms.loc[2, "Occupancy"] > 0 else "⚪ Empty")

with col4:
    st.markdown("### Staff Room")
    st.metric("Occupancy", int(rooms.loc[3, "Occupancy"]))
    st.write("🟢 Occupied" if rooms.loc[3, "Occupancy"] > 0 else "⚪ Empty")


c1, c2, c3 = st.columns(3)
c1.metric("Total Occupancy", int(rooms["Occupancy"].sum()))
c2.metric("Rooms Monitored", len(rooms))
c3.metric(
    "Estimated Power",
    f'{rooms["Power (W)"].sum()} W'
)

st.subheader("Building Room Status")
st.dataframe(rooms, use_container_width=True, hide_index=True)

st.subheader("Energy Saving Alerts")

empty_lights = rooms[
    (rooms["Occupancy"] == 0) &
    (rooms["Lights"] == "ON")
]

if empty_lights.empty:
    st.success("No empty room with lights ON in this demo.")
else:
    for _, room in empty_lights.iterrows():
        st.warning(
            f'{room["Room"]}: Room is empty but lights are ON. '
            "Check whether lighting can be switched off."
        )

st.caption(
    "Note: Room occupancy and power values are simulated demo data, "
    "not real building measurements."
)
