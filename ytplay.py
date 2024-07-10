import os
import discord
from discord.ext import commands
import asyncio
import time

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
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

# Les drapeaux des pays et leurs langues
LANGUAGE_FLAGS = {
    "english": "🇬🇧",
    "spanish": "🇪🇸",
    "french": "🇫🇷",
    "russian": "🇷🇺",
    "hindi": "🇮🇳"
}
LANGUAGE_ROLES = ["english", "spanish", "french", "russian", "hindi"]

# L'embed de sélection de langue
@bot.command(name='select_language')
async def select_language(ctx):
    embed = discord.Embed(title="Choose your language", description="Select your language by reacting with the corresponding flag. Click on ➕ to add a new language.")
    message = await ctx.send(embed=embed)
    
    for lang, flag in LANGUAGE_FLAGS.items():
        await message.add_reaction(flag)
    await message.add_reaction("➕")

# Gestion des réactions pour ajouter une nouvelle langue
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.emoji == "➕":
        await user.send("Please enter the flag of the country/language you want to add:")
        
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)
        
        try:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
            flag = msg.content.strip()
            
            if flag in LANGUAGE_FLAGS.values():
                await user.send(f"The language for this flag already exists.")
            else:
                await user.send(f"Language with flag '{flag}' has been added. React with ✅ to confirm.")
                await reaction.message.add_reaction("✅")
                
                def confirm_check(reaction, user):
                    return user == user and str(reaction.emoji) == "✅"
                
                try:
                    confirm_reaction, _ = await bot.wait_for('reaction_add', check=confirm_check, timeout=60.0)
                    if confirm_reaction:
                        lang_name = flag  # Use the flag itself as the language identifier
                        LANGUAGE_FLAGS[lang_name] = flag
                        LANGUAGE_ROLES.append(lang_name)
                        
                        role = discord.utils.get(reaction.message.guild.roles, name=lang_name)
                        if role is None:
                            await reaction.message.guild.create_role(name=lang_name)
                        await user.send(f"The language with flag '{flag}' has been successfully added!")
                except asyncio.TimeoutError:
                    await user.send("You did not confirm in time. Please try again.")
        except asyncio.TimeoutError:
            await user.send("You did not respond in time. Please try again.")

    if str(reaction.emoji) in LANGUAGE_FLAGS.values():
        lang = list(LANGUAGE_FLAGS.keys())[list(LANGUAGE_FLAGS.values()).index(str(reaction.emoji))]
        role = discord.utils.get(reaction.message.guild.roles, name=lang)
        if role:
            await user.add_roles(role)
            await user.send(f"You have been assigned the role for {lang}.")
        
        # Secret message for English and Spanish selection
        if lang in ["english", "spanish"]:
            await reaction.message.channel.send("Whoever moves first is gay")
            
bot.run(TOKEN)
