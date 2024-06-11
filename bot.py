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
        super().__init__(command_prefix="!", intents=intents)
        self.remove_command('help')  # Supprimer la commande 'help' par défaut

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="!help for any information!"))
    print(f'Bot is online as {bot.user}')

# Commande pour afficher le rang ou le niveau d'un utilisateur avec différents alias
@bot.command(name="rank", aliases=["level", "lvl"])
async def rank(ctx, user: discord.Member = None):
    user = user or ctx.author
    user_level = levels.get(user.id, 0)
    user_xp = xp.get(user.id, 0)
    await ctx.send(f"{user.mention} is level {user_level} with {user_xp} XP.")

# Commandes pour ajouter de l'XP ou des niveaux
@bot.command(name="add-xp")
@commands.has_permissions(manage_guild=True)
async def add_xp(ctx, user: discord.Member, amount: int):
    if user.id not in xp:
        xp[user.id] = 0
    xp[user.id] += amount
    await check_level_up(user)
    await ctx.send(f"Added {amount} XP to {user.mention}.")

@bot.command(name="add-level")
@commands.has_permissions(manage_guild=True)
async def add_level(ctx, user: discord.Member, amount: int):
    if user.id not in levels:
        levels[user.id] = 0
    levels[user.id] += amount
    await ctx.send(f"Added {amount} level(s) to {user.mention}.")

# Commandes pour supprimer de l'XP ou des niveaux
@bot.command(name="remove-xp")
@commands.has_permissions(manage_guild=True)
async def remove_xp(ctx, user: discord.Member, amount: int):
    if user.id not in xp:
        xp[user.id] = 0
    xp[user.id] = max(0, xp[user.id] - amount)
    await ctx.send(f"Removed {amount} XP from {user.mention}.")

@bot.command(name="remove-level")
@commands.has_permissions(manage_guild=True)
async def remove_level(ctx, user: discord.Member, amount: int):
    if user.id not in levels:
        levels[user.id] = 0
    levels[user.id] = max(0, levels[user.id] - amount)
    await ctx.send(f"Removed {amount} level(s) from {user.mention}.")

# Commande pour définir un niveau spécifique
@bot.command(name="set-level")
@commands.has_permissions(manage_guild=True)
async def set_level(ctx, user: discord.Member, amount: int):
    levels[user.id] = amount
    await ctx.send(f"Set {user.mention}'s level to {amount}.")

# Commande pour réinitialiser le niveau d'un utilisateur
@bot.command(name="reset-level")
@commands.has_permissions(manage_guild=True)
async def reset_level(ctx, user: discord.Member = None):
    if user:
        levels[user.id] = 0
        xp[user.id] = 0
        await ctx.send(f"Reset level and XP for {user.mention}.")
    else:
        levels.clear()
        xp.clear()
        await ctx.send("Reset levels and XP for all users.")

# Commande pour afficher le classement des utilisateurs
@bot.command(name="leaderboard")
async def leaderboard(ctx):
    sorted_levels = sorted(levels.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user_id}>: Level {level}" for user_id, level in sorted_levels])
    await ctx.send(f"Leaderboard:\n{leaderboard_text}")

# Commande pour envoyer un message dans un salon choisi (modérateurs uniquement)
@bot.command(name="say")
@commands.has_permissions(manage_guild=True)
async def say(ctx, channel: discord.TextChannel, *, message: str):
    await channel.send(message)
    await ctx.send(f"Message sent to {channel.mention}.")

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
        "!rank | !level | !lvl [user] - Show your or another user's level and XP.\n"
        "!add-xp <user> <amount> - Add XP to a user.\n"
        "!add-level <user> <amount> - Add level(s) to a user.\n"
        "!remove-xp <user> <amount> - Remove XP from a user.\n"
        "!remove-level <user> <amount> - Remove level(s) from a user.\n"
        "!set-level <user> <amount> - Set a user's level.\n"
        "!reset-level [user] - Reset level and XP for a user or all users.\n"
        "!leaderboard - Show the leaderboard.\n"
        "!say <channel> <message> - Send a message to a specific channel (moderators only)."
    )
    await ctx.send(help_text)

if __name__ == '__main__':
    bot.run(TOKEN)
