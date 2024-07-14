
# Running MistBuddyLite when the lights are on
MistBuddyLite does not detect whether the lights in its environment are on or off.  The software is designed for simplicity.  However, having MistBuddyLite run when lights are out can be problematic. Managing when MistBuddy spews mist can be handled many different ways.  Perhaps the simplest way since MistBuddyLite is running on a Raspberry Pi is to set up a CRON task.

# Setting up a CRON task
From [opensource.com](https://opensource.com/article/21/7/cron-linux): The cron system is a method to automatically run commands on a schedule. A scheduled job is called a cronjob, and it’s created in a file called a crontab. It’s the easiest and oldest way for a computer user to automate their computer.

## Verify Correct Date and Time Settings
The cron daemon uses the system time to run the scheduled jobs.  Make sure the time is set correctly on the Raspberry Pi.
- check the current time:
``` bash
date
```
If it is not correct, check to see if the time is set by the network:
``` bash
timedatectl

    Local time: Sun 2024-07-14 07:00:00 PDT
    Universal time: Sun 2024-07-14 14:00:00 UTC
    RTC time: n/a
    Time zone: America/Los_Angeles (PDT, -0700)
    System clock synchronized: yes
    NTP service: active
    RTC in local TZ: no
```
In the above example, the time is set by the network.  The system clock is synchronized and the NTP service is active.  If this is not the case, set the time manually:
``` bash
sudo date --set="2024-07-14 07:00:00"
```

## Edit the cron jobs
The `crontab` command is used to edit cron jobs.
```
crontab -e
```
This command opens the crontab file in the default text editor. Add a cron entry for:
- starting mistbuddy_lite every day a bit after the lights turn on.
- stopping mistbuddy_lite every day a bit before the lights turn off.
>Note:


See the [Cron Entry Syntax](#cron-entry-syntax) for more information.

Save and exit the crontab file. The cron daemon will automatically start running these jobs.
## Check Scheduled Jobs
To see the scheduled jobs, use the `crontab` command with the `-l` option:
``` bash
crontab -l
```
## Check the cron daemon
To check if the cron daemon is running, use the `systemctl` command:
``` bash
systemctl status cron
```

### Cron Entry Syntax
To schedule a cronjob, you provide a cron expression followed by the command you want your computer to execute.

#### Cron Expression
The cron expression schedules when the command gets run:

minute (0 to 59)
hour (0 to 23, with 0 being midnight)
day of month (1 to 31)
month (1 to 12)
day of week (0 to 6, with Sunday being 0)

An asterisk (*) in a field translates to "every." For example, this expression runs a backup script at the 0th minute of every hour on every day of every month:

#### Command Examples
Start mistbuddy_lite at 5:15 AM every day:
```bash
15 5 * * * /home/pi/mistbuddy_lite/shell_scripts/start_mistbuddy_lite.sh
```
Stop mistbuddy_lite at 4:45 PM every day:
```bash
45 16 * * * /home/pi/mistbuddy_lite/shell_scripts/stop_mistbuddy_lite.sh
```

### View the Log
```bash
journalctl -f -u cron.service
```

## Shell scripts
- [start_mistbuddy_lite.sh](https://github.com/solarslurpi/mistbuddy_lite/blob/main/shell_scripts/start_mistbuddy_lite.sh).
- [stop_mistbuddy_lite.sh](https://github.com/solarslurpi/mistbuddy_lite/blob/main/shell_scripts/stop_mistbuddy_lites.sh).
Are the curl commands to start and stop the mistbuddy_lite container.
