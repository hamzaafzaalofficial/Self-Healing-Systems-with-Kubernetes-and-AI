# Self-Healing Systems with Kubernetes and AI

This guide walks you through setting up a Kubernetes cluster using Minikube, deploying Prometheus and Grafana for monitoring, and creating an anomaly detection pipeline using Python and Docker.

---

## Table of Contents
# Setting Up Kubernetes Cluster(#setting-up-kubernetes-cluster)
# Minikube Setup(#minikube-setup)
# Docker Setup(#docker-setup)
# Kubectl & Helm Setup(#kubectl--helm-setup)
# Initializing Minikube Cluster(#initializing-minikube-cluster)
# Setting Up Prometheus & Grafana(#setting-up-prometheus--grafana)
# Fetching Metrics(#fetching-metrics)
# Setting Up Python Environment(#setting-up-python-environment)
# Pre-processing, Training & Testing (#pre-processing-training--testing)
# Creating Docker Image(#creating-docker-image)
# Deploying to Minikube Cluster(#deploying-to-minikube-cluster)
# Configuring Prometheus Scraping(#configuring-prometheus-scraping)
# Adding Prometheus Alert Rules(#adding-prometheus-alert-rules)
# Horizontal Pod Autoscaler (HPA)(#horizontal-pod-autoscaler-hpa)

---

## Setting Up Kubernetes Cluster

### Minikube Setup

```bash
# Download Minikube
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Make Minikube executable
chmod +x minikube

# Move Minikube to /usr/local/bin
sudo mv minikube /usr/local/bin/
# Docker Setup
# Update the package list
sudo apt-get update

# Install required packages
sudo apt-get install ca-certificates curl

# Create the directory for Docker's GPG key
sudo install -m 0755 -d /etc/apt/keyrings

# Add Docker's GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker's repository to Apt sources
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the package list again
sudo apt-get update

# Install Docker
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# Kubectl & Helm Setup

# Download kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Make kubectl executable
chmod +x kubectl

# Move kubectl to /usr/local/bin
sudo mv kubectl /usr/local/bin/

# Verify kubectl installation
kubectl version --client

# Download and install Helm
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod +x get_helm.sh
./get_helm.sh
# Initializing Minikube Cluster

# Start Minikube with 6GB RAM and 4 CPUs
minikube start --memory=6144 --cpus=4 --driver=docker --force

# Create a namespace for monitoring
kubectl create namespace monitoring
```

---

### Setting Up Prometheus & Grafana

---

```bash
# Add the Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# Update Helm repositories
helm repo update

# Install the Prometheus stack
helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring

# Expose Prometheus UI
kubectl edit svc -n monitoring prometheus-kube-prometheus-prometheus
# Change `ClusterIP` to `NodePort`
# Fetching Metrics
# Fetch CPU usage metrics from Prometheus
curl -G "http://192.168.49.2:32630/api/v1/query" --data-urlencode "query=rate(container_cpu_usage_seconds_total[1m])" -o metrics.json
```
--- 
### Setting Up Python Environment
--- 

```bash
# Update the package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-virtualenv

# Create a virtual environment
python3 -m venv myenv

# Activate the virtual environment
source myenv/bin/activate
# Install dependencies from requirements.txt:

pip install -r requirements.txt
```
--- 

### Pre-processing, Training & Testing
### Pre-processing Script (pre-processing.py)

```bash
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

# Normalize the data
df['value'] = (df['value'] - df['value'].mean()) / df['value'].std()

# Save the preprocessed data
df.to_csv('preprocessed_metrics.csv', index=False)
# Anomaly Detection Script (detect_anomalies.py)

import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

# Load the preprocessed data
df = pd.read_csv('preprocessed_metrics.csv')

# Train the Isolation Forest model
model = IsolationForest(contamination=0.01)
model.fit(df[['value']])

# Predict anomalies
df['anomaly'] = model.predict(df[['value']])

# Save the trained model
joblib.dump(model, 'anomaly_model.pkl')
Creating Docker Image
# Create a directory and copy the necessary files:

mkdir test
cd test
cp ../anomaly_model.pkl .
cp ../requirements.txt .

# Create a Dockerfile:


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
# Build the Docker image:

# Set Docker environment to Minikube
eval $(minikube docker-env)
```
---
### Build the Docker image
---
```bash
docker build -t my_new_image .
```
---
# Deploying to Minikube Cluster
---
```bash
# Create a deployment for the anomaly detection service
kubectl create deployment anomaly-detection --image=my_new_image --namespace monitoring

# Expose the deployment as a ClusterIP service
kubectl expose deployment anomaly-detection --type=ClusterIP --port=8000 --target-port=8000 -n monitoring

```
---

# Configuring Prometheus Scraping Add the following to your Prometheus configuration to scrape metrics from the anomaly detection service:
---
```bash

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
```

---
### Adding Prometheus Alert Rules
### Create a PrometheusRule resource to alert on anomalies:
```bash
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: anomaly-alerts
  namespace: monitoring
  labels:
    release: prometheus
spec:
  groups:
    - name: anomaly-alerts
      rules:
        - alert: AnomalyDetected
          expr: anomaly_detected == 1
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Anomaly detected in system metrics"
            description: "An anomaly has been detected in the system metrics. Please investigate immediately."

```
---            
### Horizontal Pod Autoscaler (HPA)
# Create an HPA to scale your application based on metrics:
###
```bash
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
```