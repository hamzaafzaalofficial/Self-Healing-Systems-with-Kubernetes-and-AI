import joblib
import pandas as pd

# Load the trained model
model = joblib.load('/app/anomaly_model.pkl')

# Function to detect anomalies
def detect_anomalies(data):
    # Convert input data to a DataFrame
    df = pd.DataFrame(data, columns=['value'])

    # Predict anomalies
    df['anomaly'] = model.predict(df[['value']])

    # Return anomalies
    anomalies = df[df['anomaly'] == -1]
    return anomalies.to_dict(orient='records')

# Example usage (for testing)
if __name__ == "__main__":
    # Example input data
    input_data = {'value': [0.12, 0.45, 0.78, 1.23, 0.56]}

    # Detect anomalies
    anomalies = detect_anomalies(input_data)
    print("Detected Anomalies:", anomalies)
