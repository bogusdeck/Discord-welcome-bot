import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CHANNEL_ID = int(os.environ.get('WELCOME_CHANNEL_ID', '1181438189949436045'))
AUTOROLE_NAME = os.environ.get('AUTOROLE_NAME', 'Member')
PREFIX = os.environ.get('BOT_PREFIX', '!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync: {e}")

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name=AUTOROLE_NAME)
    if role:
        await member.add_roles(role)
    
    welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        embed = discord.Embed(
            title="Welcome!",
            description=f"Welcome to the server, {member.mention}! We're glad to have you here.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        await welcome_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if not message.guild:
        return
    
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.channel:
        log_channel = discord.utils.get(message.guild.text_channels, id=1181438189949436045)
        if log_channel:
            embed = discord.Embed(
                title="Message Deleted",
                description=message.content or "(no content)",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"User: {message.author} | Channel: {message.channel.name}")
            await log_channel.send(embed=embed)

message_counts = {}
spam_threshold = {}

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.guild:
        user_id = message.author.id
        channel_id = message.channel.id
        
        key = (user_id, channel_id)
        
        if key in message_counts:
            message_counts[key] += 1
            if message_counts[key] >= 3:
                if key not in spam_threshold:
                    spam_threshold[key] = datetime.utcnow() + timedelta(seconds=10)
                    try:
                        await message.channel.send(f"{message.author.mention}, slow down!", delete_after=5)
                    except:
                        pass
        else:
            message_counts[key] = 1
            await asyncio.sleep(15)
            if key in message_counts:
                del message_counts[key]
            if key in spam_threshold:
                del spam_threshold[key]
        
        if message.mention_counts and message.mention_counts >= 5:
            try:
                await message.delete()
                await message.author.send(f"You've been muted for mention spam in {message.guild.name}")
                await message.channel.send(f"{message.author.mention} has been muted for excessive mentions.")
            except:
                pass
    
    await bot.process_commands(message)

@bot.tree.command(name="clear", description="Clear messages from a channel")
@app_commands.describe(amount="Number of messages to clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int = 10):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.followup.send(f"Deleted {len(deleted) - 1} messages.", ephemeral=True)

@app.command(name="poll", help="Create a poll")
async def poll(ctx, question: str, *options):
    if len(options) < 2 or len(options) > 10:
        await ctx.send("Poll needs 2-10 options.")
        return
    
    embed = discord.Embed(
        title=question,
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )
    
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    
    for i, option in enumerate(options):
        embed.add_field(name=f"{emojis[i]} {option}", value="\u200b", inline=False)
    
    message = await ctx.send(embed=embed)
    
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

@bot.command(name="reactionrole")
@commands.has_permissions(manage_roles=True)
async def reactionrole(ctx, message_id: int, role_name: str, emoji: str):
    try:
        channel = ctx.channel
        message = await channel.fetch_message(message_id)
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        
        if not role:
            await ctx.send(f"Role '{role_name}' not found.")
            return
        
        await message.add_reaction(emoji)
        
        def check(reaction, user):
            return (
                reaction.message.id == message.id and
                str(reaction.emoji) == emoji and
                user == ctx.author
            )
        
        await ctx.send("Reaction role added! Users will get the role when they react.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id == 0:
        return
    
    reaction_role_data = getattr(bot, 'reaction_roles', {})
    
    if payload.message_id in reaction_role_data:
        guild = bot.get_guild(payload.guild_id)
        if guild:
            role = discord.utils.get(guild.roles, id=reaction_role_data[payload.message_id])
            member = guild.get_member(payload.user_id)
            if role and member:
                await member.add_roles(role)

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"Kicked {member}")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"Banned {member}")

@bot.command(name="mute")
@commands.has_permissions(mute_members=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    await member.edit(mute=True, reason=reason)
    await ctx.send(f"Muted {member}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"Error: {error}")

@bot.command(name="userinfo")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    
    embed = discord.Embed(
        title=f"User Info: {member}",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Roles", value=len(member.roles) - 1, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f"Server Info: {guild.name}",
        color=discord.Color.purple(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    
    await ctx.send(embed=embed)

reminders = {}

@bot.command(name="remind")
async def remind(ctx, when: str, *, message: str):
    import re
    match = re.match(r'(\d+)([smhd])', when)
    if not match:
        await ctx.send("Invalid format. Use: remind<time><unit> <message>\nExamples: remind5m Hello, remind1h Meeting at 3pm")
        return
    
    amount = int(match.group(1))
    unit = match.group(2)
    
    if unit == 's':
        delay = amount
    elif unit == 'm':
        delay = amount * 60
    elif unit == 'h':
        delay = amount * 3600
    elif unit == 'd':
        delay = amount * 86400
    
    async def send_reminder():
        await asyncio.sleep(delay)
        await ctx.send(f"🔔 Reminder: {message}")
    
    bot.loop.create_task(send_reminder())
    await ctx.send(f"Reminder set for {when} from now.")

@bot.command(name="points")
async def points(ctx, member: discord.Member = None):
    member = member or ctx.author
    points = getattr(member, 'points', 0)
    await ctx.send(f"{member.display_name} has {points} points.")

async def give_points(member: discord.Member, amount: int = 1):
    if not hasattr(member, 'points'):
        member.points = 0
    member.points += amount

TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError('DISCORD_BOT_TOKEN environment variable not set')
bot.run(TOKEN)