import discord
from discord.ext import commands
from langdetect import detect_langs
import asyncio
from config import BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

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
        await user.send("Please enter the name of the language/country you want to add:")

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
            lang_name = msg.content.strip().lower()

            # Détection de la langue avec langdetect
            detected_langs = detect_langs(lang_name)
            if detected_langs:
                lang_code = detected_langs[0].lang
                if lang_code not in LANGUAGE_ROLES:
                    LANGUAGE_ROLES.append(lang_code)
                    await user.send(f"Language '{lang_name}' has been added. React with ✅ to confirm.")
                    await reaction.message.add_reaction("✅")

                    def confirm_check(reaction, user):
                        return user == user and str(reaction.emoji) == "✅"

                    try:
                        confirm_reaction, _ = await bot.wait_for('reaction_add', check=confirm_check, timeout=60.0)
                        if confirm_reaction:
                            role = discord.utils.get(reaction.message.guild.roles, name=lang_code)
                            if role is None:
                                await reaction.message.guild.create_role(name=lang_code)
                            await user.send(f"The language '{lang_name}' has been successfully added!")
                    except asyncio.TimeoutError:
                        await user.send("You did not confirm in time. Please try again.")
                else:
                    await user.send(f"The language '{lang_name}' already exists.")
            else:
                await user.send(f"Could not detect the language '{lang_name}'. Please try again.")
        except asyncio.TimeoutError:
            await user.send("You did not respond in time. Please try again.")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if str(reaction.emoji) in LANGUAGE_FLAGS.values():
        lang = list(LANGUAGE_FLAGS.keys())[list(LANGUAGE_FLAGS.values()).index(str(reaction.emoji))]
        role = discord.utils.get(reaction.message.guild.roles, name=lang)
        if role:
            await user.add_roles(role)
            await user.send(f"You have been assigned the role for {lang}.")

        # Secret message for English and Spanish selection
        if lang in ["english", "spanish"]:
            await reaction.message.channel.send("Whoever move first is gay")

bot.run(BOT_TOKEN)
