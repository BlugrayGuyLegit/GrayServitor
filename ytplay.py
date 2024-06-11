import os
import discord
from discord.ext import commands
import youtube_dl

TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='g!', intents=discord.Intents.default())

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

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(member="The member to warn", reason="The reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member.id not in warn_counts:
        warn_counts[member.id] = 0
    warn_counts[member.id] += 1
    await interaction.response.send_message(f"{member.mention} has been warned for: {reason}. Total warnings: {warn_counts[member.id]}")

@bot.tree.command(name="unwarn", description="Remove a warning from a user")
@app_commands.describe(member="The member to unwarn")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if member.id in warn_counts and warn_counts[member.id] > 0:
        warn_counts[member.id] -= 1
        await interaction.response.send_message(f"Removed a warning from {member.mention}. Total warnings: {warn_counts[member.id]}")
    else:
        await interaction.response.send_message(f"{member.mention} has no warnings.", ephemeral=True)

@bot.tree.command(name="warns", description="Show warnings of all users")
async def warns(interaction: discord.Interaction):
    if not warn_counts:
        await interaction.response.send_message("No warnings to display.")
        return
    warn_list = "\n".join([f"<@{user_id}>: {count} warn(s)" for user_id, count in warn_counts.items()])
    await interaction.response.send_message(warn_list)

bot.run(TOKEN)
