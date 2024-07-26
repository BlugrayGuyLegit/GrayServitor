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

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="g!", intents=intents)
        self.remove_command('help')  # Supprimer la commande 'help' par défaut

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        # Load extensions
        await self.load_extension('level_commands')

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
        xp_needed = 60 * (2 ** user_data['Level'])

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

if __name__ == '__main__':
    bot.run(TOKEN)
