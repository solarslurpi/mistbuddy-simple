# Use the specified base image
FROM dtcooper/raspberrypi-os:python3.12-bookworm

# Set the working directory in the container
WORKDIR /usr/app

# Install build-essential and clean up
RUN apt-get update && apt-get install -y build-essential && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /usr/app/src
COPY GrowBuddies_shared/ /usr/app/GrowBuddies_shared

# Set environment variables for the application
ENV PYTHONPATH=/usr/app/src:/usr/app/GrowBuddies_shared
ENV SHARED_PATH=/usr/app/GrowBuddies_shared

# Expose port 8080
EXPOSE 8080

# Define the default command to run the application
CMD ["python", "/usr/app/src/mistbuddy_lite.py"]
