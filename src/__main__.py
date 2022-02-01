import time, threading, signal, sys, pytz, asyncio, os, argparse, sched, csv, difflib
from pathlib import Path
from pytz import timezone
from datetime import datetime, timezone
import glob
import re

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
TOURNEY_FARM = '!tourney_farm'

##############################################################################
# Global 1 line functions

# Converts numbers to their orindal (1st, second etc)
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
get_growth = lambda n, m: int((float(n) + float(m) + float(n) * float(m) + 1.15) * 100 )
get_percent = lambda n: int(float(n) * 100)

# Global variables

SUNDAY = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6

HERO_NAME = 'Hero Name'
MAX_POWER = 'Max Power'
MAX_KP = 'Max KP'
MAX_MILITARY = 'Max Military'
MAX_FORTUNE = 'Max Fortune'
MAX_PROVISIONS = 'Max Provisions'
QUALITY_MILITARY = 'Military Quality'
QUALITY_FORTUNE = 'Fortune Quality'
QUALITY_PROVISIONS = 'Provisions Quality'
QUALITY_INSPIRATION = 'Inspiration Quality'
GROWTH_MILITARY = 'Military Growth'
GROWTH_FORTUNE = 'Fortune Growth'
GROWTH_PROVISIONS = 'Provisions Growth'
GROWTH_INSPIRATION = 'Inspiration Growth'
MAX_INSPIRATION = 'Max Inspiration'
MILITARY_GROWTH = 'Military Growth'
FORTUNE_GROWTH = 'Fortune Growth'
PROVISIONS_GROWTH = 'Provisions Growth'
INSPIRATION_GROWTH = 'Inspiration Growth'
MAIDEN_GROWTH = 'Maiden Bond %'
DIFFICULTY = 'Difficulty'

LOW_VIP_DIFFICULTY = 4
NEW_PLAYER_DIFFICULTY = 3
TOURNEY_FARM_STR = '''
```+-------------+-----------+--------+---+
| Name        | ID        | Heroes | KP   |
+-------------+-----------+--------+------+
| punchbag    | 545005113 | 75     | 12m  |
+-------------+-----------+--------+------+```
'''

