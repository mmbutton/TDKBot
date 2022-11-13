import time
import threading
import asyncio
import os
from pathlib import Path
import os
import enum

# import redis
import discord
from discord import app_commands
import schedule
from dotenv import main

# Dotenv must read the files before imports otherwise the .env variables will be None
main.load_dotenv()
from command import command_names, command
from command.coffee_client import CoffeeClient
from hero import hero_collection



intents = discord.Intents.default()
intents.message_content = True
client = CoffeeClient(intents=intents)

# mem = redis.Redis()

# Global variables
SUNDAY = 0
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6

@client.tree.command(description="Pulls up a formula sheet with a bunch of useful formulas such as KP, power etc.")
async def formulas(interaction):
    await interaction.response.send_message(file=discord.File(Path(__file__).parent / '../resources/formulas.png'))
    
@client.tree.command(description="Pulls up a screenshot showing Zodiacs, their maidens and their paragons.")
async def zodiacs(interaction):
    await interaction.response.send_message(file=discord.File(Path(__file__).parent / '../resources/zodiacs.png'))

@client.tree.command(description = "Pulls up a screenshot of all current castle skins and their effects.")
async def castle_skins(interaction):
    await interaction.response.send_message(file=discord.File(Path(__file__).parent / '../resources/castle_skins.png'))
    
@client.tree.command(description = "Posts an image of the event schedule for challenges and cross server events.")
async def event_schedule(interaction):
    await interaction.response.send_message(file=discord.File(Path(__file__).parent / '../resources/event_schedule.png'))
    
@client.tree.command(description = "Pulls up Haka\'s inforgraphic showing manuscript batch efficiency")
async def manuscript_efficiency(interaction):
    await interaction.response.send_message(file=discord.File(Path(__file__).parent / '../resources/manu_efficiency.png'))
    
@client.tree.command(description = "Get a hero inforgraphic created by Milo")
@app_commands.describe(hero_name="Name of the hero to get")
async def hero_infographic(interaction, hero_name: str):
    hero_name = hero_name.replace('‘', '\'').replace('’', '\'').lower()
    filename = command.get_hero_inforgraphic(hero_name)
    if filename is not None:
        await interaction.response.send_message(file=discord.File(Path(__file__).parent / filename))
    else:
        diffs = hero_collection.hero_name_diff(hero_name)
        await interaction.response.send_message("Hero " + hero_name + " not found. Close hero names: " + str(diffs))
        
@client.tree.command(description = "Get hero statistics")
@app_commands.describe(hero_name="Name of the hero to get", detailed="Use detailed statistics")
async def hero(interaction, hero_name: str, detailed: bool = True):
    hero = hero_name.replace('‘', '\'').replace('’', '\'').lower()
    entry = hero_collection.get_hero(hero)
    if entry is not None:
        ranks = [
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.KINGDOM_POWER)),
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.MILITARY_POWER)),
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.MILITARY)),
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.FORTUNE)),
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.PROVISIONS)),
            command.ordinal(hero_collection.hero_rank(
                hero, hero_collection.TierList.INSPIRATION))
        ]
        if detailed:
            response_str = "**{0}**\n".format(entry.hero_name)
            response_str = response_str + "```Max Attributes (lvl 400)\nMax Power {0} | Max KP {1} | Max Military {2} | Max Fortune {3} | Max Provisions {4} | Max Inspiration {5})```"\
                .format(command.format_big_number(entry.max_power), command.format_big_number(entry.max_kp), command.format_big_number(entry.max_military), command.format_big_number(entry.max_fortune),
                        command.format_big_number(entry.max_provisions), command.format_big_number(entry.max_inspiration))
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
            response_str = response_str + "\n" + command._LONG_BOT_MSG
            await interaction.response.send_message(response_str)
        else:
            response_str = "**{0}**\n".format(entry.hero_name)
            response_str = response_str + "```Max KP Rating: {0} | Max Power Rating: {1} | Military Growth Rank: {2} | Fortune Growth Rank: {3} | Provisions Growth Rank: {4} |"\
                .format(ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])
            response_str = response_str + "Inspiration Growth Rank: {0} | Difficulty {1}```".format(ranks[5], entry.difficulty)
            await interaction.response.send_message(response_str)
    else:
        diffs = hero_collection.hero_name_diff(hero)
        await interaction.response.send_message("Hero " + hero + " not found. Close hero names: " + str(diffs))

@client.tree.command(description = "Generate a tier list based on max attributes of heroes")
@app_commands.describe(type="Type of tier list to generate", size="Size of the tier list")
async def attribute_tier_list(interaction, type: hero_collection.TierList, size: app_commands.Range[int, 0, 200] = 10):
    tier_list = hero_collection.create_attributes_tier_list(type, 100, size)
    tier_list_str = "**{0} Attribute Tier List**\n".format(type.value)

    rank = 1
    for hero in tier_list:
        if type is hero_collection.TierList.MILITARY:
            attribute = hero.max_military
        elif type is hero_collection.TierList.FORTUNE:
            attribute = hero.max_fortune
        elif type is hero_collection.TierList.PROVISIONS:
            attribute = hero.max_provisions
        elif type is hero_collection.TierList.INSPIRATION:
            attribute = hero.max_inspiration
        elif type is hero_collection.TierList.KINGDOM_POWER:
            attribute = hero.max_kp
        elif type is hero_collection.TierList.MILITARY_POWER:
            attribute = hero.max_power
        tier_list_str += "{0}. {1} ({2})\n".format(rank, hero.hero_name, command.format_big_number(attribute))
        rank += 1

    await interaction.response.send_message(tier_list_str + "\n" + command._LONG_BOT_MSG)

