from flask import Flask, request, jsonify
import os
import discord
from discord.ext import commands
import asyncio

app = Flask(__name__)

# Connect to the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="g!", intents=intents)

# Load your bot token and other environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

@app.route('/servers', methods=['GET'])
def get_servers():
    servers = []
    for guild in bot.guilds:
        servers.append({'id': guild.id, 'name': guild.name})
    return jsonify(servers)

@app.route('/channels/<int:server_id>', methods=['GET'])
def get_channels(server_id):
    channels = []
    guild = discord.utils.get(bot.guilds, id=server_id)
    if guild:
        for channel in guild.channels:
            channels.append({'id': channel.id, 'name': channel.name, 'type': str(channel.type)})
    return jsonify(channels)

@app.route('/messages/<int:channel_id>', methods=['GET'])
def get_messages(channel_id):
    channel = bot.get_channel(channel_id)
    messages = []
    if channel:
        async def fetch_messages():
            async for message in channel.history(limit=10):  # Fetch the last 10 messages
                messages.append({'author': message.author.name, 'content': message.content, 'timestamp': str(message.created_at)})
            return jsonify(messages)
        return bot.loop.run_until_complete(fetch_messages())
    else:
        return jsonify({'error': 'Channel not found'}), 404

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    channel_id = data.get('channel_id')
    message_content = data.get('message')
    
    channel = bot.get_channel(int(channel_id))
    if channel:
        async def send_msg():
            await channel.send(message_content)
            return jsonify({'status': 'Message sent'})
        return bot.loop.run_until_complete(send_msg())
    else:
        return jsonify({'error': 'Channel not found'}), 404

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.start(DISCORD_TOKEN))
    app.run(host='0.0.0.0', port=5000)
