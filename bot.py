import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

# Variables globales pour les niveaux et l'XP
levels = {}
xp = {}
xp_threshold = 100

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="g!", intents=intents)
        self.remove_command('help')  # Supprimer la commande 'help' par défaut

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="g!help for any information!"))
    print(f'Bot is online as {bot.user}')

# Commande pour afficher le rang ou le niveau d'un utilisateur avec différents alias
@bot.tree.command(name="rank", description="Show your or another user's level and XP")
@app_commands.describe(user="The user whose rank to show")
async def rank(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    user_level = levels.get(user.id, 0)
    user_xp = xp.get(user.id, 0)
    await interaction.response.send_message(f"{user.mention} is level {user_level} with {user_xp} XP.")

# Commandes pour ajouter de l'XP ou des niveaux
@bot.tree.command(name="add-xp", description="Add XP to a user")
@app_commands.describe(user="The user to add XP to", amount="The amount of XP to add")
@commands.has_permissions(manage_guild=True)
async def add_xp(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id not in xp:
        xp[user.id] = 0
    xp[user.id] += amount
    await check_level_up(user)
    await interaction.response.send_message(f"Added {amount} XP to {user.mention}.")

@bot.tree.command(name="add-level", description="Add level(s) to a user")
@app_commands.describe(user="The user to add levels to", amount="The amount of levels to add")
@commands.has_permissions(manage_guild=True)
async def add_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id not in levels:
        levels[user.id] = 0
    levels[user.id] += amount
    await interaction.response.send_message(f"Added {amount} level(s) to {user.mention}.")

# Commandes pour supprimer de l'XP ou des niveaux
@bot.tree.command(name="remove-xp", description="Remove XP from a user")
@app_commands.describe(user="The user to remove XP from", amount="The amount of XP to remove")
@commands.has_permissions(manage_guild=True)
async def remove_xp(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id not in xp:
        xp[user.id] = 0
    xp[user.id] = max(0, xp[user.id] - amount)
    await interaction.response.send_message(f"Removed {amount} XP from {user.mention}.")

@bot.tree.command(name="remove-level", description="Remove level(s) from a user")
@app_commands.describe(user="The user to remove levels from", amount="The amount of levels to remove")
@commands.has_permissions(manage_guild=True)
async def remove_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user.id not in levels:
        levels[user.id] = 0
    levels[user.id] = max(0, levels[user.id] - amount)
    await interaction.response.send_message(f"Removed {amount} level(s) from {user.mention}.")

# Commande pour définir un niveau spécifique
@bot.tree.command(name="set-level", description="Set a user's level")
@app_commands.describe(user="The user whose level to set", amount="The level to set")
@commands.has_permissions(manage_guild=True)
async def set_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    levels[user.id] = amount
    await interaction.response.send_message(f"Set {user.mention}'s level to {amount}.")

# Commande pour réinitialiser le niveau d'un utilisateur
@bot.tree.command(name="reset-level", description="Reset level and XP for a user or all users")
@app_commands.describe(user="The user to reset (optional)")
@commands.has_permissions(manage_guild=True)
async def reset_level(interaction: discord.Interaction, user: discord.Member = None):
    if user:
        levels[user.id] = 0
        xp[user.id] = 0
        await interaction.response.send_message(f"Reset level and XP for {user.mention}.")
    else:
        levels.clear()
        xp.clear()
        await interaction.response.send_message("Reset levels and XP for all users.")

# Commande pour afficher le classement des utilisateurs
@bot.tree.command(name="leaderboard", description="Show the leaderboard")
async def leaderboard(interaction: discord.Interaction):
    sorted_levels = sorted(levels.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user_id}>: Level {level}" for user_id, level in sorted_levels])
    await interaction.response.send_message(f"Leaderboard:\n{leaderboard_text}")

# Commande pour envoyer un message dans un salon choisi (modérateurs uniquement)
@bot.tree.command(name="say", description="Send a message to a specific channel")
@app_commands.describe(channel="The channel to send the message to", message="The message to send")
@commands.has_permissions(manage_guild=True)
async def say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    await channel.send(message)
    await interaction.response.send_message(f"Message sent to {channel.mention}.")

# Fonction pour vérifier le niveau supérieur
async def check_level_up(user):
    user_xp = xp[user.id]
    user_level = levels.get(user.id, 0)
    if user_xp >= (user_level + 1) * xp_threshold:
        levels[user.id] = user_level + 1
        await user.send(f"Congratulations! You've leveled up to level {levels[user.id]}!")

# Commande d'aide personnalisée
@bot.command(name="help")
async def help_command(ctx):
    help_text = (
        "Available commands:\n"
        "g!rank | g!level | g!lvl [user] - Show your or another user's level and XP.\n"
        "/add-xp <user> <amount> - Add XP to a user.\n"
        "/add-level <user> <amount> - Add level(s) to a user.\n"
        "/remove-xp <user> <amount> - Remove XP from a user.\n"
        "/remove-level <user> <amount> - Remove level(s) from a user.\n"
        "/set-level <user> <amount> - Set a user's level.\n"
        "/reset-level [user] - Reset level and XP for a user or all users.\n"
        "/leaderboard - Show the leaderboard.\n"
        "/say <channel> <message> - Send a message to a specific channel (moderators only).\n"
        "g!ping - Check the bot's latency.\n"
        "g!skibidi - Skibidi toilet song.\n"
        "g!info - Show bot information."
    )
    await ctx.send(help_text)

# Commande ping
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! {latency}ms')

# Commande skibidi
@bot.command(name="skibidi")
async def skibidi(ctx):
    embed = discord.Embed(
        title="Skibidi toilet song",
        description=("Hey skibidi sigma rizzer, there is the skibidi toilet song:\n\n"
                     "(Sometimes I looks like ridiculous) Brrrrrr skibidi dop dop yes yes skibidi dop neeh neeh "
                     "skibidi dop dop dop yes yes skibidi dop neeh neeh everyone want to party skibidi skibidi "
                     "skibidi..."),
        footer=f"requested by {ctx.author.name}"
    )
    await ctx.send(embed=embed)

# Commande info
@bot.command(name="info")
async def info(ctx):
    with open('info.txt', 'r') as file:
        info_text = file.read()
    await ctx.send(info_text)

if __name__ == '__main__':
    bot.run(TOKEN)
