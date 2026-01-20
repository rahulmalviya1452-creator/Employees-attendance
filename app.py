import streamlit as st
import pandas as pd
from datetime import datetime, date

# Set Page Config
st.set_page_config(page_title="Staff Manager", layout="centered")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

# --- MAIN INTERFACE ---
st.title("📌 Staff Attendance")

# Step 1: Mark Attendance
with st.container(border=True):
    selected_date = st.date_input("1. Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    emp_name = st.selectbox("2. Select Employee Name", st.session_state.emp_data["Name"])
    status_type = st.radio("3. Select Attendance Type", ["Present", "Half-Day", "Leave"], horizontal=True)

    if st.button("Submit Attendance", type="primary", use_container_width=True):
        # Remove old entry for that date/employee
        st.session_state.attendance = st.session_state.attendance[
            ~((st.session_state.attendance["Date"] == date_str) & 
              (st.session_state.attendance["Name"] == emp_name))
        ]
        
        if status_type != "Present":
            new_row = pd.DataFrame({"Date": [date_str], "Name": [emp_name], "Status": [status_type]})
            st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)
            st.success(f"Saved: {emp_name} is on {status_type}")
        else:
            st.success(f"Saved: {emp_name} is Present")
        st.toast("Record Updated!")

st.divider()

# --- REPORTS SECTION ---
st.header("📊 Reports & History")

# NEW: Month and Year Picker for Summary
col1, col2 = st.columns(2)
with col1:
    view_month = st.selectbox("Select Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=date.today().month - 1)
with col2:
    view_year = st.selectbox("Select Year", [2024, 2025, 2026], index=2)

month_num = datetime.strptime(view_month, "%B").month

# Filter data for the selected Month/Year
def filter_monthly_data(df, m, y):
    if df.empty: return df
    df_temp = df.copy()
    df_temp['Date'] = pd.to_datetime(df_temp['Date'])
    return df_temp[(df_temp['Date'].dt.month == m) & (df_temp['Date'].dt.year == y)]

monthly_attendance = filter_monthly_data(st.session_state.attendance, month_num, view_year)

# Tabs for Summary vs Detailed Log
rep_tab1, rep_tab2 = st.tabs(["Monthly Salary Summary", "Detailed Leave Log"])

with rep_tab1:
    st.subheader(f"Salaries for {view_month} {view_year}")
    
    def calculate_payout(row):
        # Only count leaves for the selected month
        emp_att = monthly_attendance[monthly_attendance["Name"] == row["Name"]]
        l_count = (emp_att["Status"] == "Leave").sum() * 1.0
        h_count = (emp_att["Status"] == "Half-Day").sum() * 0.5
        total_l = l_count + h_count
        
        bonus = 1000 if total_l == 0 else 0
        unpaid = max(0.0, total_l - 1.0)
        daily = row["Base_Salary"] / 26
        deduction = unpaid * daily
        
        return pd.Series([total_l, bonus, round(deduction), round(row["Base_Salary"] + bonus - deduction)])

    summary = st.session_state.emp_data.copy()
    summary[["Leaves", "Bonus", "Deduction", "Final Pay"]] = summary.apply(calculate_payout, axis=1)
    st.dataframe(summary, use_container_width=True, hide_index=True)

with rep_tab2:
    st.subheader(f"Leave Log for {view_month}")
    if not monthly_attendance.empty:
        # Format date for display
        display_log = monthly_attendance.copy()
        display_log['Date'] = display_log['Date'].dt.strftime('%d-%m-%Y')
        st.table(display_log.sort_values(by="Date", ascending=False))
    else:
        st.info("No leaves or half-days recorded for this month.")

# Edit Base Salary Option
with st.expander("⚙️ Edit Base Salaries"):
    st.session_state.emp_data = st.data_editor(st.session_state.emp_data, num_rows="fixed")
    st.warning("Changing salary here updates the calculation for all months.")
