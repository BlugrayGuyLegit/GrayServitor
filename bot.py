import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="g!", intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="My Status"))
    print(f'Bot is online as {bot.user}')

@bot.tree.command(name="clear", description="Clear messages")
@app_commands.describe(amount="The number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Amount must be positive.", ephemeral=True)
        return
    await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"Deleted {amount} messages.", ephemeral=True)

warn_counts = {}

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(member="The member to warn", reason="The reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if member.id not in warn_counts:
        warn_counts[member.id] = 0
    warn_counts[member.id] += 1
    await interaction.response.send_message(f"{member.mention} has been warned for: {reason}. Total warnings: {warn_counts[member.id]}")

@bot.command(name="info")
async def info(ctx):
    with open('info.txt', 'r') as file:
        info_text = file.read()
    await ctx.send(info_text)

bot.run(TOKEN)
