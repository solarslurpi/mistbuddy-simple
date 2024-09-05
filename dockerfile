# Use the specified base image
FROM dtcooper/raspberrypi-os:python

# Set the working directory in the container
WORKDIR /usr/app

# Install curl
# Download and install rust. This container uses FastAPI. Even with fastapi-slim,
# orjson is included which is dependent on rust. I don't think fastapi-slim uses it..
# but such is as it is.
# Clean up the package cache. These are the files that were downloaded during apt-get and are no longer needed.
RUN apt-get update && \
    apt-get install -y curl && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin:$PATH" && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN . "$HOME/.cargo/env" && pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src/ /usr/app/src
COPY mistbuddy_lite.py .


# Set environment variables for the application
ENV PYTHONPATH=.


# Expose port 8085
EXPOSE 8085

# Define the default command to run the application
CMD ["python", "/usr/app/src/mistbuddy_lite_code.py"]
