

import glob, os, re, argparse
from pathlib import Path
import discord
from math import log10, floor

from command import command_names
from hero import hero_collection

_LOW_VIP_DIFFICULTY = 4
_NEW_PLAYER_DIFFICULTY = 3
_DM_BOT_MSG = "For a longer list use the '-s' option. For instance \"!power_tier_list -s 25\". Please use DM's to the bot for long lists."
_LONG_BOT_LIST_MSG = "List is too large and will likely flood whatever channel you are using. Please switch to a DM or reduce the size of the list you are generating."
_LONG_BOT_MSG = "For longer commands consider DMing the bot to avoid flooding the chat."


# Rounds to 3 sig figs similar to KT. Ie: 1.56M instead of 1,562,020... I hate this thing
def _round_3sigfig(n):
    return '{:,g}'.format(round(n, 3 - int(floor(log10(abs(n)))) - 1))

class ArgumentParserError(Exception):
    pass

class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)

async def parse_tier_list_args(message, prog, command):
    try:
        parser = ThrowingArgumentParser(prog, add_help=False)
        parser.add_argument('--new', '-n', action='store_true')
        parser.add_argument('--low_vip', '-l', action='store_true')
        parser.add_argument('--attributes', '-a', action='store_true')
        parser.add_argument('--size', '-s', type=int)
        args = parser.parse_args(command.split()[1:])

        if args.new and args.low_vip:
            await message.channel.send("Can only specify one of new or low econ")
            return -1

        listLength = 10
        if args.size:
            listLength = args.size

        difficulty = 101
        if args.new:
            difficulty = _NEW_PLAYER_DIFFICULTY
        if args.low_vip:
            difficulty = _LOW_VIP_DIFFICULTY
        return difficulty, args.attributes, listLength

    except ArgumentParserError:
        await message.channel.send("Unknown arguments detected. Only \"-l\" flag for low_vip or \"-n\" for new players are accepted for arguments")
        return -1, False

def _get_hero_inforgraphic(hero_name):
    matches = []
    path = Path(__file__).parent / '../../resources/milo_infographics/*'
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

def _format_big_number(num):
    suffixes = ["", "K", "M", "B", "T", "Q"]
    first_numbers = float("{:.2e}".format(int(num))[:4])

    num = "{:,}".format(int(num))
    if len(num.split(',')[0]) == 2:
        first_numbers = float(first_numbers) * 10
    elif len(num.split(',')[0]) == 3:
        first_numbers = float(first_numbers) * 100
    return _round_3sigfig(first_numbers) + suffixes[num.count(',')]

async def _send_long_string_msg(discordMessage, messageString):
    if discordMessage.channel.type != discord.ChannelType.private and len(messageString) > 1000:
        await discordMessage.channel.send(_LONG_BOT_LIST_MSG)
    for chunk in [messageString[i: i + 1999] for i in range(0, len(messageString), 1999)]:
        await discordMessage.channel.send(chunk)

# Converts numbers to their orindal (1st, second etc)
def _ordinal(n):
    return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

async def formulas(message):
    return await message.channel.send(file=discord.File(Path(__file__).parent / '../../resources/formulas.png'))

async def zodiacs(message):
    return await message.channel.send(file=discord.File(Path(__file__).parent / '../../resources/zodiacs.png'))

async def castle_skins(message):
    return await message.channel.send(file=discord.File(Path(__file__).parent / '../../resources/castle_skins.png'))

async def event_schedule(message):
    return await message.channel.send(file=discord.File(Path(__file__).parent / '../../resources/event_schedule.png'))

async def manuscript_efficiency(message):
    return await message.channel.send(file=discord.File(Path(__file__).parent / '../../resources/manu_efficiency.png'))

