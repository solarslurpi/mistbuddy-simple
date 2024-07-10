# LEARN: Docker on Raspberry Pi
This document assumes the (most likely headless) Raspberry Pi that will be running the Docker container has been setup.  The Raspberry Pi is accessible via SSH.  The account used to access the Raspberry Pi is the pi account.
## Install the Docker client and server on Raspberry Pi
Thanks to Alex Ellis for the [Getting Started with Docker on Raspberry Pi](https://blog.alexellis.io/getting-started-with-docker-on-raspberry-pi/) blog post.  The following steps are based on that post.

### Optional Rasp Pi OS customization
The Raspberry Pi is installed headless.  Alex notes: *If you are using the Pi for a headless application then you can reduce the memory split between the GPU and the rest of the system down to 16mb.*

Edit `/boot/config.txt` and add this line:
```bash
gpu_mem=16
```
### Install Docker
```bash
curl -sSL https://get.docker.com | sh
```
### Create the Docker file
Thank you to [dtcooper](https://hub.docker.com/r/dtcooper/raspberrypi-os) for the base rasp image w/ python.  The image used in this project is `dtcooper/raspberrypi-os:python`.  As I was researching how to get Docker running on the Raspberry Pi, I realized after hours of frustration how exceptionally thankful I am to dtcooper's work.  I was easily able to get the Docker container running on the Raspberry Pi.    Thank you!
- [dockerfile](https://github.com/solarslurpi/mistBuddy/blob/main/dockerfile)

### Build The Image
- Start an ssh connection with the Rasp Pi.
- Clone the mistbuddy repo.
```bash
git clone https://github.com/solarslurpi/mistbuddy_lite.git
```
- Clone the GrowBuddies_shared repo. In the mistbuddy_lite directory, clone the GrowBuddies_shared repo.
```bash
git clone https://github.com/solarslurpi/GrowBuddies_shared.git
```

- From the mistbuddy_lite directory, build the Docker image.
```bash
docker build -t solarslurpie/mistbuddy_lite:latest .
```
### Verify the image runs
- Start a container
```bash
docker run --name mistbuddy_lite -d -p 8080:8080 solarslurpie/mistbuddy_lite:latest
```
- Check if the container is running by listing all containers
```bash
docker ps -a
CONTAINER ID   IMAGE                                COMMAND                  CREATED              STATUS                          PORTS                                       NAMES
360e677b63e8   solarslurpie/mistbuddy_lite:latest   "python /usr/app/src…"   5 seconds ago   Exited (2) 4 seconds ago             mistbuddy_lite
57ec7dfca8ed   mistbuddy-lite:latest                "python /usr/app/src…"   12 days ago          Exited (255) 12 days ago        0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   mistbuddy-lite

```
In the example above, there are two containers.  Both are not running.  One is 12 days old.  Let's delete that one.
```bash
docker rm 57ec7dfca8ed
```
The docker image that we built says it exited 4 seconds ago.  Let's check the logs.
```bash
docker logs 360e677b63e8
```
The logfile says:
```python
python: can't open file '/usr/app/src/mistbuddy_lite.py': [Errno 2] No such file or directory
```
