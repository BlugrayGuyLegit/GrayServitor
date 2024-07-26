import discord
from discord.ext import commands
from discord import app_commands
import firebase_admin
from firebase_admin import firestore

db = firestore.client()
xp_threshold = 60  # XP threshold for the first level

class LevelCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rank", description="Show your or another user's level and XP")
    @app_commands.describe(user="The user whose rank to show")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        user_ref = db.collection('users').document(str(user.id))
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            await interaction.response.send_message(f"{user.mention} is level {user_data['Level']} with {user_data['Xp']} XP.")
        else:
            await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

    @app_commands.command(name="add-xp", description="Add XP to a user")
    @app_commands.describe(user="The user to add XP to", amount="The amount of XP to add")
    @commands.has_permissions(manage_guild=True)
    async def add_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        user_ref = db.collection('users').document(str(user.id))
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['Xp'] += amount
            user_data = await self.check_level_up(user, user_data)
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

    @app_commands.command(name="add-level", description="Add level(s) to a user")
    @app_commands.describe(user="The user to add levels to", amount="The amount of levels to add")
    @commands.has_permissions(manage_guild=True)
    async def add_level(self, interaction: discord.Interaction, user: discord.Member, amount: int):
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

    @app_commands.command(name="remove-xp", description="Remove XP from a user")
    @app_commands.describe(user="The user to remove XP from", amount="The amount of XP to remove")
    @commands.has_permissions(manage_guild=True)
    async def remove_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        user_ref = db.collection('users').document(str(user.id))
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['Xp'] = max(0, user_data['Xp'] - amount)
            user_ref.set(user_data)
            await interaction.response.send_message(f"Removed {amount} XP from {user.mention}.")
        else:
            await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

    @app_commands.command(name="remove-level", description="Remove level(s) from a user")
    @app_commands.describe(user="The user to remove levels from", amount="The amount of levels to remove")
    @commands.has_permissions(manage_guild=True)
    async def remove_level(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        user_ref = db.collection('users').document(str(user.id))
        user_doc = user_ref.get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
            user_data['Level'] = max(0, user_data['Level'] - amount)
            user_ref.set(user_data)
            await interaction.response.send_message(f"Removed {amount} level(s) from {user.mention}.")
        else:
            await interaction.response.send_message(f"{user.mention} has no recorded XP or levels.")

    @app_commands.command(name="set-level", description="Set a user's level")
    @app_commands.describe(user="The user whose level to set", amount="The level to set")
    @commands.has_permissions(manage_guild=True)
    async def set_level(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        user_ref = db.collection('users').document(str(user.id))
        user_doc = user_ref.get()

        user_data = user_doc.to_dict() if user_doc.exists else {}
        user_data['User'] = user.name
        user_data['Xp'] = user_data.get('Xp', 0)
        user_data['Level'] = amount
        user_data['Id'] = user.id
        user_ref.set(user_data)

        await interaction.response.send_message(f"Set {user.mention}'s level to {amount}.")

    @app_commands.command(name="reset-level", description="Reset level and XP for a user or all users")
    @app_commands.describe(user="The user to reset (optional)")
    @commands.has_permissions(manage_guild=True)
    async def reset_level(self, interaction: discord.Interaction, user: discord.Member = None):
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

    @app_commands.command(name="leaderboard", description="Show the leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        users_ref = db.collection('users').order_by('Level', direction=firestore.Query.DESCENDING).limit(10)
        users = users_ref.stream()
        leaderboard_text = "\n".join([f"<@{user.id}>: Level {user.to_dict()['Level']}" for user in users])
        await interaction.response.send_message(f"Leaderboard:\n{leaderboard_text}")

    async def check_level_up(self, user, user_data):
        xp_needed = xp_threshold * (2 ** user_data['Level'])
        if user_data['Xp'] >= xp_needed:
            user_data['Level'] += 1
            user_data['Xp'] -= xp_needed
            await user.send(f"Congratulations! You've leveled up to level {user_data['Level']}!")
        return user_data

async def setup(bot):
    await bot.add_cog(LevelCommands(bot))