class TierListGrowths(enum.Enum):
    MILITARY = hero_collection.TierList.MILITARY
    FORTUNE = hero_collection.TierList.FORTUNE
    PROVISIONS = hero_collection.TierList.PROVISIONS
    INSPIRATION = hero_collection.TierList.INSPIRATION
    
    
@client.tree.command(description = "Generate a tier list based on growth of heroes")
@app_commands.describe(type="Type of tier list to generate", size="Size of the tier list")
async def growth_tier_list(interaction, type: hero_collection.TierList, size: app_commands.Range[int, 0, 200] = 10):
    tier_list = hero_collection.create_growth_tier_list(type, 100, size)
    tier_list_str = "**{0} Growth Tier List**\n".format(type.value)

    rank = 1
    for hero in tier_list:
        if type is hero_collection.TierList.MILITARY:
            attribute = hero.max_military
            growth = hero.military_growth
        elif type is hero_collection.TierList.FORTUNE:
            attribute = hero.max_fortune
            growth = hero.fortune_growth
        elif type is hero_collection.TierList.PROVISIONS:
            attribute = hero.max_provisions
            growth = hero.provisions_growth
        elif type is hero_collection.TierList.INSPIRATION:
            attribute = hero.max_inspiration
            growth = hero.inspiration_growth
        tier_list_str += "{0}. {1} ({2}%, {3})\n".format(rank, hero.hero_name, round(growth), command.format_big_number(attribute))
        rank += 1

    await interaction.response.send_message(tier_list_str + "\n" + command._LONG_BOT_MSG)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command_str = message.content.lower()
    # Debug
    # if command.startswith('!server'):
    # await message.channel.send(mem.lrange("servers", 0, 0))
    # All servers commands
    if command_str.startswith('!help'):
        await command.help(message)
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
    if command_str.startswith(command_names.FORMULAS):
        await command.formulas(message)
    if command_str.startswith(command_names.ZODIACS):
        await command.zodiacs(message)
    if command_str.startswith(command_names.CASTLE_SKINS):
        await command.castle_skins(message)
    if command_str.startswith(command_names.EVENT_SCHEDULE):
        await command.event_schedule(message)
    if command_str.startswith(command_names.MANU_EFFICIENCY):
        await command.manuscript_efficiency(message)
    if command_str.startswith(command_names.HERO):
        await command.hero(message, command_str)
    if command_str.startswith(command_names.POWER_TIER_LIST):
        await command.power_tier_list(message, command_str)
    if command_str.startswith(command_names.KP_TIER_LIST):
        await command.kp_tier_list(message, command_str)
    if command_str.startswith(command_names.MILITARY_TIER_LIST):
        await command.military_tier_list(message, command_str)
    if command_str.startswith(command_names.FORTUNE_TIER_LIST):
        await command.fortune_tier_list(message, command_str)
    if command_str.startswith(command_names.PROVISIONS_TIER_LIST):
        await command.provisions_tier_list(message, command_str)
    if command_str.startswith(command_names.INSPIRATION_TIER_LIST):
        await command.inspiration_tier_list(message, command_str)


async def send_message_to_channel(channel_id, message, publish=False):
    channel = await client.fetch_channel(channel_id)
    msg = await channel.send(message)
    if publish:
        await msg.publish()


def jotun_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Jotun time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun time', True), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), '@everyone\n Jotun himself has Joined the fight!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Jotun time'), client.loop)


def jotun_minions_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Jotun\'s minions time'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Jotun\'s minions time', True), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), "@everyone\n Jotun has sent a surprise attack!!! Fight him back everyone!!!"), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Jotun\'s minions time'), client.loop)


def server_reset_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> Daily server rest will be in 15 minutes', True), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')),
                                     '@everyone Server will reset in 15 minutes. Be ready to collect your daily tithes and keep your maidens company!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Daily server rest will be in 15 minutes'), client.loop)


def boss_free_for_all_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS')
                                     + '> Bosses will be a free for all in 15 minutes. The invincible boss will be opened in 30min'), client.loop)


def cross_server_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS')
                                     + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS')
                                     + '> New cross server fight is open. Please deploy a hero in the alliance hall.', True), client.loop)

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
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS')
                                     + '> Bosses will be opened shortly. Please limit your hits to 10B power (ie: 5k points)'), client.loop)


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
    notifier = threading.Thread(target=notifier_thread)
    notifier.daemon = True
    notifier.start()
    client.run(os.getenv('DISCORD_TOKEN'))


if __name__ == "__main__":
    main()
