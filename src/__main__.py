import time, threading, signal, sys, pytz, asyncio, os, argparse, sched
from pathlib import Path
from pytz import timezone
from datetime import datetime, timezone

import discord
import schedule
from dotenv import load_dotenv

load_dotenv()

# Dev tokens
client = discord.Client()

# Command list
BOSS_SCHEDULE = '!boss_schedule'
EVENT_SCHEDULE = '!event_schedule'
HERO = '!hero'

##############################################################################

# Global variables
BOSS_SCHEDULE_LIST = [
    'Alliance Boss Schedule (All times in UTC)',
    '  Monday - King/Lords/Doug',
    '  Tuesday - Everyone Else',
    '  Wednesday - King/Lords/Doug',
    '  Thursday - Everyone Else',
    '  Friday - King/Lords/Doug',
    '  Saturday - Everyone Else',
    '  Sunday - G5',
]

SUNDAY = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command = message.content.lower()
    
    if command.startswith('!help'):
        await help(message)
    if command.startswith(BOSS_SCHEDULE):
        await message.channel.send(boss_schedule())
    if command.startswith(EVENT_SCHEDULE):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/event_schedule.png'))
    if command.startswith(HERO):
        parser = argparse.ArgumentParser(prog="!hero", add_help=False, exit_on_error=False)
        parser.add_argument('--detailed', '-d', action='store_true')
        parser.add_argument('hero')
        args = parser.parse_args(command.split()[1:])
        if args.help:
            await message.channel.send(parser.print_help())
        if args.hero == 'brunhilde':
            if args.detailed:
                print("DETAILED_STATS")
            else:
                await message.channel.send(args.hero + " \nKingdom Power: 30th | Military: 30th | Fortune: 30th | Provisions: 30th | Inspiration: 30th")


    

async def help(message):
    await message.channel.send(BOSS_SCHEDULE + ' :Prints the current member list that is allowed to kill bosses')
    await message.channel.send(EVENT_SCHEDULE + ' :Posts an image of the event schedule for challenges and cross server events')
    
def boss_schedule():
    boss_schedule = BOSS_SCHEDULE_LIST.copy()

    time = datetime.now(tz=timezone.utc)
    day = time.weekday()

    boss_schedule[day + 1] = '**' + boss_schedule[day + 1] + '**'

    return "\n".join(boss_schedule)

def boss_schedule_notifier(day):
    channel = client.get_channel(int(os.getenv('BOT_TESTING')))

    message = '@everyone Today\'s boss schedule is '
    if day == 1 or 3 or 5:
        message = message + 'Elites & Knights'
    elif day == 0 or 2 or 4:
        message = message + 'Kings, Lords and Doug'
    elif day == 6:
        message = message + 'George V day'

    return message;

def switch_hamlyn_tristan_notifier():
    channel = client.get_channel(int(os.getenv('KINGS_COUNCIL')))
    asyncio.run_coroutine_threadsafe(channel.send('@King Gobert please switch Hamlyn and Tristan'), client.loop)

def jotun_notifier():
    channel = client.get_channel(int(os.getenv('GENERAL_CHAT')))
    asyncio.run_coroutine_threadsafe(channel.send('Jotun time @everyone '), client.loop)

def cross_server_notifier():
    channel = client.get_channel(int(os.getenv('BOT_TESTING')))
    asyncio.run_coroutine_threadsafe(channel.send('@everyone New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

# This might be an awful way to do this but the scheduler daily run never updates after the first run.
def sunday_notifier():
    message = boss_schedule_notifier(SUNDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def monday_notifier():
    message = boss_schedule_notifier(MONDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def tuesday_notifier():
    cross_server_notifier()
    message = boss_schedule_notifier(TUESDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def wednesday_notifier():
    message = boss_schedule_notifier(WEDNESDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def thursday_notifier():
    cross_server_notifier()
    message = boss_schedule_notifier(THURSDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def friday_notifier():
    message = boss_schedule_notifier(FRIDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def saturday_notifier():
    cross_server_notifier()
    message = boss_schedule_notifier(SATURDAY)
    asyncio.run_coroutine_threadsafe(channel.send(message), client.loop)

def notifier_thread():
    # Get the timezone offset and figure out the offset from localtime (In a 24 hour context)
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset = offset / 60 / 60 * -1
    reset_time = offset % 24

    reset_hour = int(reset_time)
    reset_hour_str = '{:02d}:00'.format(reset_hour + 1)

    jotun_hour = (reset_hour - 4) % 24
    jotun_hour_str = '{:02d}:00'.format(jotun_hour)
    schedule.every().day.at(jotun_hour_str).do(jotun_notifier)

    # This schedule only works for UTC - time zones. UTC plus timezones would break it and make it go off a day late
    schedule.every().sunday.at(reset_hour_str).do(sunday_notifier)
    schedule.every().monday.at(reset_hour_str).do(monday_notifier)
    schedule.every().tuesday.at(reset_hour_str).do(tuesday_notifier)
    schedule.every().wednesday.at(reset_hour_str).do(wednesday_notifier)
    schedule.every().thursday.at(reset_hour_str).do(thursday_notifier)
    schedule.every().friday.at(reset_hour_str).do(friday_notifier)
    schedule.every().saturday.at(reset_hour_str).do(saturday_notifier)

    schedule.every().sunday.do(switch_hamlyn_tristan_notifier)

    while True:
        time.sleep(1)
        schedule.run_pending()

def main():
    notifier = threading.Thread(target=notifier_thread)
    notifier.daemon = True
    notifier.start()

    client.run(os.getenv('DISCORD_TOKEN'))
   
if __name__ == "__main__":
  main()
