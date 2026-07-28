FROM python:3.13-slim

WORKDIR /app

# Install ExifTool
RUN apt-get update && \
    apt-get install -y libimage-exiftool-perl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Start the application with gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app
