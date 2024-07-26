import discord
from discord.ext import commands
from discord import app_commands
import os
import firebase_admin
from firebase_admin import credentials, firestore

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))

# Initialize Firebase
cred = credentials.Certificate('https://grayservitor-default-rtdb.europe-west1.firebasedatabase.app/')
firebase_admin.initialize_app(cred)
db = firestore.client()

xp_threshold = 60  # XP threshold for the first level

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
    await bot.change_presence(activity=discord.Game(name="V3.0 | g!help for help !"))
    print(f'Bot is online as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_ref = db.collection('users').document(str(message.author.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['Xp'] += 15
        xp_needed = xp_threshold * (2 ** user_data['Level'])

        if user_data['Xp'] >= xp_needed:
            user_data['Level'] += 1
            user_data['Xp'] -= xp_needed
            await message.channel.send(f"Congratulations {message.author.mention}, you've leveled up to level {user_data['Level']}!")
    else:
        user_data = {
            'User': message.author.name,
            'Xp': 15,
            'Level': 0,
            'Id': message.author.id
        }

    user_ref.set(user_data)
    await bot.process_commands(message)

@bot.tree.command(name="rank", description="Show your or another user's level and XP")
@app_commands.describe(user="The user whose rank to show")
async def rank(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        await interaction.response.send_message(f"{user.mention} is level {user_data['Level']} with {user_data['Xp']} XP.")
    else:
        await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

@bot.tree.command(name="add-xp", description="Add XP to a user")
@app_commands.describe(user="The user to add XP to", amount="The amount of XP to add")
@commands.has_permissions(manage_guild=True)
async def add_xp(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['Xp'] += amount
        await check_level_up(user, user_data)
        user_ref.set(user_data)
        await interaction.response.send_message(f"Added {amount} XP to {user.mention}.")
    else:
        user_data = {
            'User': user.name,
            'Xp': amount,
            'Level': 0,
            'Id': user.id
        }
        user_ref.set(user_data)
        await interaction.response.send_message(f"Added {amount} XP to {user.mention}.")

@bot.tree.command(name="add-level", description="Add level(s) to a user")
@app_commands.describe(user="The user to add levels to", amount="The amount of levels to add")
@commands.has_permissions(manage_guild=True)
async def add_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['Level'] += amount
        user_ref.set(user_data)
        await interaction.response.send_message(f"Added {amount} level(s) to {user.mention}.")
    else:
        user_data = {
            'User': user.name,
            'Xp': 0,
            'Level': amount,
            'Id': user.id
        }
        user_ref.set(user_data)
        await interaction.response.send_message(f"Added {amount} level(s) to {user.mention}.")

@bot.tree.command(name="remove-xp", description="Remove XP from a user")
@app_commands.describe(user="The user to remove XP from", amount="The amount of XP to remove")
@commands.has_permissions(manage_guild=True)
async def remove_xp(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['Xp'] = max(0, user_data['Xp'] - amount)
        user_ref.set(user_data)
        await interaction.response.send_message(f"Removed {amount} XP from {user.mention}.")
    else:
        await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

@bot.tree.command(name="remove-level", description="Remove level(s) from a user")
@app_commands.describe(user="The user to remove levels from", amount="The amount of levels to remove")
@commands.has_permissions(manage_guild=True)
async def remove_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data['Level'] = max(0, user_data['Level'] - amount)
        user_ref.set(user_data)
        await interaction.response.send_message(f"Removed {amount} level(s) from {user.mention}.")
    else:
        await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

@bot.tree.command(name="set-level", description="Set a user's level")
@app_commands.describe(user="The user whose level to set", amount="The level to set")
@commands.has_permissions(manage_guild=True)
async def set_level(interaction: discord.Interaction, user: discord.Member, amount: int):
    user_ref = db.collection('users').document(str(user.id))
    user_doc = user_ref.get()

    user_data = user_doc.to_dict() if user_doc.exists else {}
    user_data['User'] = user.name
    user_data['Xp'] = user_data.get('Xp', 0)
    user_data['Level'] = amount
    user_data['Id'] = user.id
    user_ref.set(user_data)
    
    await interaction.response.send_message(f"Set {user.mention}'s level to {amount}.")

@bot.tree.command(name="reset-level", description="Reset level and XP for a user or all users")
@app_commands.describe(user="The user to reset (optional)")
@commands.has_permissions(manage_guild=True)
async def reset_level(interaction: discord.Interaction, user: discord.Member = None):
    if user:
        user_ref = db.collection('users').document(str(user.id))
        user_ref.set({'User': user.name, 'Xp': 0, 'Level': 0, 'Id': user.id})
        await interaction.response.send_message(f"Reset level and XP for {user.mention}.")
    else:
        users_ref = db.collection('users')
        users = users_ref.stream()
        for user in users:
            user_ref = db.collection('users').document(user.id)
            user_ref.set({'User': user.to_dict().get('User'), 'Xp': 0, 'Level': 0, 'Id': int(user.id)})
        await interaction.response.send_message("Reset levels and XP for all users.")

@bot.tree.command(name="leaderboard", description="Show the leaderboard")
async def leaderboard(interaction: discord.Interaction):
    users_ref = db.collection('users').order_by('Level', direction=firestore.Query.DESCENDING).limit(10)
    users = users_ref.stream()
    leaderboard_text = "\n".join([f"<@{user.id}>: Level {user.to_dict().get('Level')}" for user in users])
    await interaction.response.send_message(f"Leaderboard:\n{leaderboard_text}")

@bot.tree.command(name="say", description="Send a message to a specific channel")
@app_commands.describe(channel="The channel to send the message to", message="The message to send")
@commands.has_permissions(manage_guild=True)
async def say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    await channel.send(message)
    await interaction.response.send_message(f"Message sent to {channel.mention}.")

async def check_level_up(user, user_data):
    xp_needed = xp_threshold * (2 ** user_data['Level'])
    if user_data['Xp'] >= xp_needed:
        user_data['Level'] += 1
        user_data['Xp'] -= xp_needed
        await user.send(f"Congratulations! You've leveled up to level {user_data['Level']}!")
    return user_data

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

@bot.tree.command(name="banned", description="Show all banned users and the reasons for their bans")
async def banned(interaction: discord.Interaction):
    await interaction.response.defer()
    guild = interaction.guild
    try:
        banned_users = []
        async for ban_entry in guild.bans():
            banned_users.append(ban_entry)

        if not banned_users:
            await interaction.followup.send("No users are banned from this guild.")
            return

        embed = discord.Embed(title="Banned Users", color=discord.Color.orange())
        for ban_entry in banned_users:
            user = ban_entry.user
            reason = ban_entry.reason or "No reason provided"
            embed.add_field(name=f"{user.name}#{user.discriminator}", value=f"Reason: {reason}", inline=False)

        await interaction.followup.send(embed=embed)
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission to view banned users.")
    except discord.HTTPException as e:
        await interaction.followup.send(f"An error occurred while fetching banned users: {e}")

# Commande ping
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! {latency}ms')

@bot.command(name="skibidi")
async def skibidi(ctx):
    embed = discord.Embed(
        title="Skibidi toilet song",
        description=("Hey skibidi sigma rizzer, there is the skibidi toilet song:\n\n"
                     "(Sometimes I looks like ridiculous) Brrrrrr skibidi dop dop yes yes skibidi dop neeh neeh "
                     "skibidi dop dop dop yes yes skibidi dop neeh neeh everyone want to party skibidi skibidi "
                     "skibidi...")
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    await ctx.send(embed=embed)

# Commande info
@bot.command(name="info")
async def info(ctx):
    with open('info.txt', 'r') as file:
        info_text = file.read()
    await ctx.send(info_text)

if __name__ == '__main__':
    bot.run(TOKEN)
