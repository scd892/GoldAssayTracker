import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import sys
import os
import io
import zipfile
import base64

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_samples_for_date_range, get_deviations_from_benchmark
from utils import export_data_to_csv
from auth import require_permission, display_access_denied, check_page_access

st.set_page_config(page_title="Data Export", page_icon="💾", layout="wide")

# Check authentication and permissions
if not check_page_access("Data_Export"):
    display_access_denied()
    st.stop()

st.title("Data Export")
st.markdown("Export data for further analysis in external tools.")

# Date range selection
st.header("Select Export Date Range")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", value=datetime.now())

if start_date > end_date:
    st.error("Error: End date must be after start date")
    st.stop()

# Data export options
st.header("Export Options")

export_type = st.radio(
    "Select data to export:",
    ["Raw Assay Results", "Deviation Analysis", "Complete Dataset"],
    horizontal=True
)

# Get the data based on selection
if export_type == "Raw Assay Results":
    data_df = get_samples_for_date_range(start_date, end_date)
    export_filename = f"gold_assay_results_{start_date}_to_{end_date}.csv"
    
    if data_df is not None and not data_df.empty:
        # Format data for export
        data_df['test_date'] = pd.to_datetime(data_df['test_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Preview data
        st.subheader("Data Preview")
        st.dataframe(data_df.head(10), use_container_width=True)
        st.info(f"Total records: {len(data_df)}")
    else:
        st.warning("No data found for the selected date range.")
        st.stop()

elif export_type == "Deviation Analysis":
    # Calculate days between dates
    days = (end_date - start_date).days + 1
    
    # Get deviation data
    data_df = get_deviations_from_benchmark(days=days)
    export_filename = f"gold_assay_deviations_{start_date}_to_{end_date}.csv"
    
    if data_df is not None and not data_df.empty:
        # Filter for date range
        data_df['test_date'] = pd.to_datetime(data_df['test_date'])
        data_df = data_df[
            (data_df['test_date'].dt.date >= start_date) & 
            (data_df['test_date'].dt.date <= end_date)
        ]
        
        if data_df.empty:
            st.warning("No deviation data found for the selected date range.")
            st.stop()
        
        # Format data for export
        data_df['test_date'] = data_df['test_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        data_df['absolute_deviation'] = data_df['absolute_deviation'].round(4)
        data_df['percentage_deviation'] = data_df['percentage_deviation'].round(2)
        
        # Preview data
        st.subheader("Data Preview")
        st.dataframe(data_df.head(10), use_container_width=True)
        st.info(f"Total records: {len(data_df)}")
    else:
        st.warning("No deviation data found for the selected date range.")
        st.stop()

else:  # Complete Dataset
    # We'll create a zip file with multiple CSVs
    conn = sqlite3.connect('gold_assay.db')
    
    # Get assayers
    assayers_df = pd.read_sql("SELECT * FROM assayers", conn)
    
    # Get benchmark history
    benchmark_df = pd.read_sql("""
        SELECT b.*, a.name 
        FROM benchmark_assayers b
        JOIN assayers a ON b.assayer_id = a.assayer_id
        ORDER BY b.set_date DESC
    """, conn)
    
    # Get raw results for date range
    results_query = f"""
        SELECT r.*, a.name as assayer_name
        FROM assay_results r
        JOIN assayers a ON r.assayer_id = a.assayer_id
        WHERE date(r.test_date) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY r.test_date
    """
    results_df = pd.read_sql(results_query, conn)
    
    conn.close()
    
    # Create data dictionary
    data_dict = {
        "assayers.csv": assayers_df,
        "benchmark_history.csv": benchmark_df,
        "assay_results.csv": results_df
    }
    
    # Add deviation data if there are results
    if not results_df.empty:
        # Calculate days between dates
        days = (end_date - start_date).days + 1
        
        # Get deviation data
        deviations_df = get_deviations_from_benchmark(days=days)
        
        if deviations_df is not None and not deviations_df.empty:
            # Filter for date range
            deviations_df['test_date'] = pd.to_datetime(deviations_df['test_date'])
            deviations_df = deviations_df[
                (deviations_df['test_date'].dt.date >= start_date) & 
                (deviations_df['test_date'].dt.date <= end_date)
            ]
            
            if not deviations_df.empty:
                # Format data for export
                deviations_df['test_date'] = deviations_df['test_date'].dt.strftime('%Y-%m-%d %H:%M:%S')
                data_dict["deviations.csv"] = deviations_df
    
    # Preview data
    st.subheader("Data Preview")
    
    tab1, tab2, tab3 = st.tabs(["Assayers", "Benchmark History", "Assay Results"])
    
    with tab1:
        st.dataframe(assayers_df, use_container_width=True)
    
    with tab2:
        if not benchmark_df.empty:
            benchmark_df['set_date'] = pd.to_datetime(benchmark_df['set_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(benchmark_df, use_container_width=True)
        else:
            st.info("No benchmark history available.")
    
    with tab3:
        if not results_df.empty:
            results_df['test_date'] = pd.to_datetime(results_df['test_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.dataframe(results_df.head(10), use_container_width=True)
            st.info(f"Total records: {len(results_df)}")
        else:
            st.info("No assay results available for the selected date range.")
    
    export_filename = f"gold_assay_full_export_{start_date}_to_{end_date}.zip"
    
    if all(df.empty for df in data_dict.values()):
        st.warning("No data found for the selected date range.")
        st.stop()

# Export functionality
st.header("Generate Export")

# Add export format options
export_format = st.radio(
    "Select export format:",
    ["CSV", "Excel"],
    horizontal=True
)

if st.button("Generate Export"):
    if export_type != "Complete Dataset":
        # Single file export
        if export_format == "CSV":
            csv = data_df.to_csv(index=False)
            
            # Create download link
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="{export_filename}">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("Export generated successfully!")
        else:  # Excel
            excel_filename = export_filename.replace(".csv", ".xlsx")
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                data_df.to_excel(writer, index=False, sheet_name="Data")
            
            # Create download link
            b64 = base64.b64encode(output.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{excel_filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("Export generated successfully!")
    else:
        # Zip file with multiple datasets
        if export_format == "CSV":
            # Create zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, df in data_dict.items():
                    if not df.empty:
                        zip_file.writestr(filename, df.to_csv(index=False))
            
            # Create download link
            b64 = base64.b64encode(zip_buffer.getvalue()).decode()
            href = f'<a href="data:application/zip;base64,{b64}" download="{export_filename}">Download Zip File</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("Export generated successfully!")
        else:  # Excel
            excel_filename = export_filename.replace(".zip", ".xlsx")
            
            # Create Excel file in memory with multiple sheets
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, df in data_dict.items():
                    if not df.empty:
                        # Strip .csv from sheet name and limit to 31 chars (Excel limit)
                        sheet = sheet_name.replace(".csv", "")[:31]
                        df.to_excel(writer, index=False, sheet_name=sheet)
            
            # Create download link
            b64 = base64.b64encode(output.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{excel_filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success("Export generated successfully!")

# Data retention notice
st.markdown("---")
st.markdown("""
**Data Retention Notice:**
- Exported data is not stored on our servers
- All exports are generated dynamically and only available for immediate download
- For data security, please store downloaded files securely
""")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888;'>"
    "© 2025 AEG Monitoring System<br>"
    "Developed by Algo Digital Solutions, powered by Mureri Technologies<br>"
    "All Rights Reserved"
    "</div>", 
    unsafe_allow_html=True
)

# Add the chat component from the shared module
import sys
import os
# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simple_chat import display_chat_widget
display_chat_widget()
