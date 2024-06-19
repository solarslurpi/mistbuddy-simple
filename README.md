
get started with docker: https://blog.alexellis.io/getting-started-with-docker-on-raspberry-pi/

base rasp image w/ python: https://hub.docker.com/r/dtcooper/raspberrypi-os  e.g.: dtcooper/raspberrypi-os:python

1.

(from get started with docker i did this sicne i didn't knwo aobut it.)
If you are using the Pi for a headless application then you can reduce the memory split between the GPU and the rest of the system down to 16mb.

Edit /boot/config.txt and add this line:

gpu_mem=16

2. move this project to gus.
= check into github.