async def hero(message, command_str):
    command_str = command_str[(len(command_names.HERO) + 1):].replace('‘', '\'').replace('’', '\'')
    if command_str.startswith("-i"):
        command_str = command_str[3:]
        filename = _get_hero_inforgraphic(command_str)
        if filename is not None:
            await message.channel.send(file=discord.File(Path(__file__).parent / filename))
        else:
            diffs = hero_collection.hero_name_diff(command_str.lower())
            await message.channel.send("Hero " + command_str + " not found. Close hero names: " + str(diffs))
        return

    detailed = False
    if command_str.startswith("-d"):
        detailed = True
        command_str = command_str[3:]
    hero = command_str.lower()

    entry = hero_collection.get_hero(hero)
    if entry is not None:
        ranks = [
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.KP)),
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.POWER)),
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.MILITARY)),
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.FORTUNE)),
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.PROVISIONS)),
            _ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.INSPIRATION))
        ]
        if detailed:
            response_str = "**{0}**\n".format(entry.hero_name)
            response_str = response_str + "```Max Attributes (lvl 400)\nMax Power {0} | Max KP {1} | Max Military {2} | Max Fortune {3} | Max Provisions {4} | Max Inspiration {5})```"\
                .format(_format_big_number(entry.max_power), _format_big_number(entry.max_kp), _format_big_number(entry.max_military), _format_big_number(entry.max_fortune),
                        _format_big_number(entry.max_provisions), _format_big_number(entry.max_inspiration))
            response_str = response_str + "```Base Quality\n Military {0} | Fortune {1} | Provisions {2} | Inspiration {3}```"\
                .format(entry.military_quality, entry.fortune_quality, entry.provisions_quality, entry.inspiration_quality)
            response_str = response_str + "```Quality Efficiency %\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                .format(entry.military_growth, entry.fortune_growth, entry.provisions_growth, entry.inspiration_growth)
            response_str = response_str + "```Paragon % (Tome efficiency)\n Military {0}% | Fortune {1}% | Provisions {2}% | Inspiration {3}%```"\
                .format(int(entry.military_paragon * 100), int(entry.fortune_paragon * 100), int(entry.provisions_paragon * 100), int(entry.inspiration_paragon * 100))
            response_str = response_str + "```\nRank (KP | Power)\n Max KP {0} | Power {1}```"\
                .format(ranks[0], ranks[1])
            response_str = response_str + "```\nRank (Quality Efficiency)\n Military {0} | Fortune {1} | Provisions {2} | Inspiration {3}```"\
                .format(ranks[2], ranks[3], ranks[4], ranks[5])
            response_str = response_str + "\n" + _LONG_BOT_MSG
            await message.channel.send(response_str)
        else:
            response_str = "**{0}**\n".format(entry.hero_name)
            response_str = response_str + "```Max KP Rating: {0} | Max Power Rating: {1} | Military Growth Rank: {2} | Fortune Growth Rank: {3} | Provisions Growth Rank: {4} |"\
                .format(ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])
            response_str = response_str + "Inspiration Growth Rank: {0} | Difficulty {1}```".format(ranks[5], entry.difficulty)
            await message.channel.send(response_str)
    else:
        diffs = hero_collection.hero_name_diff(hero)
        await message.channel.send("Hero " + hero + " not found. Close hero names: " + str(diffs))

