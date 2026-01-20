import streamlit as st
import pandas as pd
from datetime import datetime, date

# Set Page Config for a clean look
st.set_page_config(page_title="Attendance App", layout="centered")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

# --- APP UI ---
st.title("📌 Staff Attendance")

# 1. Select Date
selected_date = st.date_input("1. Select Date", date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# 2. Select Employee
emp_name = st.selectbox("2. Select Employee Name", st.session_state.emp_data["Name"])

# 3. Select Attendance Type
status_type = st.radio("3. Select Attendance Type", ["Present", "Half-Day", "Leave"], horizontal=True)

# 4. Save Button
if st.button("Submit Attendance", type="primary", use_container_width=True):
    # Remove old entry if exists for that date/employee
    st.session_state.attendance = st.session_state.attendance[
        ~((st.session_state.attendance["Date"] == date_str) & 
          (st.session_state.attendance["Name"] == emp_name))
    ]
    
    # Save if not "Present" (since you only want to track exceptions)
    if status_type != "Present":
        new_row = pd.DataFrame({"Date": [date_str], "Name": [emp_name], "Status": [status_type]})
        st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
        st.success(f"Successfully marked {emp_name} as {status_type} for {date_str}")
    else:
        st.success(f"Confirmed: {emp_name} is Present for {date_str}")
    
    st.toast("Record Saved!", icon="✅")

st.divider()

# --- OTHER OPTIONS IN TABS (Hidden by default) ---
with st.expander("📊 View Salary & History Reports"):
    sub_tab1, sub_tab2 = st.tabs(["Monthly Summary", "Detailed History"])
    
    with sub_tab1:
        def calculate_payout(row):
            emp_att = st.session_state.attendance[st.session_state.attendance["Name"] == row["Name"]]
            total_l = (emp_att["Status"] == "Leave").sum() * 1.0 + (emp_att["Status"] == "Half-Day").sum() * 0.5
            bonus = 1000 if total_l == 0 else 0
            unpaid = max(0.0, total_l - 1.0)
            daily = row["Base_Salary"] / 26
            deduction = unpaid * daily
            return pd.Series([total_l, bonus, round(deduction), round(row["Base_Salary"] + bonus - deduction)])

        summary = st.session_state.emp_data.copy()
        summary[["Leaves", "Bonus", "Deduction", "Final Pay"]] = summary.apply(calculate_payout, axis=1)
        st.dataframe(summary, hide_index=True)

    with sub_tab2:
        st.write("Full History Log:")
        st.table(st.session_state.attendance.sort_values(by="Date", ascending=False))
