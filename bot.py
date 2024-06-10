import discord
from discord.ext import commands
from discord import app_commands
import os
from discord.ui import Modal, TextInput
import spotipy
from spotipy.oauth2 import SpotifyOAuth

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="g!", intents=intents)
        self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                                                 client_secret=SPOTIFY_CLIENT_SECRET,
                                                                 redirect_uri=SPOTIFY_REDIRECT_URI,
                                                                 scope="user-modify-playback-state,user-read-playback-state"))

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="g!help for any information!"))
    print(f'Bot is online as {bot.user}')

warn_counts = {}
ticket_category_id = 1210339937539325973  # ID de la catégorie de ticket

# Spotify Commands
@bot.command(name="play")
async def play(ctx, link: str):
    try:
        bot.spotify.start_playback(uris=[link])
        await ctx.send(f"Playing track: {link}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="stop")
async def stop(ctx):
    try:
        bot.spotify.pause_playback()
        await ctx.send("Playback stopped.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="next")
async def next(ctx):
    try:
        bot.spotify.next_track()
        await ctx.send("Skipped to the next track.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="queue")
async def queue(ctx):
    try:
        current_track = bot.spotify.current_playback()
        if current_track and current_track['item']:
            track = current_track['item']
            track_info = f"Currently playing: {track['name']} by {', '.join(artist['name'] for artist in track['artists'])}"
            await ctx.send(track_info)
        else:
            await ctx.send("No track is currently playing.")
    except Exception as e:
        await ctx.send(f"Error: {e}")

# Existing Commands
@bot.tree.command(name="clear", description="Clear messages")
@app_commands.describe(amount="The number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Amount must be positive.", ephemeral=True)
        return
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {amount} messages.", ephemeral=True)

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

@bot.tree.command(name="mute", description="Mute a user")
@app_commands.describe(member="The member to mute", reason="The reason for the mute")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str):
    await member.edit(mute=True)
    await interaction.response.send_message(f"{member.mention} has been muted for: {reason}.")

@bot.tree.command(name="unmute", description="Unmute a user")
@app_commands.describe(member="The member to unmute")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.edit(mute=False)
    await interaction.response.send_message(f"{member.mention} has been unmuted.")

class TicketModal(Modal):
    def __init__(self):
        super().__init__(title="Create a Ticket")
        self.reason = TextInput(label="Reason", placeholder="Enter the reason for the ticket")
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason.value
        category = discord.utils.get(interaction.guild.categories, id=ticket_category_id)
        if category is None:
            await interaction.response.send_message("Ticket category not found.", ephemeral=True)
            return
        channel = await category.create_text_channel(name=f"ticket-{interaction.user.name}")
        await channel.send(f"{interaction.user.mention} created a ticket with the reason: {reason}")
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket", description="Create a ticket")
async def ticket(interaction: discord.Interaction):
    await interaction.response.send_modal(TicketModal())

@bot.tree.command(name="close", description="Close the current ticket")
async def close(interaction: discord.Interaction):
    if interaction.channel.category and interaction.channel.category.id == ticket_category_id:
        await interaction.channel.delete()
    else:
        await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! {latency}ms')

@bot.command(name="info")
async def info(ctx):
    with open('info.txt', 'r') as file:
        info_text = file.read()
    await ctx.send(info_text)

if __name__ == '__main__':
    bot.run(TOKEN)
