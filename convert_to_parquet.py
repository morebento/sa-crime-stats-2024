import pandas as pd

# Load the CSV data
csv_file = 'filtered-data-sa-crime.csv'
df = pd.read_csv(csv_file)

# Optionally, specify data types to optimize storage
# For example:
# df['Offence count'] = df['Offence count'].astype('int32')

# Save as Parquet
parquet_file = 'filtered-data-sa-crime.parquet'
df.to_parquet(parquet_file, engine='pyarrow', compression='snappy')
