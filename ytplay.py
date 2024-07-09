import os
import discord
from discord.ext import commands
import asyncio
import time

TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='g!', intents=discord.Intents.default())

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

    # Replace this with your actual music playing logic
    await ctx.send("Playing music.")

bot.run(TOKEN)
