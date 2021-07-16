from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import discord, logging, os, gspread, re

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')

gspread_creds = ServiceAccountCredentials.from_json_keyfile_name('google_sheets_key.json', scopes = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
gspread_client = gspread.authorize(gspread_creds)
gamelog = gspread_client.open(input("Spreadsheet for session log: ")).worksheet('Session Log')

client = discord.Client()

async def quest_command(message):
    msg = message.content[message.content.find('"')+1:]

#reads commands
async def cmd_reader(message):
    msg = message.content
    if msg.startswith('$quest'):
        if('"' in msg and '"' in msg[msg.find('"')+1:] and '/' in msg and ':' in msg):
            #quest_command(message)
            print("quest message registered")
        else:
            await message.channel.send('Incorrect format for the $quest command')


@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user))

@client.event
async def on_message(message):
    if message.author != client.user and message.content.startswith('$'):
        cmd_reader(message)

client.run(bot_token)