# 
FROM python:3.12-slim

WORKDIR /app

# Install libraries
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app to the container
COPY ./app ./app
