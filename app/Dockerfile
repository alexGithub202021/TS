# Use the official Python image from Docker Hub
FROM python:latest
# FROM arm64v8/python:2.7

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN mkdir ts

RUN chmod 777 -R ts

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run app.py when the container launches
CMD ["python3", "app.py"]