import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.event
async def on_member_join(member):
    welcome_channel = member.guild.get_channel(1181438189949436045)
    
    if welcome_channel:
        await welcome_channel.send(f'Welcome to the server, {member.mention}!')

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError('DISCORD_BOT_TOKEN environment variable not set')
bot.run(TOKEN) 