# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code (except things in .dockerignore)
COPY . .

# Use .env file passed at runtime (via --env-file)

# Run the app
CMD ["python", "main.py"]
