
# MistBuddy Lite

## Introduction

MistBuddy Lite is a software package running on [GrowBase](https://github.com/solarslurpi/GrowBase)  that controls a [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device). It sends power on/off commands for a user-specified duration, repeating the misting cycle every minute.



## How it Works

The software manages a MistBuddy device's fan and mister by sending power on/off messages to it's smart plugs. Review the [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device) for more details.


### Getting Started
1. Build a [MistBuddy device](https://github.com/solarslurpi/mistbuddy_lite).
2. Build a [GrowBase](https://github.com/solarslurpi/GrowBase).  This is a Raspberry Pi server that will run the MistBuddy Lite software.
3. Pull the MistBuddy Lite Docker image.

1. **Install Requirements**
   - Make sure Python is installed on your system.

2. **Setup Configuration**
   - Create and configure `growbuddies_settings.json` with your device settings:
     ```json
     {
       "global_settings": {
         "address": "192.168.1.100"
       },
       "mqtt_power_messages": {
         "MyMistBuddy": ["cmnd/device1/POWER", "cmnd/device2/POWER"]
       }
     }
     ```

3. **Run the Application**
   ```sh
   uvicorn mistbuddy_lite:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Start Misting**
   - Use the following API endpoint to start misting:
     ```sh
     curl -X POST "http://localhost:8080/api/v1/mistbuddy-lite/start" -H "Content-Type: application/json" -d '{"duration_on": 30, "name": "MyMistBuddy"}'
     ```

5. **Stop Misting**
   - Use the following API endpoint to stop misting:
     ```sh
     curl -X GET "http://localhost:8080/api/v1/mistbuddy-lite/stop"
     ```

### Maintenance
- Check the `growbuddies_settings.json` file for correct configurations.
- Monitor logs for any errors.

## Detailed Guide

### Introduction
- Overview of MistBuddy Lite and its purpose.

### Installation
- Detailed prerequisites and step-by-step installation instructions.

### Configuration
- Environment variables
- Detailed guide on setting up `growbuddies_settings.json`

### Core Modules
- used wsl for dev environment.  Windows pathnames and file i/o makes it difficult to build projects that are ultimately destined for a Linux envrironment like the Raspbery Pi OS.
#### MistBuddyLite_state
- Description of attributes and validation:
  - `ServicesAddress`
  - `PowerMessages`
  - `MistBuddyLite_state`
- Loading settings from `growbuddies_settings.json`

#### MistBuddyLiteController
- Description and methods:
  - `start`
  - `stop`
- Singleton pattern for controller instance

### API Endpoints

#### Start MistBuddy
- Endpoint: `/api/v1/mistbuddy-lite/start`
- Method: POST
- Request body format
- Example request and response

#### Stop MistBuddy
- Endpoint: `/api/v1/mistbuddy-lite/stop`
- Method: GET
- Example request and response

### Logging
- Logging setup and configuration
- LoggerBase setup

### Error Handling
- Common errors and solutions
- Debugging tips

### Running the Application
- Using Uvicorn to run the FastAPI app
- Example command to start the server

### Contributing
- Contribution guidelines
- Code of conduct

### License
- License information

### Contact & Support
- Support contact information


get started with docker: https://blog.alexellis.io/getting-started-with-docker-on-raspberry-pi/

base rasp image w/ python: https://hub.docker.com/r/dtcooper/raspberrypi-os  e.g.: dtcooper/raspberrypi-os:python

1.

(from get started with docker i did this sicne i didn't knwo aobut it.)
If you are using the Pi for a headless application then you can reduce the memory split between the GPU and the rest of the system down to 16mb.

Edit /boot/config.txt and add this line:

gpu_mem=16

2. move this project to gus.
= check into github.
- clone MistBuddy
- clone GrowBuddies_shared within the MistBuddy directory at the same level as src