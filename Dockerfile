# Use Python 3.10 slim as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container
COPY . .

# Set the environment variable for any necessary variables like API keys (optional)
# ENV API_KEY="your_api_key_here"

# Run the script when the container starts
CMD ["python", "main.py"]
