import json
import pandas as pd

# Load the metrics data
with open('metrics.json') as f:
    data = json.load(f)

# Convert data to a pandas DataFrame
df = pd.DataFrame(data['data']['result'])

# Extract timestamp and value
df['timestamp'] = df['value'].apply(lambda x: x[0])
df['value'] = df['value'].apply(lambda x: float(x[1]))

# Drop unnecessary columns
df = df[['timestamp', 'value']]

# Normalize the data
df['value'] = (df['value'] - df['value'].mean()) / df['value'].std()
print(df.info())
# Handle missing values
df = df.dropna()

# Save the preprocessed data
df.to_csv('preprocessed_metrics.csv', index=False)

# Verify the data
#print("Preprocessed Data:")
#print(df.head())
#print("\nSummary Statistics:")
#print(df.describe())
#print(df.info())
