import time, threading, signal, sys, pytz, asyncio, os, argparse, sched, csv, difflib
from pathlib import Path
from pytz import timezone
from datetime import datetime, timezone
import glob
import re
from math import log10, floor

#import redis
import discord
import schedule
from dotenv import load_dotenv

load_dotenv()
#mem = redis.Redis()

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
KP_TIER_LIST = '!kp_tier_list'
FORMULAS = '!formulas'
ZODIACS = '!zodiacs'
CASTLE_SKINS = '!castle_skins'

##############################################################################
# Global 1 line functions

# Converts numbers to their orindal (1st, second etc)
ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
get_growth = lambda n, m: int((float(n) + float(m) + float(n) * float(m) + 1.15) * 100 )
get_percent = lambda n: int(float(n) * 100)
round_3sigfig = lambda n: '{:,g}'.format(round(n, 3-int(floor(log10(abs(n))))-1))

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
| punchbag    | 545005113 | A lot  | 12m  |
+-------------+-----------+--------+------+```
'''

DM_BOT_MSG = "For longer commands consider DMing the bot to avoid flooding the chat."

hero_attributes_dict = []
# CSV Import
with open(Path(__file__).parent / '../resources/hero_attr_stats.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        hero_attributes_dict.append(row)

def format_big_number(num):
    suffixes = ["", "K", "M", "B", "T", "Q"]
    first_numbers = float("{:.2e}".format(int(num))[:4])

    num = "{:,}".format(int(num))
    if len(num.split(',')[0]) == 2:
        first_numbers = float(first_numbers) * 10
    elif len(num.split(',')[0]) == 3:
        first_numbers = float(first_numbers) * 100
    return round_3sigfig(first_numbers) + suffixes[num.count(',')]

def create_attributes_tier_list(type, difficulty, cutoff):
    heros = []
    for dic in hero_attributes_dict:
        if float(dic[DIFFICULTY]) >= difficulty:
            continue
        hero = {}
        hero[HERO_NAME] = dic[HERO_NAME]
        hero['Attributes'] = int(dic[type])
        heros.append(hero)
    return sorted(heros, key=lambda k: (k['Attributes']), reverse=True)[:cutoff]

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

        if type is MILITARY_GROWTH:
            growth['Attributes'] = int(dic[MAX_MILITARY])
        elif type is FORTUNE_GROWTH:
            growth['Attributes'] = int(dic[MAX_FORTUNE])
        elif type is PROVISIONS_GROWTH:
            growth['Attributes'] = int(dic[MAX_PROVISIONS])
        elif type is INSPIRATION_GROWTH:
            growth['Attributes'] = int(dic[MAX_INSPIRATION])
        
        growths.append(growth)
    return sorted(growths, key=lambda k: (k['Growth'], k['Attributes']), reverse=True)
    
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
    notifier = threading.Thread(target=notifier_thread)
    notifier.daemon = True
    notifier.start()

class ArgumentParserError(Exception): pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

async def parse_tier_list_args(message, prog, command):
    try:
        parser = ThrowingArgumentParser(prog=POWER_TIER_LIST, add_help=False)
        parser.add_argument('--new', '-n', action='store_true')
        parser.add_argument('--low_vip', '-l', action='store_true')
        parser.add_argument('--attributes', '-a', action='store_true')
        args = parser.parse_args(command.split()[1:])
    
        if args.new and args.low_vip:
            await message.channel.send("Can only specify one of new or low econ")
            return -1

        difficulty = 101
        if args.new:
            difficulty = NEW_PLAYER_DIFFICULTY
        if args.low_vip:
            difficulty = LOW_VIP_DIFFICULTY
        return difficulty, args.attributes

    except:
        await message.channel.send("Unknown arguments detected. Only \"-l\" flag for low_vip or \"-n\" for new players are accepted for arguments")
        return -1, false

def get_hero_inforgraphic(hero_name):
    matches = []
    path = Path(__file__).parent / '../resources/milo_infographics/*'
    for filename in glob.glob(str(path)):
        name = os.path.basename(filename).lower().replace('_', '')

        if re.search(hero_name.lower().replace(' ', ''), name):
            matches.append(filename)
    
    if len(matches) == 0:
        return None
    if len(matches) == 1:
        return matches[0]
    else:
        return min(matches, key=len)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command = message.content.lower()
    ## Debug
    ##if command.startswith('!server'):
        #await message.channel.send(mem.lrange("servers", 0, 0))
    ## BL Only commands
    if message.guild is not None:
        if os.getenv('BL_SERVER_ID') == str(message.guild.id):
            if command.startswith(TOURNEY_FARM):
                await message.channel.send(TOURNEY_FARM_STR)
    ## All servers commands
    if command.startswith('!help'):
        await help(message)
    '''if command.startswith('!add_channel_to_notifications'):
        command = command[(len('!add_channel_to_notifications') + 1):]
        mem.lpush("servers", message.guild.id)
        mem.set(str(message.guild.id), message.channel.id)
        if len(command) > 0:
           mem.set(str(message.guild.id), "<@&" + str(command + ">"))
        else:
            mem.set(str(message.guild.id), "@everyone") 
        mem.set(str(message.guild.id), message.channel.id)
        await message.channel.send("Added channel to notifications. Default is to ping everyone. Please add a roleId if you want to only ping a specific role.")
'''
    if command.startswith(FORMULAS):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/formulas.png'))
    if command.startswith(ZODIACS):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/zodiacs.png'))
    if command.startswith(CASTLE_SKINS):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/castle_skins.png'))
    if command.startswith(EVENT_SCHEDULE):
        await message.channel.send(file=discord.File(Path(__file__).parent / '../resources/event_schedule.png'))
    if command.startswith(HERO):
        detailed = False
        command = command[(len(HERO) + 1):].replace('‘', '\'').replace('’', '\'')
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
            ranks = [
                    ordinal(hero_rank(hero, MAX_KP)),
                    ordinal(hero_rank(hero, MAX_POWER)),
                    ordinal(hero_growth_rank(hero, MILITARY_GROWTH)[0]),
                    ordinal(hero_growth_rank(hero, FORTUNE_GROWTH)[0]),
                    ordinal(hero_growth_rank(hero, PROVISIONS_GROWTH)[0]),
                    ordinal(hero_growth_rank(hero, INSPIRATION_GROWTH)[0])
            ]
            if detailed:
                response_str = "**{0}**\n".format(entry[HERO_NAME])
                response_str = response_str + "```Max Attributes (lvl 400)\nMax Power {0} | Max KP {1} | Max Military {2} | Max Fortune {3} | Max Provisions {4} | Max Inspiration {5})```"\
                    .format(format_big_number(entry[MAX_POWER]), format_big_number(entry[MAX_KP]), format_big_number(entry[MAX_MILITARY]), format_big_number(entry[MAX_FORTUNE]), format_big_number(entry[MAX_PROVISIONS]), format_big_number(entry[MAX_INSPIRATION]))
                response_str = response_str + "```Base Quality\n Military {0} | Fortune {1} | Provisions {2} | Inspiration {3}```"\
                    .format(entry[QUALITY_MILITARY], entry[QUALITY_FORTUNE], entry[QUALITY_PROVISIONS], entry[QUALITY_INSPIRATION])
                response_str = response_str + "```Quality Efficiency %\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                    .format(get_growth(entry[GROWTH_MILITARY], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_FORTUNE], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_PROVISIONS], entry[MAIDEN_GROWTH]), get_growth(entry[GROWTH_INSPIRATION], entry[MAIDEN_GROWTH]))
                response_str = response_str + "```Paragon % (Tome efficiency)\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                    .format(get_percent(entry[GROWTH_MILITARY]), get_percent(entry[GROWTH_FORTUNE]), get_percent(entry[GROWTH_PROVISIONS]), get_percent(entry[GROWTH_INSPIRATION]))
                response_str = response_str + "```\nRank (Power & KP)\n Max KP {0} | Power {1}```"\
                    .format(ranks[0], ranks[1])
                response_str = response_str + "```\nRank (Quality Efficiency)\n Military {0} | Fortune {1} | Provisions {2} | Inspiration {3}```"\
                    .format(ranks[2], ranks[3], ranks[4], ranks[5])
                response_str = response_str + "\n" + DM_BOT_MSG
                await message.channel.send(response_str)
            else:
                await message.channel.send("**{0}**\n ```Max KP Rating: {1} | Max Power Rating: {2} | Military Growth Rank: {3} | Fortune Growth Rank: {4} | Provisions Growth Rank: {5} | Inspiration Growth Rank: {6} | Difficulty {7}```".format(entry[HERO_NAME], ranks[0], ranks[1], ranks[2], ranks[3], ranks[4], ranks[5], entry[DIFFICULTY]))
        else:
            diffs = hero_name_diff(hero)
            await message.channel.send("Hero " + command + " not found. Close hero names: " + str(diffs))
    if command.startswith(POWER_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, POWER_TIER_LIST, command)
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
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero[MAX_POWER]) + ")\n"
            rank += 1

        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)
    if command.startswith(KP_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, MILITARY_TIER_LIST, command)
        if difficulty < 0:
            return

        difficulty_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            difficulty_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            difficulty_type = " (New Player)"

        tier_list_str = "**KP Tier List** " + difficulty_type + "\n"

        tier_list = create_attributes_tier_list(MAX_KP, difficulty, 20)
        rank = 1
        for hero in tier_list:
            tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero['Attributes']) + ")\n"
            rank += 1
        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)
    if command.startswith(MILITARY_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, MILITARY_TIER_LIST, command)
        if difficulty < 0:
            return
        if attributes:
            tier_list = create_attributes_tier_list(MAX_MILITARY, difficulty, 20)
        else:
            tier_list = create_growth_tier_list(MILITARY_GROWTH, difficulty, 20)

        difficulty_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            difficulty_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            difficulty_type = " (New Player)"

        tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
        tier_list_str = "**Military Tier List (" + tier_list_type + ")** " + difficulty_type + "\n"

        rank = 1
        for hero in tier_list:
            if attributes:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero['Attributes']) + ")\n"
            else:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%, " + format_big_number(hero['Attributes']) + ")\n"
            rank += 1
        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)
    if command.startswith(FORTUNE_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, FORTUNE_TIER_LIST, command)
        if difficulty < 0:
            return
        if attributes:
            tier_list = create_attributes_tier_list(MAX_FORTUNE, difficulty, 20)
        else:
            tier_list = create_growth_tier_list(FORTUNE_GROWTH, difficulty, 20)

        difficulty_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            difficulty_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            difficulty_type = " (New Player)"

        tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
        tier_list_str = "**Fortune Tier List (" + tier_list_type + ")** " + difficulty_type + "\n"

        rank = 1
        for hero in tier_list:
            if attributes:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero['Attributes']) + ")\n"
            else:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%, " + format_big_number(hero['Attributes']) + ")\n"
            rank += 1
            
        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)
    if command.startswith(PROVISIONS_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, PROVISIONS_TIER_LIST, command)
        if difficulty < 0:
            return
        if attributes:
            tier_list = create_attributes_tier_list(MAX_PROVISIONS, difficulty, 20)
        else:
            tier_list = create_growth_tier_list(PROVISIONS_GROWTH, difficulty, 20)

        difficulty_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            difficulty_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            difficulty_type = " (New Player)"

        tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
        tier_list_str = "**Provisions Tier List (" + tier_list_type + ")** " + difficulty_type + "\n"

        rank = 1
        for hero in tier_list:
            if attributes:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero['Attributes']) + ")\n"
            else:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%, " + format_big_number(hero['Attributes']) + ")\n"
            rank += 1

        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)
    if command.startswith(INSPIRATION_TIER_LIST):
        difficulty, attributes = await parse_tier_list_args(message, INSPIRATION_TIER_LIST, command)
        if difficulty < 0:
            return
        if attributes:
            tier_list = create_attributes_tier_list(MAX_INSPIRATION, difficulty, 20)
        else:
            tier_list = create_growth_tier_list(INSPIRATION_GROWTH, difficulty, 20)

        difficulty_type = ""
        if difficulty is LOW_VIP_DIFFICULTY:
            difficulty_type = " (Low VIP)"
        elif difficulty is NEW_PLAYER_DIFFICULTY:
            difficulty_type = " (New Player)"

        tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
        tier_list_str = "**Inspiration Tier List (" + tier_list_type + ")** " + difficulty_type + "\n"

        rank = 1
        for hero in tier_list:
            if attributes:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + format_big_number(hero['Attributes']) + ")\n"
            else:
                tier_list_str += str(rank) + ". " + hero['Hero Name'] + " (" + str(round(hero['Growth'])) + "%, " + format_big_number(hero['Attributes']) + ")\n"
            rank += 1
        await message.channel.send(tier_list_str + "\n" + DM_BOT_MSG)

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
    await message.channel.send(FORMULAS + ': Pulls up a formula sheet with a bunch of useful formulas such as KP, power etc.')
    await message.channel.send(ZODIACS + ': Pulls up a screenshot showing Zodiacs, their maidens and their paragons.')
    await message.channel.send(CASTLE_SKINS + ': Pulls up a screenshot of all current castle skins and there effects.')
    await message.channel.send('---------------------------------------------------------------------------')
    await message.channel.send('All tier lists can use the low VIP "-l" or new player "-n" flags to create a tier list geared towards lower spenders or new players')
    await message.channel.send(KP_TIER_LIST + ': Tier list for heroes maximum KP')
    await message.channel.send(POWER_TIER_LIST + ': Tier list for the strongest hero\'s rated by maximum power')
    await message.channel.send(MILITARY_TIER_LIST + ': Tier list for military growth. Use -a to switch to attributes')
    await message.channel.send(FORTUNE_TIER_LIST + ': Tier list for fortune growth. Use -a to switch to attributes')
    await message.channel.send(PROVISIONS_TIER_LIST + ': Tier list for provisions growth. Use -a to switch to attributes')
    await message.channel.send(INSPIRATION_TIER_LIST + ': Tier list for inspiration growth. Use -a to switch to attributes')
    await message.channel.send('You can send any of these commands to the bot by messaging it directly. Please consider doing so unless you\'re discussing the hero in the channel')

