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

@bot.tree.command(name="say", description="Send a message to a specific channel")
@app_commands.describe(channel="The channel to send the message to", message="The message to send")
@commands.has_permissions(manage_guild=True)
async def say(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    await channel.send(message)
    await interaction.response.send_message(f"Message sent to {channel.mention}.")

@bot.command(name="help")
async def help_command(ctx):
    help_text = (
        "Available commands:\n"
        "g!ping - Check the bot's latency.\n"
        "g!skibidi - Skibidi toilet song.\n"
        "g!info - Show bot information.\n"
        "/say - Send a message to a specific channel (moderators only).\n"
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

@bot.command(name="info")
async def info(ctx):
    with open('info.txt', 'r') as file:
        info_text = file.read()
    await ctx.send(info_text)

if __name__ == '__main__':
    bot.run(TOKEN)
