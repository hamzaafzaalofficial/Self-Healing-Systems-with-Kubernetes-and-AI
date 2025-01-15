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