async def send_message_to_channel(channel_id, message):
    channel = await client.fetch_channel(channel_id)
    await channel.send(message)

def jotun_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Jotun time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), '@everyone\n Jotun himself has Joined the fight!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Jotun time'), client.loop)

def jotun_minions_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Jotun\'s minions time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun\'s minions time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), "@everyone\n Jotun has sent a surprise attack!!! Fight him back everyone!!!"), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Jotun\'s minions time'), client.loop)

def server_reset_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Daily server rest will be in 15 minutes'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), '@everyone Server will reset in 15 minutes. Be ready to collect your daily tithes and keep your maidens company!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Daily server rest will be in 15 minutes'), client.loop)

def boss_free_for_all_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Bosses will be a free for all in 30 minutes. If you have not hit bosses today please get your points in now.'), client.loop)

def cross_server_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), '@everyone A new cross server fight begins!!! Send your hero to battle in the alliance hall!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

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

    boss_free_for_all = (reset_hour - 2) % 24
    boss_free_for_all_str = '{:02d}:30'.format(boss_free_for_all)
    schedule.every().day.at(boss_free_for_all_str).do(boss_free_for_all_notifier)

    while True:
        time.sleep(1)
        schedule.run_pending()

def main():
    client.run(os.getenv('DISCORD_TOKEN'))
   
if __name__ == "__main__":
  main()
