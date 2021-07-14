from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import discord, logging, os, gspread

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')

gspread_creds = ServiceAccountCredentials.from_json_keyfile_name('google_sheets_key.json', scopes = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
gspread_client = gspread.authorize(gspread_creds)
gamelog = gspread_client.open('Warden Campaign Tracker').worksheet('Session Log')

gamelog.update_cell(100, 1, "Hello World!")

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {}'.format(client.user))

client.run(bot_token)