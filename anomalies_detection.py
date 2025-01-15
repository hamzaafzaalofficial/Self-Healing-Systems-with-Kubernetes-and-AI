import requests
import time
import joblib
import pandas as pd
from prometheus_client import start_http_server, Gauge

# Load the trained model
model = joblib.load('/app/anomaly_model.pkl')

# Create a Prometheus gauge metric
anomaly_metric = Gauge('anomaly_detected', 'Anomaly detection output (1 = anomaly, 0 = normal)')

# Prometheus API URL
PROMETHEUS_URL = "http://64.227.140.195:9091/api/v1/query"  # Replace with your Prometheus URL

# Function to fetch CPU usage metrics from Prometheus
def fetch_metrics():
    query = 'rate(container_cpu_usage_seconds_total[1m])'  # Query for CPU usage
    response = requests.get(PROMETHEUS_URL, params={'query': query})
    data = response.json()
    return data['data']['result']

# Function to pre-process metrics
def preprocess_metrics(metrics):
    # Example: Extract values and convert to a DataFrame
    values = [float(metric['value'][1]) for metric in metrics]
    df = pd.DataFrame(values, columns=['value'])
    return df

# Function to detect anomalies
def detect_anomalies(df):
    df['anomaly'] = model.predict(df[['value']])
    anomalies = df[df['anomaly'] == -1]
    return anomalies.to_dict(orient='records')

# Main loop
def main():
    # Start Prometheus HTTP server on port 8000
    start_http_server(8000)

    while True:
        # Fetch metrics from Prometheus
        metrics = fetch_metrics()

        # Pre-process metrics
        df = preprocess_metrics(metrics)

        # Detect anomalies
        anomalies = detect_anomalies(df)

        # Set the Prometheus metric based on anomaly detection
        if len(anomalies) > 0:
            anomaly_metric.set(1)  # Anomaly detected
        else:
            anomaly_metric.set(0)  # No anomaly detected

        # Sleep for a while before checking again
        time.sleep(60)  # Adjust the interval as needed

if __name__ == "__main__":
    main()