async def power_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.POWER_TIER_LIST, command_str)
    if difficulty < 0:
        return
    tier_list = hero_collection.create_attributes_tier_list(
        hero_collection.TierList.POWER, difficulty, listLength)

    tier_list_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        tier_list_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        tier_list_type = " (New Player)"

    tier_list_str = "**Power Tier List**" + tier_list_type + "\n"

    rank = 1
    for hero in tier_list:
        tier_list_str += str(rank) + ". " + hero.hero_name + \
            " (" + _format_big_number(hero.max_power) + ")\n"
        rank += 1

    await _send_long_string_msg(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def kp_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.KP_TIER_LIST, command_str)
    if difficulty < 0:
        return

    difficulty_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        difficulty_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        difficulty_type = " (New Player)"

    tier_list_str = "**KP Tier List** " + difficulty_type + "\n"

    tier_list = hero_collection.create_attributes_tier_list(
        hero_collection.TierList.KP, difficulty, listLength)
    rank = 1
    for hero in tier_list:
        tier_list_str += str(rank) + ". " + hero.hero_name + \
            " (" + _format_big_number(hero.max_kp) + ")\n"
        rank += 1
    await message.channel.send(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def military_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.MILITARY_TIER_LIST, command_str)
    if difficulty < 0:
        return
    if attributes:
        tier_list = hero_collection.create_attributes_tier_list(
            hero_collection.TierList.MILITARY, difficulty, listLength)
    else:
        tier_list = hero_collection.create_growth_tier_list(
            hero_collection.TierList.MILITARY, difficulty, listLength)

    difficulty_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        difficulty_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        difficulty_type = " (New Player)"

    tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
    tier_list_str = "**Military Tier List (" + \
        tier_list_type + ")** " + difficulty_type + "\n"

    rank = 1
    for hero in tier_list:
        if attributes:
            tier_list_str += str(rank) + ". " + hero.hero_name + \
                " (" + _format_big_number(hero.max_military) + ")\n"
        else:
            tier_list_str += str(rank) + ". " + hero.hero_name + " (" + str(round(
                hero.military_growth)) + "%, " + _format_big_number(hero.max_military) + ")\n"
        rank += 1
    await _send_long_string_msg(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def fortune_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.FORTUNE_TIER_LIST, command_str)
    if difficulty < 0:
        return
    if attributes:
        tier_list = hero_collection.create_attributes_tier_list(
            hero_collection.TierList.FORTUNE, difficulty, listLength)
    else:
        tier_list = hero_collection.create_growth_tier_list(
            hero_collection.TierList.FORTUNE, difficulty, listLength)

    difficulty_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        difficulty_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        difficulty_type = " (New Player)"

    tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
    tier_list_str = "**Fortune Tier List (" + \
        tier_list_type + ")** " + difficulty_type + "\n"

    rank = 1
    for hero in tier_list:
        if attributes:
            tier_list_str += str(rank) + ". " + hero.hero_name + \
                " (" + _format_big_number(hero.max_fortune) + ")\n"
        else:
            tier_list_str += str(rank) + ". " + hero.hero_name + " (" + str(round(
                hero.fortune_growth)) + "%, " + _format_big_number(hero.max_fortune) + ")\n"
        rank += 1

    await _send_long_string_msg(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def provisions_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.PROVISIONS_TIER_LIST, command_str)
    if difficulty < 0:
        return
    if attributes:
        tier_list = hero_collection.create_attributes_tier_list(
            hero_collection.TierList.PROVISIONS, difficulty, listLength)
    else:
        tier_list = hero_collection.create_growth_tier_list(
            hero_collection.TierList.PROVISIONS, difficulty, listLength)

    difficulty_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        difficulty_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        difficulty_type = " (New Player)"

    tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
    tier_list_str = "**Provisions Tier List (" + \
        tier_list_type + ")** " + difficulty_type + "\n"

    rank = 1
    for hero in tier_list:
        if attributes:
            tier_list_str += str(rank) + ". " + hero.hero_name + \
                " (" + _format_big_number(hero.max_provisions) + ")\n"
        else:
            tier_list_str += str(rank) + ". " + hero.hero_name + " (" + str(round(
                hero.provisions_growth)) + "%, " + _format_big_number(hero.max_provisions) + ")\n"
        rank += 1

    await _send_long_string_msg(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def inspiration_tier_list(message, command_str):
    difficulty, attributes, listLength = await parse_tier_list_args(message, command_names.INSPIRATION_TIER_LIST, command_str)
    if difficulty < 0:
        return
    if attributes:
        tier_list = hero_collection.create_attributes_tier_list(
            hero_collection.TierList.INSPIRATION, difficulty, listLength)
    else:
        tier_list = hero_collection.create_growth_tier_list(
            hero_collection.TierList.INSPIRATION, difficulty, listLength)

    difficulty_type = ""
    if difficulty is _LOW_VIP_DIFFICULTY:
        difficulty_type = " (Low VIP)"
    elif difficulty is _NEW_PLAYER_DIFFICULTY:
        difficulty_type = " (New Player)"

    tier_list_type = "Max Attributes" if attributes else "Quality Efficiency"
    tier_list_str = "**Inspiration Tier List (" + \
        tier_list_type + ")** " + difficulty_type + "\n"

    rank = 1
    for hero in tier_list:
        if attributes:
            tier_list_str += str(rank) + ". " + hero.hero_name + \
                " (" + _format_big_number(hero.max_inspiration) + ")\n"
        else:
            tier_list_str += str(rank) + ". " + hero.hero_name + " (" + str(round(
                hero.inspiration_growth)) + "%, " + _format_big_number(hero.max_inspiration) + ")\n"
        rank += 1
    await _send_long_string_msg(message, tier_list_str + "\n" + _DM_BOT_MSG)

async def help(message):
    helpStr = '**______Command List________**\n'

    # All server commands
    helpStr += command_names.EVENT_SCHEDULE + \
        ': Posts an image of the event schedule for challenges and cross server events\n'
    helpStr += command_names.HERO + \
        ': Shows the rating of the hero compared to others. Use -d to see fully detailed stats, use -i to pull up an infographic.\n'
    helpStr += command_names.FORMULAS + \
        ': Pulls up a formula sheet with a bunch of useful formulas such as KP, power etc.'
    helpStr += command_names.ZODIACS + \
        ': Pulls up a screenshot showing Zodiacs, their maidens and their paragons.\n'
    helpStr += command_names.CASTLE_SKINS + \
        ': Pulls up a screenshot of all current castle skins and there effects.\n'
    helpStr += command_names.MANU_EFFICIENCY + \
        ': Pulls up Haka\'s inforgraphic showing manuscript batch efficiency\n'
    helpStr += '---------------------------------------------------------------------------\n'
    helpStr += 'All tier lists can use the low VIP "-l" or new player "-n" flags to create a tier list geared towards lower spenders or new players\n'
    helpStr += command_names.KP_TIER_LIST + ': Tier list for heroes maximum KP\n'
    helpStr += command_names.POWER_TIER_LIST + \
        ': Tier list for the strongest hero\'s rated by maximum power\n'
    helpStr += command_names.MILITARY_TIER_LIST + \
        ': Tier list for military growth. Use -a to switch to attributes\n'
    helpStr += command_names.FORTUNE_TIER_LIST + \
        ': Tier list for fortune growth. Use -a to switch to attributes\n'
    helpStr += command_names.PROVISIONS_TIER_LIST + \
        ': Tier list for provisions growth. Use -a to switch to attributes\n'
    helpStr += command_names.INSPIRATION_TIER_LIST + \
        ': Tier list for inspiration growth. Use -a to switch to attributes\n'
    helpStr += 'You can send any of these commands to the bot by messaging it directly. Please consider doing so unless you\'re discussing the hero in the channel\n'
    await message.channel.send(helpStr)
