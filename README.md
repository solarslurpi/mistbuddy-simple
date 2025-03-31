# MistBuddy Lite

## Introduction

MistBuddy Lite is a software package running on [GrowBase](https://github.com/solarslurpi/GrowBase) that controls a [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device). It sends power on/off commands for a user-specified duration, repeating the misting cycle every minute.

## How it Works

The software manages a MistBuddy device's fan and mister by sending power on/off messages to it's smart plugs. Review the [MistBuddy device](https://github.com/solarslurpi/mistbuddy_device) for more details.
```
Regular Context              MQTT Thread              Async Playground
     │                           │                          │
     ├── SimpleMistBuddy()      │                          │
     ├── Setup callbacks ────────│                          │
     ├── client.connect()        │                          │
     │                           │                          │
     └── asyncio.run() ──────────┼─────────────────────────┤
                                │                          ├── run() starts
                                │                          ├── get_running_loop()
                                │                          │
                                │◄─────client.loop_start()─┤
                                │                          │
                                ├── Thread running         ├── while True: sleep
                                ├── Message arrives!        │
                                ├── _on_message runs       │
                                ├── run_coroutine_threadsafe ─►start_misting()
                                │                          ├── misting_cycle runs
                                │                          │
                                │                          │
     └── KeyboardInterrupt ─────┼──────────────────────────┤
                                │                          ├── cleanup
                                │◄─────client.loop_stop()──┤
                                X                          │
                                                          X
```



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

Okay, let's review `src/app.py` against the asynchronous flow described in the diagram.

```
Regular Context              MQTT Thread              Async Playground
     │                           │                          │
     ├── SimpleMistBuddy()      │                          │
     ├── Setup callbacks ────────│                          │
     ├── client.connect()        │                          │
     │                           │                          │
     └── asyncio.run() ──────────┼─────────────────────────┤
                                │                          ├── run() starts
                                │                          ├── get_running_loop()
                                │                          │
                                │◄─────client.loop_start()─┤
                                │                          │
                                ├── Thread running         ├── while True: sleep
                                ├── Message arrives!        │
                                ├── _on_message runs       │
                                ├── run_coroutine_threadsafe ─►start_misting()
                                │                          ├── misting_cycle runs
                                │                          │
                                │                          │
     └── KeyboardInterrupt ─────┼──────────────────────────┤
                                │                          ├── cleanup
                                │◄─────client.loop_stop()──┤
                                X                          │
                                                          X
```

**Overall Assessment:**

The code in `src/app.py` accurately implements the flow depicted in the diagram. It correctly separates the initial setup (Regular Context), the main asynchronous execution environment (Async Playground), and the MQTT client's separate thread, using the appropriate mechanisms to bridge between them.

**Detailed Breakdown:**

1.  **Initialization (Regular Context):**
    *   `main()` function (Lines 121-130): This is the entry point, running in the standard Python context.
    *   `buddy = SimpleMistBuddy()` (Line 124): Instantiates the class.
    *   `SimpleMistBuddy.__init__` (Lines 11-29): Executes entirely in the regular context.
        *   Loads `config.yaml` using `pathlib` (✅ Correct path handling).
        *   Initializes attributes like `broker`, `control_topic`, sets `self.loop = None` (✅ Correct, loop acquired later).
        *   Calls `_setup_mqtt_client()`.
    *   `_setup_mqtt_client()` (Lines 31-36): Also runs in the regular context.
        *   Creates the `paho.mqtt.Client` instance (✅).
        *   Assigns `_on_connect` and `_on_message` callbacks (✅ Setup Callbacks).
        *   Calls `self.client.connect()` (✅ client.connect()).

2.  **Entering the Async Playground:**
    *   `asyncio.run(buddy.run())` (Line 125): This is the key transition. It creates the event loop (the Async Playground) and starts executing the `buddy.run()` coroutine within it (✅ `asyncio.run()` transition).

3.  **Running the Async Playground & Starting MQTT Thread:**
    *   `SimpleMistBuddy.run()` (Lines 103-119): This coroutine is now running *inside* the Async Playground.
        *   `self.loop = asyncio.get_running_loop()` (Line 105): Correctly captures the event loop created by `asyncio.run()` (✅ `get_running_loop()`).
        *   `self.client.loop_start()` (Line 106): Starts the MQTT client's network loop in a *separate background thread* (✅ `client.loop_start()`). This creates the "MQTT Thread" context in the diagram.
        *   `while True: await asyncio.sleep(1)` (Lines 110-112): Keeps the main event loop running and responsive to scheduled tasks (✅ `while True: sleep`).

4.  **MQTT Thread Operation & Message Handling:**
    *   `_on_connect()` (Lines 38-44): Called by the MQTT library *in the MQTT thread* when connection is established. Subscribes to the topic (✅).
    *   `_on_message()` (Lines 46-63): Called by the MQTT library *in the MQTT thread* when a message arrives (✅ `_on_message runs`).
        *   Checks `msg.topic` (✅).
        *   Decodes payload (✅).
        *   **Crucially**, uses `asyncio.run_coroutine_threadsafe(self.start_misting(seconds), self.loop)` (Lines 54-57): This is the bridge. It safely schedules the `start_misting` coroutine to be executed back in the main Async Playground's event loop (`self.loop`) (✅ `run_coroutine_threadsafe -> start_misting()`).
        *   Calls `self.stop_misting()` directly if `seconds <= 0` (✅ Synchronous call is safe here).

5.  **Async Task Execution (Async Playground):**
    *   `start_misting()` (Lines 80-85): This `async def` method runs *in the Async Playground* when scheduled by `run_coroutine_threadsafe`.
        *   Calls `self.stop_misting()` to cancel any previous cycle (✅).
        *   Uses `asyncio.create_task(self.misting_cycle(duration))` (Line 84): Creates a new task for the misting cycle *within the same event loop* (✅ Correct way to start background async work).
    *   `misting_cycle()` (Lines 87-101): This `async def` method runs *in the Async Playground* as a task.
        *   `while True:` loop with `power_on()` and `await asyncio.sleep()` (✅ `misting_cycle runs`). The `await` allows the event loop to handle other things.
        *   Handles `CancelledError` for clean shutdown (✅).

6.  **Shutdown:**
    *   `KeyboardInterrupt` (Line 126): Catches Ctrl+C in the main thread. `asyncio.run()` ensures the `run()` coroutine is cancelled.
    *   `finally` block in `run()` (Lines 115-119): Executes during shutdown.
        *   `self.stop_misting()` (Line 116): Cancels the `misting_cycle` task if running (✅ Cleanup).
        *   `self.client.loop_stop()` (Line 117): Signals the MQTT thread to stop (✅ `client.loop_stop()`).
        *   `self.client.disconnect()` (Line 118): Disconnects the client (✅ Cleanup).

**Conclusion:**

The code in `src/app.py` is a solid implementation of the asynchronous pattern described. It correctly handles the different execution contexts and uses the appropriate `asyncio` tools for communication and task management.

----
** TO DO: ADD TO THE INSTALLATION SCRIPT **


Setting light on and off in Tasmota.  MistBuddy (and other devices) need to know if the light is on or off.  There is an analog reading that comes over on a snifferbuddy.  But we can simplify what mistbuddy needs to do to find out.

By setting up Tasmota rules on the command line, mistbuddy can send a cmnd message and receive an answer whether the light is on or off. The rules are:
```
Rule1 0
Rule1 ON Tele-ANALOG#A0<%Var1% DO mem1 0 ENDON
Rule1 1

Rule2 0
Rule2 ON Tele-ANALOG#A0<%Var1% DO mem1 1 ENDON
Rule2 1
```
Then to check the value of mem1, publish the topic `cmnd/snifferbuddy/tent_one/sunshine/Mem1`, which will return a string value of either 0 or 1.




