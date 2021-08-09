import time, threading, signal, sys, pytz, asyncio
from pytz import timezone
from datetime import datetime, timezone

import discord
import schedule

# Dev tokens
# DISCORD_TOKEN = 'ODczMzEwOTY2MDgxODEwNTAz.YQ2kNw.XG3asgLg3Gh9JKQtpHxqHlest2U'
# GENERAL_CHAT = 820733319540768780
# TDK Tokens
DISCORD_TOKEN = 'ODc0NDE4MTQ5MDYyMjI1OTky.YRGrXA.3AsS7YIx1C5pmbRdnDeCec2bKM0'
GENERAL_CHAT = 820733319540768780
KINGS_COUNCIL = 820733319540768780

client = discord.Client()

# Command list
BOSS_SCHEDULE = '!boss_schedule'
##############################################################################

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!help'):
        await help(message)
    if message.content.startswith(BOSS_SCHEDULE):
        await message.channel.send(boss_schedule())

async def help(message):
    print(BOSS_SCHEDULE)
    await message.channel.send('Prints the current member list that is allowed to kill bosses')

def boss_schedule(everyone=False):
    time = datetime.now(tz=timezone.utc)
    day = time.weekday()

    message = 'Today\'s boss schedule is '
    if everyone: 
        message = '@everyone ' + message
    
    elif day == 1 or 3 or 5:
        return message + 'Elites & Knights'
    elif day == 0 or 2 or 4:
        return message + 'Kings, Lords and Doug'
    elif day == 6:
        return message + 'George V day'
    
def boss_schedule_notifier():
    channel = client.get_channel(GENERAL_CHAT)
    asyncio.run_coroutine_threadsafe(channel.send(boss_schedule(True)), client.loop)

def switch_hamlyn_tristan_notifier():
    channel = client.get_channel(KINGS_COUNCIL)
    asyncio.run_coroutine_threadsafe(channel.send('@JyuVGrace#2224 please switch Hamlyn and Tristan'), client.loop)

def notifier_thread():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset = offset / 60 / 60 * -1

    reset_time = offset
    # If offset is negative add the negative offset to 24 to get the hour of the reset
    if offset < 0:
        reset_time = 24 + offset

    hour = int(reset_time)
    hour_str = '{:02d}:00'.format(hour)

    print(hour_str)
    schedule.every().day.at(hour_str).do(boss_schedule_notifier)
    schedule.every().sunday.do(switch_hamlyn_tristan_notifier)

    while True:
        time.sleep(1)
        schedule.run_pending()

def main():
    notifier = threading.Thread(target=notifier_thread)
    notifier.daemon = True
    notifier.start()

    client.run(DISCORD_TOKEN)
   
if __name__ == "__main__":
  main()
