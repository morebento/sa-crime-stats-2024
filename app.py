import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  # Import Graph Objects for adding traces
from io import BytesIO
import re

# Set Streamlit page configuration
st.set_page_config(
    page_title="Crime Data Analysis for Selected Suburbs",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "### Crime Data Analysis App\nDeveloped by @morebento July 2024\n\nVisualization of SAPOL crime statistics from the SA Government Data Portal."
    }
)

@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """
    Loads and preprocesses the crime data from a CSV file.
    Caches the data to optimize performance.
    
    Parameters:
    - file_path (str): Path to the CSV file.

    Returns:
    - pd.DataFrame: Preprocessed crime data.
    """
    data = pd.read_csv(file_path)
    # Convert 'Reported Date' to datetime
    data['Reported Date'] = pd.to_datetime(data['Reported Date'], format='%d/%m/%Y')
    # Extract month for analysis
    data['Month'] = data['Reported Date'].dt.to_period('M').astype(str)
    return data

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

def main():
    # Load pre-filtered data
    file_path = 'filtered-data-sa-crime.csv'  # Path to the filtered CSV
    data = load_data(file_path)
    
    # Sidebar Configuration
    st.sidebar.title('Instructions')
    st.sidebar.markdown("""
    Visualization of SAPOL crime statistics from the SA Government Data Portal. 
    [View the dataset here](https://data.sa.gov.au/data/dataset/crime-statistics). 
    Data covers July 2023 to September 2024 only.
    
    **Filter Options:**
    - Select a suburb and offence levels to display specific charts.
    """)
    
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
    
    # Apply Filters
    filtered_data = data[data['Suburb - Incident'] == selected_suburb]
    filtered_data = filter_offence_levels(filtered_data, selected_level1, selected_level2)
    if selected_level3 != 'All Data':
        filtered_data = filtered_data[filtered_data['Offence Level 3 Description'] == selected_level3]
    
    # Display Summary Statistics
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
    
    # Check if filtered data is empty
    if filtered_data.empty:
        st.warning("No data available for the selected filters. Please adjust your selections.")
        return
    
    # Layout using Tabs for better organization
    tabs = st.tabs(["Monthly Offences", "Offence Types", "Trends Comparison", "Offence Heat Map", "Data Download"])
    
    with tabs[0]:
        st.subheader('Monthly Offences')
        monthly_offences = filtered_data.groupby('Month')['Offence count'].sum().reset_index()
        
        # Sort the data by Month to ensure correct order
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
        
    with tabs[1]:
        st.subheader('Offence Types Distribution')
        offence_levels = ['Level 1', 'Level 2', 'Level 3']
        selected_level = st.selectbox('Select Offence Level for Distribution', options=offence_levels, help="Choose the offence level to visualize distribution.")
        
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
    
    with tabs[2]:
        st.subheader('Monthly Offence Trends Comparison Across Suburbs')
        # Since only one suburb is selected, this chart will display a single line.
        # To maintain functionality, we can still plot trends across all pre-filtered suburbs.
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
    
    with tabs[3]:
        st.subheader('Offence Heat Map')
        
        # Aggregate total Level 2 offences per suburb
        heatmap_data = data.groupby(['Offence Level 2 Description', 'Suburb - Incident'])['Offence count'].sum().reset_index()
        
        # Pivot the data to have Level 2 offences as rows and suburbs as columns
        heatmap_pivot = heatmap_data.pivot(index='Offence Level 2 Description', columns='Suburb - Incident', values='Offence count').fillna(0)
        
        # Optional: Sort the offences and suburbs for better visualization
        heatmap_pivot = heatmap_pivot.sort_index()
        
        # Create the heat map
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
    
    with tabs[4]:
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
        # Similarly, add download buttons for other plots if desired
        # Example for Heat Map
        fig_heatmap_bytes = fig_heatmap.to_image(format="png")
        st.download_button(
            label="Download Offence Heat Map",
            data=fig_heatmap_bytes,
            file_name=f'offence_heatmap_{sanitized_suburb}.png',
            mime='image/png'
        )
    
    # Footer
    st.markdown("---")
    st.markdown("© morebento January 2025")

if __name__ == "__main__":
    main()
