
from pathlib import Path
import discord
from math import log10, floor

from command import command_names
from hero import hero_collection

DM_BOT_MSG = "For longer commands consider DMing the bot to avoid flooding the chat."
#This should become private at some point
# Rounds to 3 sig figs similar to KT. Ie: 1.56M instead of 1,562,020... I hate this thing
round_3sigfig = lambda n: '{:,g}'.format(round(n, 3-int(floor(log10(abs(n))))-1))
def format_big_number(num):
    suffixes = ["", "K", "M", "B", "T", "Q"]
    first_numbers = float("{:.2e}".format(int(num))[:4])

    num = "{:,}".format(int(num))
    if len(num.split(',')[0]) == 2:
        first_numbers = float(first_numbers) * 10
    elif len(num.split(',')[0]) == 3:
        first_numbers = float(first_numbers) * 100
    return round_3sigfig(first_numbers) + suffixes[num.count(',')]

# Converts numbers to their orindal (1st, second etc)
_ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

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

async def hero(message, hero, detailed):
    entry = hero_collection.get_hero(hero)
    if entry is not None:
        ranks = [
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.KP)),
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.POWER)),
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.MILITARY)),
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.FORTUNE)),
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.PROVISIONS)),
                _ordinal(hero_collection.hero_rank(hero, hero_collection.TierList.INSPIRATION))
        ]
        if detailed:
            response_str = "**{0}**\n".format(entry.hero_name)
            response_str = response_str + "```Max Attributes (lvl 400)\nMax Power {0} | Max KP {1} | Max Military {2} | Max Fortune {3} | Max Provisions {4} | Max Inspiration {5})```"\
                .format(format_big_number(entry.max_power), format_big_number(entry.max_kp), format_big_number(entry.max_military), format_big_number(entry.max_fortune), format_big_number(entry.max_provisions), format_big_number(entry.max_inspiration))
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
            response_str = response_str + "\n" + DM_BOT_MSG
            await message.channel.send(response_str)
        else:
            await message.channel.send("**{0}**\n ```Max KP Rating: {1} | Max Power Rating: {2} | Military Growth Rank: {3} | Fortune Growth Rank: {4} | Provisions Growth Rank: {5} | Inspiration Growth Rank: {6} | Difficulty {7}```".format(entry.hero_name, ranks[0], ranks[1], ranks[2], ranks[3], ranks[4], ranks[5], entry.difficulty))
    else:
        diffs = hero_collection.hero_name_diff(hero)
        await message.channel.send("Hero " + hero + " not found. Close hero names: " + str(diffs))

async def help(message):
    helpStr = '**______Command List________**\n'

    # All server commands
    helpStr += command_names.EVENT_SCHEDULE + ': Posts an image of the event schedule for challenges and cross server events\n'
    helpStr += command_names.HERO + ': Shows the rating of the hero compared to others. Use -d to see fully detailed stats, use -i to pull up an infographic.\n'
    helpStr += command_names.FORMULAS + ': Pulls up a formula sheet with a bunch of useful formulas such as KP, power etc.'
    helpStr += command_names.ZODIACS + ': Pulls up a screenshot showing Zodiacs, their maidens and their paragons.\n'
    helpStr += command_names.CASTLE_SKINS + ': Pulls up a screenshot of all current castle skins and there effects.\n'
    helpStr += command_names.MANU_EFFICIENCY + ': Pulls up Haka\'s inforgraphic showing manuscript batch efficiency\n'
    helpStr += '---------------------------------------------------------------------------\n'
    helpStr += 'All tier lists can use the low VIP "-l" or new player "-n" flags to create a tier list geared towards lower spenders or new players\n'
    helpStr += command_names.KP_TIER_LIST + ': Tier list for heroes maximum KP\n'
    helpStr += command_names.POWER_TIER_LIST + ': Tier list for the strongest hero\'s rated by maximum power\n'
    helpStr += command_names.MILITARY_TIER_LIST + ': Tier list for military growth. Use -a to switch to attributes\n'
    helpStr += command_names.FORTUNE_TIER_LIST + ': Tier list for fortune growth. Use -a to switch to attributes\n'
    helpStr += command_names.PROVISIONS_TIER_LIST + ': Tier list for provisions growth. Use -a to switch to attributes\n'
    helpStr += command_names.INSPIRATION_TIER_LIST + ': Tier list for inspiration growth. Use -a to switch to attributes\n'
    helpStr += 'You can send any of these commands to the bot by messaging it directly. Please consider doing so unless you\'re discussing the hero in the channel\n'
    await message.channel.send(helpStr)