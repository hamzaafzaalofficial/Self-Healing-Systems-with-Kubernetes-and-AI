# Self-Healing-Systems-with-Kubernetes-and-AI
Tasks: 

Setting Up a Kubernetes Cluster and dependencies: 



Select your choice for cluster Minikube for local development or deploying on cloud platforms like GKE, EKS, or AKS. I used Minikube cluster. 

 Using tools like kubectl and helm for cluster management.

Minikube setup:

curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/
Docker Setup:

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# Add the repository to Apt sources:
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
docker version
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin



Kubectl & Helm Setup: 

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod +x get_helm.sh
./get_helm.sh



Initializing Minikube cluster: 

minikube start --memory=6144 --cpus=4 --driver=docker --force
kubectl create namespace -n monitoring 




2. Setting up Prometheus & Grafana(optional) using prometheus stack: 

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update 
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring

kubectl edit svc -n monitoring prometheus-kube-prometheus-prometheus 
#change from ClusterIP to NodePort you might not be able to access the ui of #promethues for now. if want to access the prometheus ui then. then expose the #service using additional flag of address 0.0.0.0

Getting the metrics.json using below command: 

curl -G "http://192.168.49.2:32630/api/v1/query" --data-urlencode "query=rate(container_cpu_usage_seconds_total[1m])" -o metrics.json
3.  Setting up Python Environment: 

sudo apt update
sudo apt install python3 python3-pip
python3 --version
pip3 --version
pip3 install virtualenv
sudo apt install python3-virtualenv
python3 -m venv myenv
apt install python3.12-venv 
source myenv/bin/activate
python3 -m venv myenv
source myenv/bin/activate

Creating python dependencies in requirements.txt file: 

joblib==1.4.2
numpy==2.2.1
pandas==2.2.3
python-dateutil==2.9.0.post0
pytz==2024.2
scikit-learn==1.6.1
scipy==1.15.1
six==1.17.0
threadpoolctl==3.5.0
tzdata==2024.2   
Apply to install dependencies: 

pip install -r requirements.txt 


4. Pre-processing, Training & Testing: 

Creating a pre-processing.py file

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

Above code block will output a .csv file. 

Now our detection file will be applied. Create a detect_anomalies.py file: 

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
This code block will output a anomaly_model.pkl 



5. Creating a docker image for the above anomaly_model.pkl, requirements.txt etc.

Create a seperate directory and cd into it. 

mkdir test 
sudo test/
Create requirements.txt, Dockerfile and copying the anomaly_model.pkl from previous directory. 

a) requirements.txt 

requests==2.31.0
prometheus_client==0.20.0
joblib==1.4.2
numpy==2.2.1
pandas==2.2.3
python-dateutil==2.9.0.post0
pytz==2024.2
scikit-learn==1.6.1
scipy==1.15.1
six==1.17.0
threadpoolctl==3.5.0
tzdata==2024.2

b) Dockerfile 

FROM python:3.10-slim

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the script and model
COPY anomaly_detection_pipeline.py /app/anomaly_detection_pipeline.py
COPY anomaly_model.pkl /app/anomaly_model.pkl

# Set the working directory
WORKDIR /app

# Run the script
CMD ["python", "anomaly_detection_pipeline.py"]

c) 

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

d) copy the anomaly_model.pkl into this working directory. 



Finally build your docker image: 

eval $(minikube docker-env) # this will set your docker environment of minikube
docker build -t my_new_image .


6. Deploying the docker image to Minikube Cluster: 

kubectl create deployment anomaly-detection --image=my_new_image --n monitoring
#exposing the service 
kubectl expose deployment anomaly-detection --type=ClusterIP --port=8000 --target-port=8000 -n monitoring


7. Editing the Prometheus file to scrap the metrics exposed by running the image: 

 I used the below code to scrap the metric exposed by the container, but it was not running smooth. I invite you to change the below code for yourself. 

additionalScrapeConfigs:
  - job_name: 'anomaly-detection'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - monitoring
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_name]
        action: keep
        regex: anomaly-detection
    metrics_path: /metrics
    scheme: http
8. Adding a Prometheus rule:

apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: anomaly-alerts
  namespace: monitoring  # Ensure this matches the namespace where Prometheus is installed
  labels:
    release: prometheus  # This label must match the release label of your kube-prometheus-stack
spec:
  groups:
    - name: anomaly-alerts
      rules:
        - alert: AnomalyDetected
          expr: anomaly_detected == 1  # Use the metric exposed by your anomaly detection service
          for: 1m  # Alert if the condition is true for 1 minute
          labels:
            severity: critical
          annotations:
            summary: "Anomaly detected in system metrics"
            description: "An anomaly has been detected in the system metrics. Please investigate immediately."
9. Adding a HPA file:

apiVersion: autoscaling/v2beta2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric:
          name: requests_per_second
        target:
          type: AverageValue
          averageValue: 100