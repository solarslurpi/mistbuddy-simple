# MistBuddy Lite

## Introduction

MistBuddy Lite is a software package running on [GrowBase](https://github.com/solarslurpi/GrowBase) that controls a [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device). It sends power on/off commands for a user-specified duration, repeating the misting cycle every minute.

## How it Works

The software manages a MistBuddy device's fan and mister by sending power on/off messages to it's smart plugs. Review the [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device) for more details.


## Build Prerequisites
The humidifier and base station need to be running. These are separate projects.
1. Build a [MistBuddy device](https://github.com/solarslurpi/mistbuddy_lite).
2. Build a [GrowBase](https://github.com/solarslurpi/GrowBase).  This is a Raspberry Pi server that will run the MistBuddy Lite software.


## Create config.yaml
A `yaml` file is used to store configuration settings for the MistBuddy Lite application. It contains:
- The IP address of the GrowBase server.
- Tent settings for each grow tent, specifying:
  - MQTT power topics for the MistBuddy device
  - MQTT power topics for the CO2Buddy device (if applicable)
unique to the grow tent environment.

### Create the yaml file
The easiest way to create the config `yaml` file is to download the [`config.yaml` file](https://github.com/solarslurpi/mistbuddy_lite/blob/main/config.yaml) and edit it, or modify the following and copy/paste into a `config.yaml` file.

```yaml
growbase_settings:
  host_ip: 192.168.68.67

tents_settings:
  tent_one:
    MistBuddy:
      mqtt_power_topics:
        - cmnd/mistbuddy_fan/POWER
        - cmnd/mistbuddy_mister/POWER
    CO2Buddy:
      mqtt_power_topics:
        - cmnd/stomabuddy/POWER
```
## Download the Docker file


A `config.yaml` file is used to
To configure MistBuddy Lite, you need to:
Download the config.yaml file from the MistBuddy Lite repository.
Modify the config.yaml file to match your device settings. This includes setting up the growbase_settings with the hostname and IP address of your GrowBase, and defining the tents_settings with MQTT topics for each tent's MistBuddy and CO2Buddy devices.
Pull the MistBuddy Lite Docker image.
Run MistBuddy Lite using the modified config.yaml file (though the exact command for this is not provided in the given README snippet).
The configuration process ensures that MistBuddy Lite can communicate with your specific GrowBase setup and control the appropriate devices in your grow tents.
3. Pull the MistBuddy Lite Docker image.
4. Download the config.yaml file from the MistBuddy Lite repository. Modify the file to match your device settings.
5. Run MistBuddy Lite with the command....



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

## Configuration

The `config.yaml` file contains the following settings:

- `growbase_settings`: Contains the hostname and IP address of the GrowBase
- `tents_settings`: Defines the MQTT topics for each tent's MistBuddy and CO2Buddy devices

## Automated Operation

To automate the operation of MistBuddy Lite based on your grow light schedule, you can use cron jobs. See the [README_CRON.md](README_CRON.md) file for detailed instructions on setting up cron jobs.

## Development

### Prerequisites

- Python 3.7+
- pip

### Setup

1. Create a virtual environment:
   ```python
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
2. Install dependencies:
   ```python
   pip install -r requirements.txt
   ```

### Running Tests

To run the test suite:

```
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
