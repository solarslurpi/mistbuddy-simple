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
git clone
```
