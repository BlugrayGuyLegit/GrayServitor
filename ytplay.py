import discord
from discord.ext import commands
import youtube_dl

bot = commands.Bot(command_prefix='g!', intents=discord.Intents.voice_states())

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

@bot.command(name='stop')
async def stop(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        await ctx.send("I am not connected to a voice channel.")
        return
    await voice_client.disconnect()
    await ctx.send("Stopped playing music.")

bot.run(TOKEN)
