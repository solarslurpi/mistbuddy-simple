
# Running MistBuddyLite when the lights are on
MistBuddyLite does not detect whether the lights in its environment are on or off.  The software is designed for simplicity.  However, having MistBuddyLite run when lights are out can be problematic. Managing when MistBuddy spews mist can be handled many different ways.  Perhaps the simplest way since MistBuddyLite is running on a Raspberry Pi is to set up a CRON task.

# Setting up a CRON task
From [opensource.com](https://opensource.com/article/21/7/cron-linux): The cron system is a method to automatically run commands on a schedule. A scheduled job is called a cronjob, and it’s created in a file called a crontab. It’s the easiest and oldest way for a computer user to automate their computer.

## cron syntax
To schedule a cronjob, you provide a cron expression followed by the command you want your computer to execute. The cron expression schedules when the command gets run:

minute (0 to 59)
hour (0 to 23, with 0 being midnight)
day of month (1 to 31)
month (1 to 12)
day of week (0 to 6, with Sunday being 0)

An asterisk (*) in a field translates to "every." For example, this expression runs a backup script at the 0th minute of every hour on every day of every month:

Start mistbuddy_lite at 5:15 AM every day:
```bash
15 5 * * * /opt/start_mistbuddy_lite.sh
```
Stop mistbuddy_lite at 4:45 PM every day:
```bash
45 16 * * * /opt/stop_mistbuddy_lite.sh
```
## Shell scripts
- [start_mistbuddy_lite.sh]()
- [stop_mistbuddy_lite.sh]()
Are the curl commands to start and stop the mistbuddy_lite container.
