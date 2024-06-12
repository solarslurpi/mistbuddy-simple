


Use the same telegraf.conf that i've been using to access mqtt.
# TODO: determine the global location for telegraf.conf - clearly this is gus...so....?
# always get the latest.
- use the same growbuddies config file.

-> mistbuddy_lite needs no readings.
-> the actuators are sent on and off messages via mqtt. The duration on = duration_on. This is the number of seconds to have the actuator on in a minute. The client can adjust.
mistbuddy_lite:
/api/v1/mistbuddy_lite/start
/api/v1/mistbuddy_lite/stop
/api/v1/mistbuddy_lite/duration_on, input = int.  Saved across boots, etc.

Use: - set the duration first if you want start. the mistbuddy will be on for duration_on seconds.
send duation_on endpoint.

start: Load settings.
async task fire and forget:
- set up listening for readings and get readings.

First program: use telegraf for mqtt, send on/off to mister.  adjust number of seconds per minute to be on via mqtt.

Features:
- constantly turning mister on and off for on seconds per minute.
- settings default to 10 but can be set.
- does not turn on at night.
- can be turned off or on via mqtt (via telegraf)
- uses telegraf to send mqtt messages.
- uses growbuddies config file from GrowBuddies.
- runs as a systemd service.git

Todo:
1. consistent/clean/tested coder for getting snifferbuddy readings from telegraf.  This code should probably be in shared.