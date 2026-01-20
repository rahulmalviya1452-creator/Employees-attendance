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
        # Clear existing entry for that day/person to avoid duplicates
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

# Tabs for different report views
rep_tab1, rep_tab2, rep_tab3 = st.tabs(["💰 Monthly Summary", "📅 Monthly Log", "👤 Employee History"])

with rep_tab1:
    st.subheader("Monthly Salary Calculation")
    c1, c2 = st.columns(2)
    with c1:
        sum_month = st.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], index=date.today().month - 1, key="sum_m")
    with c2:
        sum_year = st.selectbox("Year", [2024, 2025, 2026, 2027], index=2, key="sum_y")
    
    m_num = datetime.strptime(sum_month, "%B").month
    
    def calculate_payout(row):
        df = st.session_state.attendance.copy()
        if df.empty: 
            return pd.Series([0.0, 1000, 0, row["Base_Salary"] + 1000])
        
        df['Date'] = pd.to_datetime(df['Date'])
        month_data = df[(df['Date'].dt.month == m_num) & (df['Date'].dt.year == sum_year) & (df['Name'] == row['Name'])]
        
        l_count = (month_data["Status"] == "Leave").sum() * 1.0
        h_count = (month_data["Status"] == "Half-Day").sum() * 0.5
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
    st.subheader(f"Date-wise Log: {sum_month}")
    df_log = st.session_state.attendance.copy()
    if not df_log.empty:
        df_log['Date'] = pd.to_datetime(df_log['Date'])
        filtered_log = df_log[(df_log['Date'].dt.month == m_num) & (df_log['Date'].dt.year == sum_year)]
        
        if not filtered_log.empty:
            # Format date for cleaner viewing
            display_log = filtered_log.copy()
            display_log['Date'] = display_log['Date'].dt.strftime('%d-%m-%Y')
            st.table(display_log.sort_values(by="Date", ascending=False))
        else:
            st.info("No leave records found for this specific month.")
    else:
        st.info("No records found in the system yet.")

with rep_tab3:
    st.subheader("Individual Employee Record")
    target_name = st.selectbox("Select Employee", st.session_state.emp_data["Name"])
    
    personal_history = st.session_state.attendance[st.session_state.attendance["Name"] == target_name]
    
    if not personal_history.empty:
        st.write(f"Showing all recorded absences for **{target_name}**")
        st.table(personal_history.sort_values(by="Date", ascending=False))
        
        # Add a download button for this specific person
        csv = personal_history.to_csv(index=False).encode('utf-8')
        st.download_button(f"Download {target_name}'s Report", csv, f"{target_name}_report.csv", "text/csv")
    else:
        st.info(f"No leave records found for {target_name}.")

# Settings
with st.expander("⚙️ Settings: Edit Base Salaries"):
    st.session_state.emp_data = st.data_editor(st.session_state.emp_data, num_rows="fixed")
