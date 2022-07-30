from command import command_names
from pathlib import Path
import discord

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