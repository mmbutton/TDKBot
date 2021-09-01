import time, threading, signal, sys, pytz, asyncio, os, argparse, sched, csv, difflib
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
POWER_TIER_LIST = '!power_tier_list'
MILITARY_TIER_LIST = '!military_tier_list'
FORTUNE_TIER_LIST = '!fortune_tier_list'
PROVISIONS_TIER_LIST = '!provisions_tier_list'
INSPIRATION_TIER_LIST = '!inspiration_tier_list'

##############################################################################
# Global 1 line functions

# Converts numbers to their orindal (1st, second etc)
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

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

HERO_NAME = 'Hero Name'
MAX_POWER = 'Max Power'
MILITARY_GROWTH = 'Military Growth'
FORTUNE_GROWTH = 'Fortune Growth'
PROVISIONS_GROWTH = 'Provisions Growth'
INSPIRATION_GROWTH = 'Inspiration Growth'
MAIDEN_GROWTH = 'Maiden Bond %'
DIFFICULTY = 'Difficulty'

hero_attributes_dict = []
# CSV Import
with open(Path(__file__).parent / '../resources/hero_attr_stats.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        hero_attributes_dict.append(row)

def get_sorted_growths(type, difficulty=6):
    growths = []
    for dic in hero_attributes_dict:
        if float(dic[DIFFICULTY]) >= difficulty:
            continue
        growth = {}
        growth[HERO_NAME] = dic[HERO_NAME]

        if dic[type] == '':
            dic[type] = 0
        if dic[MAIDEN_GROWTH] == '':
            dic[MAIDEN_GROWTH] = 0

        growth['Growth'] = float(dic[type]) + float(dic[MAIDEN_GROWTH])
        growths.append(growth)
    return sorted(growths, key=lambda k: k['Growth'], reverse=True)
    
def hero_growth_rank(hero_name, type):
    growths = get_sorted_growths(type)
    for i, dic in enumerate(growths):
        if dic[HERO_NAME].lower() == hero_name.lower():
            return i + 1, dic['Growth']

def hero_rank(hero_name, type):
    sorted_heroes = sorted(hero_attributes_dict, key=lambda k: int(k[type]), reverse=True)
    for i, dic in enumerate(sorted_heroes):
        if dic[HERO_NAME].lower() == hero_name.lower():
            return i + 1

def hero_row(hero_name):
    for dic in hero_attributes_dict:
        if dic[HERO_NAME].lower() == hero_name:
            return dic
    return None

def hero_name_diff(command_hero_name):
    heroes = []
    for dic in hero_attributes_dict:
        hero_name = dic[HERO_NAME].lower()
        heroes.append(hero_name)
    return difflib.get_close_matches(command_hero_name.lower(), heroes, cutoff=0.75)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def parse_tier_list_args(prog, command):
    parser = argparse.ArgumentParser(prog=POWER_TIER_LIST, add_help=False)
    parser.add_argument('--new', '-n', action='store_true')
    parser.add_argument('--low_vip', '-l', action='store_true')
    args = parser.parse_args(command.split()[1:])

    if args.new and args.low_vip:
        await message.channel.send("Can only specify one of new or low econ")
        return -1

    difficulty = 101
    if args.new:
        difficulty = 3
    if args.low_vip:
        difficulty = 4
    return difficulty

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
        parser = argparse.ArgumentParser(prog=HERO, add_help=False)
        parser.add_argument('--detailed', '-d', action='store_true')
        parser.add_argument('hero')
        args = parser.parse_args(command.split()[1:])

        entry = hero_row(args.hero.lower())
        if entry is not None:
            if args.detailed:
                print(entry)
            else:
                ranks = [ordinal(hero_growth_rank(args.hero.lower(), MILITARY_GROWTH)[0]), ordinal(hero_growth_rank(args.hero.lower(), FORTUNE_GROWTH)[0]), ordinal(hero_growth_rank(args.hero.lower(), PROVISIONS_GROWTH)[0]), ordinal(hero_growth_rank(args.hero.lower(), INSPIRATION_GROWTH)[0])]
                power_rank = ordinal(hero_rank(args.hero.lower(), MAX_POWER))
                await message.channel.send("**{0}**\n Max Power Rating: {1} | Military KP Rank: {2} | Fortune KP Rank: {3} | Provisions KP Rank: {4} | Inspiration KP Rank: {5} | Difficulty {6}".format(entry[HERO_NAME], power_rank, ranks[0], ranks[1], ranks[2], ranks[3], entry[DIFFICULTY]))
        else:
            diffs = hero_name_diff(args.hero.lower())
            await message.channel.send("Hero " + args.hero + " not found. Close hero names: " + str(diffs))
    if command.startswith(POWER_TIER_LIST):
        difficulty = await parse_tier_list_args(POWER_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = sorted(hero_attributes_dict, key=lambda k: int(k[MAX_POWER]), reverse=True)
        tier_list = list(filter(lambda k: float(k[DIFFICULTY]) < difficulty, tier_list))
        tier_list_str = "**Power Tier List**\n"

        rank = 1
        for hero in tier_list[:20]:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + hero[MAX_POWER] + ")\n"
            rank += 1

        await message.channel.send(tier_list_str)
    if command.startswith(MILITARY_TIER_LIST):
        difficulty = await parse_tier_list_args(MILITARY_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(MILITARY_GROWTH, difficulty, 20)
        tier_list_str = "**Military Tier List**\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'] * 100)) + "%)\n"
            rank += 1
        await message.channel.send(tier_list_str)
    if command.startswith(FORTUNE_TIER_LIST):
        difficulty = await parse_tier_list_args(FORTUNE_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(FORTUNE_GROWTH, difficulty, 20)
        tier_list_str = "**Fortune Tier List**\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'] * 100)) + "%)\n"
            rank += 1
            
        await message.channel.send(tier_list_str)
    if command.startswith(PROVISIONS_TIER_LIST):
        difficulty = await parse_tier_list_args(PROVISIONS_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(PROVISIONS_GROWTH, difficulty, 20)
        tier_list_str = "**Provisions Tier List**\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'] * 100)) + "%)\n"
            rank += 1

        await message.channel.send(tier_list_str)
    if command.startswith(INSPIRATION_TIER_LIST):
        difficulty = await parse_tier_list_args(INSPIRATION_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(INSPIRATION_GROWTH, difficulty, 20)
        tier_list_str = "**Inspiration Tier List**\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'] * 100)) + "%)\n"
            rank += 1

        await message.channel.send(tier_list_str)


def create_growth_tier_list(type, difficulty, cutoff):
    growths = get_sorted_growths(type, difficulty)
    return list(growths)[:cutoff]

async def help(message):
    await message.channel.send(BOSS_SCHEDULE + ': Prints the current member list that is allowed to kill bosses')
    await message.channel.send(EVENT_SCHEDULE + ': Posts an image of the event schedule for challenges and cross server events')
    await message.channel.send(HERO + ': Shows the rating of the hero compared to others. Use -d to see fully detailed stats')
    await message.channel.send('---------------------------------------------------------------------------')
    await message.channel.send('All tier lists can use the "--low_vip" or "new" flags to create a tier list geared towards lower spenders or new players')
    await message.channel.send(POWER_TIER_LIST + ': Tier list for the strongest hero\'s rated by maximum power')
    await message.channel.send(MILITARY_TIER_LIST + ': Tier list for military growth')
    await message.channel.send(FORTUNE_TIER_LIST + ': Tier list for fortune growth')
    await message.channel.send(PROVISIONS_TIER_LIST + ': Tier list for provisions growth')
    await message.channel.send(INSPIRATION_TIER_LIST + ': Tier list for inspiration growth')
    
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
