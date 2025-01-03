import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import re

# ----------------------------
# Streamlit Page Configuration
# ----------------------------
st.set_page_config(
    page_title="Crime Data Analysis for Selected Suburbs",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        ### Crime Data Analysis App
        Developed by @morebento July 2024

        Visualization of SAPOL crime statistics from the SA Government Data Portal.
        """
    }
)

# ----------------------------
# Data Loading and Caching
# ----------------------------
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """
    Loads and preprocesses the crime data from a Parquet file.
    Caches the data to optimize performance.

    Parameters:
    - file_path (str): Path to the Parquet file.

    Returns:
    - pd.DataFrame: Preprocessed crime data.
    """
    dtype = {
        'Offence count': 'int32',
        'Offence Level 1 Description': 'category',
        'Offence Level 2 Description': 'category',
        'Offence Level 3 Description': 'category',
        'Suburb - Incident': 'category'
        # Add other columns and their types as necessary
    }
    # Load data from Parquet
    data = pd.read_parquet(file_path, engine='pyarrow')
    
    # Convert data types for optimization
    for col, col_type in dtype.items():
        if col in data.columns:
            data[col] = data[col].astype(col_type)
    
    # Ensure 'Reported Date' is in datetime format
    data['Reported Date'] = pd.to_datetime(data['Reported Date'], format='%d/%m/%Y')
    
    # Extract month for analysis
    data['Month'] = data['Reported Date'].dt.to_period('M').astype(str)
    
    return data

# ----------------------------
# Helper Functions
# ----------------------------

def filter_offence_levels(data: pd.DataFrame, selected_level1: str, selected_level2: str) -> pd.DataFrame:
    """
    Filters data based on selected Level 1 and Level 2 offences.

    Parameters:
    - data (pd.DataFrame): The crime data.
    - selected_level1 (str): Selected Level 1 offence.
    - selected_level2 (str): Selected Level 2 offence.

    Returns:
    - pd.DataFrame: Filtered data.
    """
    if selected_level1 != 'All Data':
        data = data[data['Offence Level 1 Description'] == selected_level1]
    if selected_level2 != 'All Data':
        data = data[data['Offence Level 2 Description'] == selected_level2]
    return data

def sanitize_filename(name: str) -> str:
    """
    Sanitizes the suburb name to create a filesystem-friendly filename.

    Parameters:
    - name (str): The suburb name to sanitize.

    Returns:
    - str: Sanitized filename component.
    """
    # Replace spaces with underscores and remove non-alphanumeric characters
    sanitized = re.sub(r'\s+', '_', name)
    sanitized = re.sub(r'[^\w\-]', '', sanitized)
    return sanitized

def download_csv(data: pd.DataFrame) -> BytesIO:
    """
    Converts a DataFrame to a downloadable CSV.

    Parameters:
    - data (pd.DataFrame): The data to convert.

    Returns:
    - BytesIO: In-memory binary stream of the CSV.
    """
    csv_buffer = BytesIO()
    data.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer

# ----------------------------
# Main Application Function
# ----------------------------
def main():
    # ----------------------------
    # Load Data
    # ----------------------------
    file_path = 'filtered-data-sa-crime.parquet'  # Path to the Parquet file
    data = load_data(file_path)
    
    # ----------------------------
    # Sidebar Configuration
    # ----------------------------
    st.sidebar.title('Filter Options')
    
    # Dynamic Suburb Selection (Single Selection)
    suburbs_of_interest = sorted(data['Suburb - Incident'].unique().tolist())
    selected_suburb = st.sidebar.selectbox(
        'Select Suburb',
        options=suburbs_of_interest,
        index=0,
        help="Select a suburb to analyze."
    )
    
    # Offence Level 1 Selection
    level1_offences = ['All Data'] + sorted(data['Offence Level 1 Description'].unique().tolist())
    selected_level1 = st.sidebar.selectbox(
        'Select Level 1 Offence',
        options=level1_offences,
        index=0,
        help="Select a Level 1 offence to filter the data."
    )
    
    # Offence Level 2 Selection based on Level 1
    if selected_level1 == 'All Data':
        filtered_level2_offences = ['All Data'] + sorted(data['Offence Level 2 Description'].unique().tolist())
    else:
        filtered_level2_offences = ['All Data'] + sorted(
            data[data['Offence Level 1 Description'] == selected_level1]['Offence Level 2 Description'].unique().tolist()
        )
    selected_level2 = st.sidebar.selectbox(
        'Select Level 2 Offence',
        options=filtered_level2_offences,
        index=0,
        help="Select a Level 2 offence to further filter the data."
    )
    
    # Offence Level 3 Selection based on Level 2
    if selected_level2 == 'All Data':
        filtered_level3_offences = ['All Data'] + sorted(data['Offence Level 3 Description'].unique().tolist())
    else:
        filtered_level3_offences = ['All Data'] + sorted(
            data[data['Offence Level 2 Description'] == selected_level2]['Offence Level 3 Description'].unique().tolist()
        )
    selected_level3 = st.sidebar.selectbox(
        'Select Level 3 Offence',
        options=filtered_level3_offences,
        index=0,
        help="Select a Level 3 offence to further filter the data."
    )
    
    # ----------------------------
    # Apply Filters
    # ----------------------------
    filtered_data = data[data['Suburb - Incident'] == selected_suburb]
    filtered_data = filter_offence_levels(filtered_data, selected_level1, selected_level2)
    if selected_level3 != 'All Data':
        filtered_data = filtered_data[filtered_data['Offence Level 3 Description'] == selected_level3]
    
    # ----------------------------
    # Display Summary Statistics
    # ----------------------------
    st.markdown("## Summary Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        total_offences = filtered_data['Offence count'].sum()
        st.metric("Total Offences", f"{total_offences}")
    with col2:
        unique_offences = filtered_data['Offence Level 3 Description'].nunique()
        st.metric("Unique Offence Types", f"{unique_offences}")
    with col3:
        months = filtered_data['Month'].nunique()
        st.metric("Number of Months", f"{months}")
    
    st.markdown("---")
    
    # ----------------------------
    # Check if Filtered Data is Empty
    # ----------------------------
    if filtered_data.empty:
        st.warning("No data available for the selected filters. Please adjust your selections.")
        return
    
    # ----------------------------
    # Layout Using Tabs
    # ----------------------------
    tabs = st.tabs(["Instructions", "Monthly Offences", "Offence Types", "Trends Comparison", "Offence Heat Map", "Data Download"])
    
    # ----------------------------
    # Tab 1: Instructions
    # ----------------------------
    with tabs[0]:
        st.title("Instructions")
        st.markdown("""
        ### Welcome to the Crime Data Analysis App

        This application allows you to explore and analyze crime statistics for selected suburbs in South Australia. Below is a guide on how to navigate and utilize the app effectively.

        #### **Sidebar Filters**

        - **Select Suburb:**
          - Choose a specific suburb from the dropdown to analyze its crime data.
        
        - **Select Level 1 Offence:**
          - Filter the data based on high-level offence categories.
          - Selecting "All Data" includes all Level 1 offences.
        
        - **Select Level 2 Offence:**
          - Further refine your analysis by selecting a more specific offence category under Level 1.
          - If "All Data" is selected at Level 1, this will include all Level 2 offences.
        
        - **Select Level 3 Offence:**
          - Drill down to the most specific offence categories.
          - Similar to Level 2, selecting "All Data" will include all Level 3 offences.

        #### **Tabs Overview**

        - **Monthly Offences:**
          - Displays a line chart showing the total number of offences reported each month.
          - Includes a 3-month moving average to highlight trends over time.
        
        - **Offence Types:**
          - Provides a pie chart distribution of offences based on the selected offence level.
          - Choose between Level 1, Level 2, or Level 3 offences to visualize their distribution.
        
        - **Trends Comparison:**
          - Compares monthly offence trends across all suburbs.
          - Useful for identifying patterns or anomalies in different areas.
        
        - **Offence Heat Map:**
          - Presents a heat map with Level 2 offences on the Y-axis and suburbs on the X-axis.
          - The color intensity represents the total number of offences, allowing for quick identification of hotspots.
        
        - **Data Download:**
          - Enables you to download the filtered crime data as a CSV file.
          - Also provides options to download the visualizations (charts and heat maps) as PNG images.

        #### **How to Use the App**

        1. **Apply Filters:**
           - Start by selecting the suburb and offence levels from the sidebar to filter the data according to your interests.

        2. **Explore Visualizations:**
           - Navigate through the tabs to view different aspects of the data.
           - Use the interactive charts to hover over data points for more detailed information.

        3. **Download Data and Visualizations:**
           - In the "Data Download" tab, use the provided buttons to export your data and charts for offline analysis or reporting.

        #### **Tips for Effective Analysis**

        - **Comparative Analysis:**
          - Use the "Trends Comparison" tab to compare crime trends across multiple suburbs, helping identify areas with increasing or decreasing offences.

        - **Identifying Hotspots:**
          - The "Offence Heat Map" is particularly useful for pinpointing suburbs with high concentrations of specific offences.

        - **Long-Term Trends:**
          - The moving average in the "Monthly Offences" chart smooths out short-term fluctuations, revealing underlying trends over longer periods.


        """)

    # ----------------------------
    # Tab 2: Monthly Offences
    # ----------------------------
    with tabs[1]:
        st.subheader('Monthly Offences')
        monthly_offences = filtered_data.groupby('Month')['Offence count'].sum().reset_index()
        
        # Sort the data by Month to ensure correct chronological order
        monthly_offences = monthly_offences.sort_values('Month')
        
        # Calculate the 3-Month Moving Average
        monthly_offences['Moving Average'] = monthly_offences['Offence count'].rolling(window=3).mean()
        
        # Create the initial line chart for Offence Count
        fig1 = px.line(
            monthly_offences,
            x='Month',
            y='Offence count',
            markers=True,
            title='Monthly Offences with 3-Month Moving Average',
            labels={'Offence count': 'Number of Offences', 'Month': 'Month'}
        )
        
        # Add the Moving Average trace
        fig1.add_trace(
            go.Scatter(
                x=monthly_offences['Month'],
                y=monthly_offences['Moving Average'],
                mode='lines',
                name='3-Month Moving Average',
                line=dict(color='orange', dash='dash')
            )
        )
        
        # Set y-axis origin to 0 and adjust layout
        fig1.update_layout(
            xaxis_tickangle=-45,
            yaxis=dict(rangemode='tozero'),  # Ensures y-axis starts at 0
            legend=dict(x=0, y=1.0)
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    # ----------------------------
    # Tab 3: Offence Types Distribution
    # ----------------------------
    with tabs[2]:
        st.subheader('Offence Types Distribution')
        offence_levels = ['Level 1', 'Level 2', 'Level 3']
        selected_level = st.selectbox(
            'Select Offence Level for Distribution', 
            options=offence_levels, 
            help="Choose the offence level to visualize distribution."
        )
        
        if selected_level == 'Level 1':
            distribution = filtered_data['Offence Level 1 Description'].value_counts().reset_index()
            distribution.columns = ['Offence Level 1 Description', 'Count']
            title = 'Distribution of Level 1 Offence Types'
        elif selected_level == 'Level 2':
            distribution = filtered_data['Offence Level 2 Description'].value_counts().reset_index()
            distribution.columns = ['Offence Level 2 Description', 'Count']
            title = 'Distribution of Level 2 Offence Types'
        else:
            distribution = filtered_data['Offence Level 3 Description'].value_counts().reset_index()
            distribution.columns = ['Offence Level 3 Description', 'Count']
            title = 'Distribution of Level 3 Offence Types'
        
        fig2 = px.pie(
            distribution,
            values='Count',
            names=distribution.columns[0],
            title=title,
            hole=0.3
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # ----------------------------
    # Tab 4: Trends Comparison
    # ----------------------------
    with tabs[3]:
        st.subheader('Monthly Offence Trends Comparison Across Suburbs')
        # Aggregate data for all suburbs to enable comparison
        suburb_trends = data.groupby(['Suburb - Incident', 'Month'])['Offence count'].sum().reset_index()
        fig3 = px.line(
            suburb_trends,
            x='Month',
            y='Offence count',
            color='Suburb - Incident',
            markers=True,
            title='Monthly Offence Trends Comparison Across Suburbs',
            labels={'Offence count': 'Number of Offences', 'Month': 'Month'}
        )
        fig3.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
    
    # ----------------------------
    # Tab 5: Offence Heat Map
    # ----------------------------
    with tabs[4]:
        st.subheader('Offence Heat Map')
        
        # Aggregate total Level 2 offences per suburb
        heatmap_data = data.groupby(['Offence Level 2 Description', 'Suburb - Incident'])['Offence count'].sum().reset_index()
        
        # Pivot the data to have Level 2 offences as rows and suburbs as columns
        heatmap_pivot = heatmap_data.pivot(index='Offence Level 2 Description', columns='Suburb - Incident', values='Offence count').fillna(0)
        
        # Optional: Sort the offences and suburbs for better visualization
        heatmap_pivot = heatmap_pivot.sort_index()
        
        # Create the heat map using Plotly Express
        fig_heatmap = px.imshow(
            heatmap_pivot,
            labels=dict(x="Suburb", y="Level 2 Offence", color="Total Offences"),
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            color_continuous_scale='Viridis',
            aspect="auto",
            title="Heat Map of Level 2 Offences Across Suburbs"
        )
        
        fig_heatmap.update_layout(
            xaxis_tickangle=-45,
            yaxis=dict(tickmode='linear'),
            coloraxis_colorbar=dict(title="Total Offences")
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # ----------------------------
    # Tab 6: Data Download
    # ----------------------------
    with tabs[5]:
        st.subheader('Download Data and Visualizations')
        csv_buffer = download_csv(filtered_data)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv_buffer,
            file_name='filtered_crime_data.csv',
            mime='text/csv'
        )
        st.markdown("### Download Visualizations")
        # Sanitize the suburb name for filename
        sanitized_suburb = sanitize_filename(selected_suburb)
        fig1_bytes = fig1.to_image(format="png")
        st.download_button(
            label="Download Monthly Offences Plot",
            data=fig1_bytes,
            file_name=f'monthly_offences_{sanitized_suburb}.png',
            mime='image/png'
        )
        fig_heatmap_bytes = fig_heatmap.to_image(format="png")
        st.download_button(
            label="Download Offence Heat Map",
            data=fig_heatmap_bytes,
            file_name=f'offence_heatmap_{sanitized_suburb}.png',
            mime='image/png'
        )
        # Add additional download buttons for other plots if desired
    
    # ----------------------------
    # Footer
    # ----------------------------
    st.markdown("---")
    st.markdown("© morebento January 2025")

# ----------------------------
# Run the Application
# ----------------------------
if __name__ == "__main__":
    main()
