


Use the same telegraf.conf that i've been using to access mqtt.
# TODO: determine the global location for telegraf.conf - clearly this is gus...so....?
# always get the latest.
- use the same growbuddies config file.


First program: use telegraf for mqtt, send on/off to mister.  adjust number of seconds per minute to be on via mqtt.

Features:
- constantly turning mister on and off for on seconds per minute.
- settings default to 10 but can be set.
- does not turn on at night.
- can be turned off or on via mqtt.
- uses telegraf to send mqtt messages.
- uses growbuddies config file from GrowBuddies.
- runs as a systemd service.git