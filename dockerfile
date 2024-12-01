# Use a specific Python version
FROM dtcooper/raspberrypi-os:python3.12

# Set the working directory in the container
WORKDIR /usr/app

# Install curl and rust dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN . "/root/.cargo/env" && pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /usr/app/src
COPY mistbuddy_lite.py /usr/app/

# Set environment variables for the application
ENV PYTHONPATH=/usr/app

# Expose port 8085
EXPOSE 8085

# Define the default command to run the application
CMD ["python", "/usr/app/mistbuddy_lite.py"]