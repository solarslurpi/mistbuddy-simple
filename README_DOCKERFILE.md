# LEARN: Docker on Raspberry Pi
This document assumes a [GrowBase](https://github.com/solarslurpi/GrowBase) has been set up and is accessible via SSH. The account used to access the Raspberry Pi is the pi account.
## Install the Docker client and server on Raspberry Pi
Thanks to Alex Ellis for the [Getting Started with Docker on Raspberry Pi](https://blog.alexellis.io/getting-started-with-docker-on-raspberry-pi/) blog post.  The following steps are based on that post.

### Install Docker
```bash
curl -sSL https://get.docker.com | sh
```

### Get Docker Permissions
Docker is typically managed by the root user or users in the docker group.
1. Login via `SSH` to GrowBase.
2. Add the user you logged in with to the docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
sudo systemctl restart docker
```
The commands add the currently logged in user to the docker group. `newgrp` applies the changes. Then restart docker.

### Create the Docker file
Thank you to [dtcooper](https://hub.docker.com/r/dtcooper/raspberrypi-os) for the base rasp image w/ python.  The image used in this project is `dtcooper/raspberrypi-os:python`.  As I was researching how to get Docker running on the Raspberry Pi, I realized after hours of frustration how exceptionally thankful I am to dtcooper's work.  I was easily able to get the Docker container running on the Raspberry Pi.    Thank you!
- [dockerfile](https://github.com/solarslurpi/mistBuddy/blob/main/dockerfile)

### Build The Image
- Start an ssh connection with the Rasp Pi.
- Clone the mistbuddy_lite repo.
```bash
git clone https://github.com/solarslurpi/mistbuddy_lite.git
```
- Start the Docker service.
- From the mistbuddy_lite directory, build the Docker image.
```bash
docker build -t solarslurpie/mistbuddy_lite:latest .
```
### Push the Image to Dockerhub

### Run The Image
- Name the container `mistbuddy_lite`.
- Start a container in detached mode (-d).
- Map the host port 8080 to the container port 8080.
- Always restart (see [Use a restart policy](https://docs.docker.com/config/containers/start-containers-automatically/#use-a-restart-policy))
- Use the latest image.
```bash
docker run -v $(pwd)/config.yaml:/usr/app/config.yaml --name mistbuddy_lite -d -p 8085:8085 --restart always solarslurpie/mistbuddy_lite:latest
```
*Note: The restart policy and other commands can be updated after the container is running.  See [docker update](https://docs.docker.com/engine/reference/commandline/update/)*
e.g.:
```bash
docker update --restart always mistbuddy_lite
```
And to start the container:
```bash
docker start mistbuddy_lite
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
