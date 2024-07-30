import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
file_path = 'data-sa-crime-q1q3-2023-24.csv'  # Adjust this path if necessary
data = pd.read_csv(file_path)

# Filter the data for the specified suburbs
suburbs_of_interest = ['PARKSIDE', 'UNLEY', 'FULLARTON', 'EASTWOOD']
filtered_data = data[data['Suburb - Incident'].isin(suburbs_of_interest)]

# Convert the Reported Date to datetime format for time series analysis
filtered_data['Reported Date'] = pd.to_datetime(filtered_data['Reported Date'], format='%d/%m/%Y')

# Extract the month from the reported date and convert to string for plotting
filtered_data['Month'] = filtered_data['Reported Date'].dt.to_period('M').astype(str)

# Get unique values for Level 1, Level 2, and Level 3 offence descriptions
level1_offences = ['All Data'] + filtered_data['Offence Level 1 Description'].unique().tolist()
level2_offences = ['All Data'] + filtered_data['Offence Level 2 Description'].unique().tolist()
level3_offences = ['All Data'] + filtered_data['Offence Level 3 Description'].unique().tolist()

# Streamlit app
st.title('Crime Data Analysis for Selected Suburbs')

# Sidebar for instructions, header, and dropdown lists
st.sidebar.title('Instructions')
st.sidebar.markdown("Visualisation of SAPOL crime statistics from the SA Government Data Portal. [View the dataset here](https://data.sa.gov.au/data/dataset/crime-statistics). Data covers July 2023 to March 2024 only.")

st.sidebar.markdown("Select a suburb or offence level to display specific charts.")

st.sidebar.title('Filter Options')
selected_suburb = st.sidebar.selectbox('Select a Suburb', suburbs_of_interest)
selected_level1 = st.sidebar.selectbox('Select Level 1 Offence', level1_offences)

# Filter Level 2 offences based on selected Level 1 offence
if selected_level1 == 'All Data':
    filtered_level2_offences = ['All Data'] + filtered_data['Offence Level 2 Description'].unique().tolist()
else:
    filtered_level2_offences = ['All Data'] + filtered_data[filtered_data['Offence Level 1 Description'] == selected_level1]['Offence Level 2 Description'].unique().tolist()

selected_level2 = st.sidebar.selectbox('Select Level 2 Offence', filtered_level2_offences)

# Filter Level 3 offences based on selected Level 2 offence
if selected_level2 == 'All Data':
    filtered_level3_offences = ['All Data'] + filtered_data['Offence Level 3 Description'].unique().tolist()
else:
    filtered_level3_offences = ['All Data'] + filtered_data[filtered_data['Offence Level 2 Description'] == selected_level2]['Offence Level 3 Description'].unique().tolist()

selected_level3 = st.sidebar.selectbox('Select Level 3 Offence', filtered_level3_offences)

# Filter data based on selected Level 1, Level 2, and Level 3 offences
suburb_data = filtered_data[filtered_data['Suburb - Incident'] == selected_suburb]

offence_data = suburb_data
if selected_level1 != 'All Data':
    offence_data = offence_data[offence_data['Offence Level 1 Description'] == selected_level1]
if selected_level2 != 'All Data':
    offence_data = offence_data[offence_data['Offence Level 2 Description'] == selected_level2]
if selected_level3 != 'All Data':
    offence_data = offence_data[offence_data['Offence Level 3 Description'] == selected_level3]

# Group by month and sum the offence counts
monthly_offences = offence_data.groupby('Month')['Offence count'].sum().reset_index()

# Plot monthly offences
st.subheader(f'Monthly Offences in {selected_suburb}')
fig1 = px.line(monthly_offences, x='Month', y='Offence count', markers=True, title=f'Monthly Offences in {selected_suburb}')
st.plotly_chart(fig1)

# Group by month and Level 3 offence description
monthly_offences_level3 = offence_data.groupby(['Month', 'Offence Level 3 Description'])['Offence count'].sum().unstack(fill_value=0).reset_index()

# Melt the dataframe for plotly express compatibility
monthly_offences_level3_melted = monthly_offences_level3.melt(id_vars='Month', var_name='Offence Level 3 Description', value_name='Offence count')

# Plot stacked bar chart of monthly offences by Level 3 offence type
st.subheader(f'Monthly Offences in {selected_suburb} by Offence Type')
fig2 = px.bar(monthly_offences_level3_melted, x='Month', y='Offence count', color='Offence Level 3 Description', title=f'Monthly Offences in {selected_suburb} by Offence Type')
st.plotly_chart(fig2)

# Trend comparison across suburbs
# Group by suburb and month, summing the offence counts
suburb_trends = filtered_data.groupby(['Suburb - Incident', 'Month'])['Offence count'].sum().reset_index()

# Plot multi-line chart
st.subheader('Monthly Offence Trends Comparison Across Suburbs')
fig3 = px.line(suburb_trends, x='Month', y='Offence count', color='Suburb - Incident', title='Monthly Offence Trends Comparison Across Suburbs')
st.plotly_chart(fig3)

# Distribution of Level 1 Offence Types
level1_distribution = suburb_data['Offence Level 1 Description'].value_counts().reset_index()
level1_distribution.columns = ['Offence Level 1 Description', 'Count']

# Plot pie chart for Level 1 Offences
st.subheader(f'Distribution of Level 1 Offence Types in {selected_suburb}')
fig4 = px.pie(level1_distribution, values='Count', names='Offence Level 1 Description', title=f'Distribution of Level 1 Offence Types in {selected_suburb}')
st.plotly_chart(fig4)

# Distribution of Level 2 Offence Types
level2_distribution = suburb_data['Offence Level 2 Description'].value_counts().reset_index()
level2_distribution.columns = ['Offence Level 2 Description', 'Count']

# Plot pie chart for Level 2 Offences
st.subheader(f'Distribution of Level 2 Offence Types in {selected_suburb}')
fig5 = px.pie(level2_distribution, values='Count', names='Offence Level 2 Description', title=f'Distribution of Level 2 Offence Types in {selected_suburb}')
st.plotly_chart(fig5)

# Distribution of Level 3 Offence Types
level3_distribution = suburb_data['Offence Level 3 Description'].value_counts().reset_index()
level3_distribution.columns = ['Offence Level 3 Description', 'Count']

# Plot pie chart for Level 3 Offences
st.subheader(f'Distribution of Level 3 Offence Types in {selected_suburb}')
fig6 = px.pie(level3_distribution, values='Count', names='Offence Level 3 Description', title=f'Distribution of Level 3 Offence Types in {selected_suburb}')
st.plotly_chart(fig6)



# Add footer
st.markdown("---")
st.markdown("@morebento July 2024")
