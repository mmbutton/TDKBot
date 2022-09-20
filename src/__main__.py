import time, threading, signal, sys, pytz, asyncio, os, sched
from pathlib import Path
from pytz import timezone
from datetime import datetime, timezone
import glob
import re
import os

#import redis
import discord
import schedule
from dotenv import load_dotenv

from command import command_names, command
from hero import hero_collection

load_dotenv()
#mem = redis.Redis()

# Dev tokens
client = discord.Client()

##############################################################################
# Global 1 line functions


# Growth is the coefficients from the KP formula (Paragon, Bond, Bronze)
get_percent = lambda n: int(float(n) * 100)


# Global variables
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

    command_str = message.content.lower()
    ## Debug
    ##if command.startswith('!server'):
        #await message.channel.send(mem.lrange("servers", 0, 0))
    ## All servers commands
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

async def send_message_to_channel(channel_id, message, publish = False):
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

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('MACKENZIE')), '@everyone Server will reset in 15 minutes. Be ready to collect your daily tithes and keep your maidens company!'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('S941')), '@everyone Daily server rest will be in 15 minutes'), client.loop)

def boss_free_for_all_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Bosses will be a free for all in 30 minutes. If you have not hit bosses today please get your points in now.'), client.loop)

def cross_server_notifier():
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.'), client.loop)

    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('COLLECTIVE')), '<@&' + os.getenv('COLLECTIVE_ALERTS') + '> New cross server fight is open. Please deploy a hero in the alliance hall.', True), client.loop)

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
    asyncio.run_coroutine_threadsafe(send_message_to_channel(int(os.getenv('GENERAL_CHAT')), '<@&' + os.getenv('BL_ALERTS') + '> Bosses will be opened shortly. Please limit your hits to 10B power (ie: 5k points)'), client.loop)

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