hero_attributes_dict = []
# CSV Import
with open(Path(__file__).parent / '../resources/hero_attr_stats.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        hero_attributes_dict.append(row)

def get_sorted_growths(type, difficulty=101):
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

        growth['Growth'] = get_growth(dic[type], dic[MAIDEN_GROWTH])
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

class ArgumentParserError(Exception): pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

async def parse_tier_list_args(message, prog, command):
    try:
        parser = ThrowingArgumentParser(prog=POWER_TIER_LIST, add_help=False)
        parser.add_argument('--new', '-n', action='store_true')
        parser.add_argument('--low_vip', '-l', action='store_true')
        args = parser.parse_args(command.split()[1:])
    
        if args.new and args.low_vip:
            await message.channel.send("Can only specify one of new or low econ")
            return -1

        difficulty = 101
        if args.new:
            difficulty = NEW_PLAYER_DIFFICULTY
        if args.low_vip:
            difficulty = LOW_VIP_DIFFICULTY
        return difficulty

    except:
        await message.channel.send("Unknown arguments detected. Only \"-l\" flag for low_vip or \"-n\" for new players are accepted for arguments")
        return -1

def get_hero_inforgraphic(hero_name):
    path = Path(__file__).parent / '../resources/milo_infographics/*'
    for filename in glob.glob(str(path)):
        name = os.path.basename(filename).lower().replace('_', '')

        print(name + " : " + hero_name.lower().replace(' ', ''))

        if re.search(hero_name.lower().replace(' ', ''), name):
            return filename
    
    return None


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command = message.content.lower()
    
    ## BL Only commands
    if(message.guild is not None):
        if os.getenv('BL_SERVER_ID') == str(message.guild.id):
            if command.startswith(TOURNEY_FARM):
                await message.channel.send(TOURNEY_FARM_STR)
 
    ## All servers commands
    if command.startswith('!help'):
        await help(message)
    if command.startswith(EVENT_SCHEDULE):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/event_schedule.png'))
    if command.startswith(HERO):
        detailed = False
        command = command[(len(HERO) + 1):]
        if command.startswith("-i"):
            command = command[3:]
            filename = get_hero_inforgraphic(command)
            if filename is not None:
                await message.channel.send(file=discord.File(Path(__file__).parent / filename))
            else:
                diffs = hero_name_diff(command.lower())
                await message.channel.send("Hero " + command + " not found. Close hero names: " + str(diffs))
            return

        if command.startswith("-d"):
            detailed = True
            command = command[3:]
        hero = command.lower()
        entry = hero_row(hero)
        if entry is not None:
            if detailed:
                ranks = [ordinal(hero_rank(hero, MAX_POWER)), ordinal(hero_growth_rank(hero, MILITARY_GROWTH)[0]), ordinal(hero_growth_rank(hero, FORTUNE_GROWTH)[0]), ordinal(hero_growth_rank(hero, PROVISIONS_GROWTH)[0]), ordinal(hero_growth_rank(hero, INSPIRATION_GROWTH)[0])]

                response_str = "**{0}**\n".format(entry[HERO_NAME])
                response_str = response_str + "```Max Attributes (lvl 400)\nMax Power {0} | Max KP {1} | Max Military {2} | Max Fortune {3} | Max Provisions {4} | Max Inspiration {5})```"\
                    .format(entry[MAX_POWER], entry[MAX_KP], entry[MAX_MILITARY], entry[MAX_FORTUNE], entry[MAX_PROVISIONS], entry[MAX_INSPIRATION])
                response_str = response_str + "```Base Quality\n Military {0} | Fortune {1} | Provisions {2} | Inspiration {3}```"\
                    .format(entry[QUALITY_MILITARY], entry[QUALITY_FORTUNE], entry[QUALITY_PROVISIONS], entry[QUALITY_INSPIRATION])
                response_str = response_str + "```Quality Efficiency %\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                    .format(get_growth(entry[GROWTH_MILITARY], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_FORTUNE], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_PROVISIONS], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_INSPIRATION], entry[MAIDEN_GROWTH]))
                response_str = response_str + "```Paragon % (Tome efficiency)\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                    .format(get_percent(entry[GROWTH_MILITARY]), get_percent(entry[GROWTH_FORTUNE]), get_percent(entry[GROWTH_PROVISIONS]), get_percent(entry[GROWTH_INSPIRATION]))
                response_str = response_str + "```\nRank\n Power {0} | Military {1} | Fortune {2} | Provisions {3} | Inspiration {4}```"\
                    .format(ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])
                await message.channel.send(response_str)
            else:
                ranks = [ordinal(hero_rank(hero, MAX_POWER)), ordinal(hero_growth_rank(hero, MILITARY_GROWTH)[0]), ordinal(hero_growth_rank(hero, FORTUNE_GROWTH)[0]), ordinal(hero_growth_rank(hero, PROVISIONS_GROWTH)[0]), ordinal(hero_growth_rank(hero, INSPIRATION_GROWTH)[0])]
                power_rank = ordinal(hero_rank(hero, MAX_POWER))
                await message.channel.send("**{0}**\n Max Power Rating: {1} | Military Growth Rank: {2} | Fortune Growth Rank: {3} | Provisions Growth Rank: {4} | Inspiration Growth Rank: {5} | Difficulty {6}".format(entry[HERO_NAME], ranks[0], ranks[1], ranks[2], ranks[3], ranks[4], entry[DIFFICULTY]))
        else:
            diffs = hero_name_diff(hero)
            await message.channel.send("Hero " + command + " not found. Close hero names: " + str(diffs))
    if command.startswith(POWER_TIER_LIST):
        difficulty = await parse_tier_list_args(message, POWER_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = sorted(hero_attributes_dict, key=lambda k: int(k[MAX_POWER]), reverse=True)
        tier_list = list(filter(lambda k: float(k[DIFFICULTY]) < difficulty, tier_list))

        tier_list_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            tier_list_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            tier_list_type = " (New Player)"

        tier_list_str = "**Power Tier List**" + tier_list_type + "\n"

        rank = 1
        for hero in tier_list[:20]:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + hero[MAX_POWER] + ")\n"
            rank += 1

        await message.channel.send(tier_list_str)
    if command.startswith(MILITARY_TIER_LIST):
        difficulty = await parse_tier_list_args(message, MILITARY_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(MILITARY_GROWTH, difficulty, 20)

        tier_list_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            tier_list_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            tier_list_type = " (New Player)"

        tier_list_str = "**Military Tier List**" + tier_list_type + "\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%)\n"
            rank += 1
        await message.channel.send(tier_list_str)
    if command.startswith(FORTUNE_TIER_LIST):
        difficulty = await parse_tier_list_args(message, FORTUNE_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(FORTUNE_GROWTH, difficulty, 20)

        tier_list_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            tier_list_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            tier_list_type = " (New Player)"
        tier_list_str = "**Fortune Tier List**" + tier_list_type + "\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%)\n"
            rank += 1
            
        await message.channel.send(tier_list_str)
    if command.startswith(PROVISIONS_TIER_LIST):
        difficulty = await parse_tier_list_args(message, PROVISIONS_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(PROVISIONS_GROWTH, difficulty, 20)
        

        tier_list_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            tier_list_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            tier_list_type = " (New Player)"

        tier_list_str = "**Provisions Tier List**" + tier_list_type + "\n"
        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%)\n"
            rank += 1

        await message.channel.send(tier_list_str)
    if command.startswith(INSPIRATION_TIER_LIST):
        difficulty = await parse_tier_list_args(message, INSPIRATION_TIER_LIST, command)
        if difficulty <0:
            return
        tier_list = create_growth_tier_list(INSPIRATION_GROWTH, difficulty, 20)

        tier_list_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            tier_list_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            tier_list_type = " (New Player)"

        tier_list_str = "**Inspiration Tier List**" + tier_list_type + "\n"

        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%)\n"
            rank += 1

        await message.channel.send(tier_list_str)


def create_growth_tier_list(type, difficulty, cutoff):
    growths = get_sorted_growths(type, difficulty)
    return list(growths)[:cutoff]

async def help(message):
    # BL only commands
    if(message.guild is not None):
        if os.getenv('BL_SERVER_ID') == str(message.guild.id):
            await message.channel.send(TOURNEY_FARM + ': Creates a table of safely farmable individuals (inactive and low KP/hero ratio)')

    # All server commands
    await message.channel.send(EVENT_SCHEDULE + ': Posts an image of the event schedule for challenges and cross server events')
    await message.channel.send(HERO + ': Shows the rating of the hero compared to others. Use -d to see fully detailed stats, use -i to pull up an infographic.')
    await message.channel.send('---------------------------------------------------------------------------')
    await message.channel.send('All tier lists can use the low VIP "-l" or new player "-n" flags to create a tier list geared towards lower spenders or new players')
    await message.channel.send(POWER_TIER_LIST + ': Tier list for the strongest hero\'s rated by maximum power')
    await message.channel.send(MILITARY_TIER_LIST + ': Tier list for military growth')
    await message.channel.send(FORTUNE_TIER_LIST + ': Tier list for fortune growth')
    await message.channel.send(PROVISIONS_TIER_LIST + ': Tier list for provisions growth')
    await message.channel.send(INSPIRATION_TIER_LIST + ': Tier list for inspiration growth')

def jotun_notifier():
    channel = client.get_channel(int(os.getenv('GENERAL_CHAT')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('BL_ALERTS') + '> Jotun time'), client.loop)

    channel = client.get_channel(int(os.getenv('COLLECTIVE')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun time'), client.loop)

def jotun_minions_notifier():
    channel = client.get_channel(int(os.getenv('GENERAL_CHAT')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('BL_ALERTS') + '> Jotun\'s minions time'), client.loop)

    channel = client.get_channel(int(os.getenv('COLLECTIVE')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun\'s minions time'), client.loop)

def server_reset_notifier():
    channel = client.get_channel(int(os.getenv('COLLECTIVE')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Daily server rest will be in 15 minutes'), client.loop)

def cross_server_notifier():
    channel = client.get_channel(int(os.getenv('GENERAL_CHAT')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('BL_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

    channel = client.get_channel(int(os.getenv('COLLECTIVE')))
    asyncio.run_coroutine_threadsafe(channel.send('<@&' + os.getenv('COLLECTIVE_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

# This might be an awful way to do this but the scheduler daily run never updates after the first run.
def monday_notifier():
    cross_server_notifier()

def wednesday_notifier():
    cross_server_notifier()

def friday_notifier():
    cross_server_notifier()

def boss_notifier():
    channel = client.get_channel(int(os.getenv('BLOODLUST')))
    asyncio.run_coroutine_threadsafe(channel.send('@everyone Bosses will be opened shortly. Please limit your hits to 10B power (ie: 5k points).'), client.loop)

def notifier_thread():
    # Get the timezone offset and figure out the offset from localtime (In a 24 hour context)
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    offset = offset / 60 / 60 * -1
    reset_time = offset % 24

    reset_hour = int(reset_time)
    reset_hour_str = '{:02d}:00'.format(reset_hour)

    boss_open_hour = int(reset_time) + 1
    boss_open_hour_str = '{:02d}:00'.format(boss_open_hour)
    schedule.every().day.at(boss_open_hour_str).do(boss_notifier)

    fifteen_min_before_reset_hour_str = '{:02d}:45'.format(reset_hour - 1)
    schedule.every().day.at(fifteen_min_before_reset_hour_str).do(server_reset_notifier)

    jotun_hour = (reset_hour - 3) % 24
    jotun_hour_str = '{:02d}:00'.format(jotun_hour)
    schedule.every().day.at(jotun_hour_str).do(jotun_notifier)

    jotun_minions_hour = (reset_hour - 7) % 24
    jotun_minions_hour_str = '{:02d}:00'.format(jotun_minions_hour)
    schedule.every().day.at(jotun_minions_hour_str).do(jotun_minions_notifier)

    jotun_minions_hour = (reset_hour + 10) % 24
    jotun_minions_hour_str = '{:02d}:00'.format(jotun_minions_hour)
    schedule.every().day.at(jotun_minions_hour_str).do(jotun_minions_notifier)

    # This schedule only works for UTC - time zones. UTC plus timezones would break it and make it go off a day late
    schedule.every().monday.at(reset_hour_str).do(monday_notifier)
    schedule.every().wednesday.at(reset_hour_str).do(wednesday_notifier)
    schedule.every().friday.at(reset_hour_str).do(friday_notifier)

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
