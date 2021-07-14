from dotenv import load_dotenv
import discord, logging, os

load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user))

client.run(bot_token)