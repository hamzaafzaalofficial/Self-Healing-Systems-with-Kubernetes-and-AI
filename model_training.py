import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# Load the preprocessed data
df = pd.read_csv('preprocessed_metrics.csv')

# Prepare the features
X = df[['value']]

# Initialize and train the Isolation Forest model
model = IsolationForest(contamination=0.01)
model.fit(X)

# Predict anomalies
df['anomaly'] = model.predict(X)

# Identify anomalies
anomalies = df[df['anomaly'] == -1]
print(f"Number of anomalies detected: {len(anomalies)}")

# Save the trained model
joblib.dump(model, 'anomaly_model.pkl')
