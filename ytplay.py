import os
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash import SlashCommand, SlashContext
import youtube_dl
import asyncio
import time

TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='g!', intents=discord.Intents.default())
slash = SlashCommand(bot, sync_commands=True)

last_message = {}
spam_count = {}

@bot.event
async def on_message(message):
    if message.author.bot or isinstance(message.channel, discord.DMChannel):
        return

    if message.author.id in last_message:
        time_difference = time.time() - last_message[message.author.id]
        if time_difference < 3:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, please don't send messages too quickly.")
            # Alert automod channel
            automod_channel = discord.utils.get(message.guild.channels, name="automod-alerts")
            if automod_channel:
                await automod_channel.send(f"Automod alert: {message.author.mention} sent messages too quickly.")
                # Delete the alert message after 5 seconds
                bot_msg = await automod_channel.send("Automod alert message will be deleted in 5 seconds.")
                await asyncio.sleep(5)
                await bot_msg.delete()
            else:
                await message.channel.send("Automod alerts channel not found. Please configure it.")
            spam_count[message.author.id] = spam_count.get(message.author.id, 0) + 1
            if spam_count[message.author.id] >= 5:
                spam_count[message.author.id] = 0
        
    last_message[message.author.id] = time.time()

    await bot.process_commands(message)

@bot.command(name='play')
async def play(ctx, url: str):
    voice_channel = ctx.author.voice.channel
    if voice_channel is None:
        await ctx.send("You must first join a voice channel.")
        return
    await voice_channel.connect()
    voice_client = ctx.guild.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        voice_client.play(discord.FFmpegPCMAudio(url2), after=lambda e: print('done', e))
        await ctx.send("Playing music.")

@slash.slash(name="removesuspect", description="Remove Suspect role from a user")
async def remove_suspect(ctx: SlashContext):
    if ctx.author.guild_permissions.manage_roles:
        # Remove auto role rule for marking spam messages
        await remove_auto_role_rule(ctx.guild)
        # Send alert to automod channel
        automod_channel = discord.utils.get(ctx.guild.channels, name="automod-alerts")
        if automod_channel:
            await automod_channel.send("Automod rules have been reset.")
        else:
            await ctx.send("Automod alerts channel not found. Please configure it.")
    else:
        await ctx.send("You do not have permission to manage roles.")

@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        await asyncio.sleep(5)
        try:
            await message.delete()
        except discord.Forbidden:
            pass

async def remove_auto_role_rule(guild):
    # Function to remove auto role rule (placeholder for your implementation)
    pass

bot.run(TOKEN)
