import streamlit as st
import pandas as pd
from datetime import datetime, date

# Set Page Config
st.set_page_config(page_title="Staff Payroll & History", layout="wide")

# 1. Initialize Data
if 'emp_data' not in st.session_state:
    st.session_state.emp_data = pd.DataFrame({
        "Name": ["Karishma", "Riya", "Saache", "Neha", "Bhumi", "Sahil"],
        "Base_Salary": [24000, 22000, 22000, 21000, 20000, 23000]
    })

if 'attendance' not in st.session_state:
    # Adding a dummy column to ensure proper date sorting later
    st.session_state.attendance = pd.DataFrame(columns=["Date", "Name", "Status"])

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["📝 Mark Attendance", "💰 Monthly Summary", "📅 History & Filters"])

# --- TAB 1: MARK ATTENDANCE ---
with tab1:
    st.header("Mark Daily Attendance")
    selected_date = st.date_input("Select Date", date.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    st.write(f"Marking for: **{selected_date.strftime('%d %B %Y')}**")
    
    for name in st.session_state.emp_data["Name"]:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write(f"**{name}**")
        with col2:
            existing = st.session_state.attendance[
                (st.session_state.attendance["Date"] == date_str) & 
                (st.session_state.attendance["Name"] == name)
            ]
            default_idx = 0
            if not existing.empty:
                status_val = existing.iloc[0]["Status"]
                default_idx = ["Present", "Leave", "Half-Day"].index(status_val)
            
            status = st.radio(f"Status for {name}", ["Present", "Leave", "Half-Day"], 
                              index=default_idx, horizontal=True, key=f"in_{name}_{date_str}")
            
            # Update Logic
            st.session_state.attendance = st.session_state.attendance[
                ~((st.session_state.attendance["Date"] == date_str) & 
                  (st.session_state.attendance["Name"] == name))
            ]
            if status != "Present":
                new_row = pd.DataFrame({"Date": [date_str], "Name": [name], "Status": [status]})
                st.session_state.attendance = pd.concat([st.session_state.attendance, new_row], ignore_index=True)

# --- TAB 2: MONTHLY SUMMARY ---
with tab2:
    st.header("Monthly Salary Calculation")
    # Rule: Base/26 per day. 1 Paid leave. 1000 Bonus if 0 leaves.
    
    def calculate_payout(row):
        emp_att = st.session_state.attendance[st.session_state.attendance["Name"] == row["Name"]]
        l_count = (emp_att["Status"] == "Leave").sum() * 1.0
        h_count = (emp_att["Status"] == "Half-Day").sum() * 0.5
        total_l = l_count + h_count
        
        bonus = 1000 if total_l == 0 else 0
        unpaid = max(0.0, total_l - 1.0)
        daily = row["Base_Salary"] / 26
        deduction = unpaid * daily
        
        return pd.Series([total_l, bonus, round(deduction), round(row["Base_Salary"] + bonus - deduction)])

    summary = st.session_state.emp_data.copy()
    summary[["Total Leaves", "Bonus (+)", "Deduction (-)", "Final Payout"]] = summary.apply(calculate_payout, axis=1)
    st.dataframe(summary, use_container_width=True, hide_index=True)
    
    with st.expander("Edit Base Salaries"):
        st.session_state.emp_data = st.data_editor(st.session_state.emp_data)

# --- TAB 3: HISTORY & FILTERS ---
with tab3:
    st.header("Detailed Attendance History")
    
    col_a, col_b = st.columns(2)
    with col_a:
        emp_filter = st.multiselect("Filter by Employee", options=st.session_state.emp_data["Name"].tolist(), default=st.session_state.emp_data["Name"].tolist())
    with col_b:
        date_range = st.date_input("Filter by Date Range", [date(2025, 1, 1), date.today()])

    # Filter the data
    history_df = st.session_state.attendance.copy()
    if not history_df.empty:
        history_df['Date'] = pd.to_datetime(history_df['Date']).dt.date
        
        # Apply Filters
        mask = (history_df["Name"].isin(emp_filter))
        if len(date_range) == 2:
            mask = mask & (history_df["Date"] >= date_range[0]) & (history_df["Date"] <= date_range[1])
        
        filtered_history = history_df[mask].sort_values(by="Date", ascending=False)
        
        if filtered_history.empty:
            st.warning("No leaves found for the selected filters.")
        else:
            st.table(filtered_history)
            
            # Download Button
            csv = filtered_history.to_csv(index=False).encode('utf-8')
            st.download_button("Download This Report (CSV)", csv, "attendance_report.csv", "text/csv")
    else:
        st.info("No attendance records found yet. All employees are currently marked 'Present'.")
