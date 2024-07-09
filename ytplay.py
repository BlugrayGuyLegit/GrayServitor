import os
import discord
from discord.ext import commands
import youtube_dl
import time  # Import time module for timestamp comparison

TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='g!', intents=discord.Intents.default())

# Dictionary to keep track of the last message timestamp per user
last_message = {}

@bot.event
async def on_message(message):
    # Check if the message author is a bot or the message is from a DM
    if message.author.bot or isinstance(message.channel, discord.DMChannel):
        return

    # Check if the user has sent a message before
    if message.author.id in last_message:
        # Calculate the time difference between the current message and the last message
        time_difference = time.time() - last_message[message.author.id]
        
        # If the time difference is less than 3 seconds, delete the message and notify the user
        if time_difference < 3:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, please don't send messages too quickly.")
    
    # Update the last message timestamp for the user
    last_message[message.author.id] = time.time()

    # Continue with processing other commands if any
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

# Run the bot
bot.run(TOKEN)
