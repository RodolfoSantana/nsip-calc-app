import os
import sys

# Auto-launch with Streamlit
if __name__ == "__main__" and not os.environ.get("INSIDE_STREAMLIT"):
    os.environ["INSIDE_STREAMLIT"] = "1"
    os.system(f"streamlit run \"{os.path.abspath(__file__)}\"")
    sys.exit()

import streamlit as st
import pandas as pd

# Load Excel
file_path = '/Users/rodolfosantana/Desktop/Team Management/OIC/NSIP_LOE.xlsx'
df = pd.read_excel(file_path)

# Normalize column names
df.columns = df.columns.str.strip()
df.rename(columns={"Tab": "Record Type"}, inplace=True)

# Page config
st.set_page_config(page_title="NSIP Messages Estimation", layout="wide")
st.markdown("<h1 style='color:#4B8BBE;'>NSIP Messages Estimation</h1>", unsafe_allow_html=True)

# Select System
systems = df['System'].dropna().unique()
selected_system = st.selectbox("Select a System:", systems)

# Filter data
df_filtered = df[df['System'] == selected_system].copy()

# Use unique keys internally, but clean labels visually
df_filtered["selection_key"] = df_filtered.index
df_filtered["label"] = df_filtered.apply(lambda row: f"📁 {row['Record Type']} → {row['Direction']}", axis=1)
key_to_label = dict(zip(df_filtered["selection_key"], df_filtered["label"]))

# Multiselect with format_func for clean display
st.subheader("Step 1: Select flows")
selected_keys = st.multiselect(
    "Flows:",
    options=list(key_to_label.keys()),
    format_func=lambda k: key_to_label[k]
)

# Input storage
frequency_map = {}
monthly_volume_map = {}
exec_hour_map = {}
exec_day_map = {}

if selected_keys:
    st.markdown("### Step 2: Configure parameters for each selected flow")
    for key in selected_keys:
        row = df_filtered.loc[key]

        with st.container():
            st.markdown("---")
            cols = st.columns([2, 2, 2, 2, 2])
            with cols[0]:
                st.markdown(f"**{key_to_label[key]}**")

            with cols[1]:
                freq = st.radio("Frequency", ["Real Time", "Scheduled"], key=f"freq_{key}", horizontal=True)
                frequency_map[key] = freq

            if freq == "Scheduled":
                exec_hour = cols[2].number_input("Exec/hour", min_value=1, max_value=60, value=1, step=1, key=f"exec_hour_{key}")
                exec_day = exec_hour * 24 * 30
            else:
                exec_hour = 0
                exec_day = 0
                cols[2].markdown("Exec/hour: `0`")

            exec_hour_map[key] = exec_hour
            exec_day_map[key] = exec_day

            with cols[3]:
                monthly = st.number_input("Monthly Volume", min_value=0, value=0, step=1, key=f"monthly_{key}")
                monthly_volume_map[key] = monthly

            with cols[4]:
                st.markdown(f"Exec/Month: **{exec_day}**")

    st.divider()

    # Step 3: Results
    st.markdown("### Step 3: Results")
    records = []

    for key in selected_keys:
        row = df_filtered.loc[key].to_dict()

        freq = frequency_map[key]
        monthly = monthly_volume_map[key]
        exec_hour = exec_hour_map[key]
        exec_day = exec_day_map[key]

        total_msgs = monthly * row["# Messages"]
        if freq == "Scheduled":
            total_msgs += exec_day

        row.update({
            "Frequency": freq,
            "Executions per Hour": exec_hour,
            "Executions per Day": exec_day,
            "Monthly Volume": monthly,
            "Total Messages": total_msgs
        })
        records.append(row)

    df_final = pd.DataFrame(records)

    # Show summary including total per row
    st.subheader("Selected Lines Summary:")
    summary_columns = ["Record Type", "Direction", "Description", "# Messages", "Total Messages"]
    st.dataframe(df_final[summary_columns], use_container_width=True)

    # Show total with dynamic color
    total = int(df_final["Total Messages"].sum())
    color = "red" if total > 1_000_000 else "green"
    st.markdown(f"<h3 style='color:{color};'>💬 Total Messages: <b>{total:,}</b></h3>", unsafe_allow_html=True)

else:
    st.info("Please select at least one flow to begin.")
