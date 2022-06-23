import os

# Command list
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
MANU_EFFICIENCY = '!manuscript_efficiency'

async def help(message):
    helpStr = '**______Command List________**\n'
    # BL only commands
    if(message.guild is not None):
        if os.getenv('BL_SERVER_ID') == str(message.guild.id):
            helpStr += TOURNEY_FARM + ': Creates a table of safely farmable individuals (inactive and low KP/hero ratio)\n'

    # All server commands
    helpStr += EVENT_SCHEDULE + ': Posts an image of the event schedule for challenges and cross server events\n'
    helpStr += HERO + ': Shows the rating of the hero compared to others. Use -d to see fully detailed stats, use -i to pull up an infographic.\n'
    helpStr += FORMULAS + ': Pulls up a formula sheet with a bunch of useful formulas such as KP, power etc.'
    helpStr += ZODIACS + ': Pulls up a screenshot showing Zodiacs, their maidens and their paragons.\n'
    helpStr += CASTLE_SKINS + ': Pulls up a screenshot of all current castle skins and there effects.\n'
    helpStr += MANU_EFFICIENCY + ': Pulls up Haka\'s inforgraphic showing manuscript batch efficiency\n'
    helpStr += '---------------------------------------------------------------------------\n'
    helpStr += 'All tier lists can use the low VIP "-l" or new player "-n" flags to create a tier list geared towards lower spenders or new players\n'
    helpStr += KP_TIER_LIST + ': Tier list for heroes maximum KP\n'
    helpStr += POWER_TIER_LIST + ': Tier list for the strongest hero\'s rated by maximum power\n'
    helpStr += MILITARY_TIER_LIST + ': Tier list for military growth. Use -a to switch to attributes\n'
    helpStr += FORTUNE_TIER_LIST + ': Tier list for fortune growth. Use -a to switch to attributes\n'
    helpStr += PROVISIONS_TIER_LIST + ': Tier list for provisions growth. Use -a to switch to attributes\n'
    helpStr += INSPIRATION_TIER_LIST + ': Tier list for inspiration growth. Use -a to switch to attributes\n'
    helpStr += 'You can send any of these commands to the bot by messaging it directly. Please consider doing so unless you\'re discussing the hero in the channel\n'
    await message.channel.send(helpStr)