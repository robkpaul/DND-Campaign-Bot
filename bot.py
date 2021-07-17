from dotenv import load_dotenv
import discord, logging, os, re, datetime, pymongo

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')
mongo_URI = os.getenv('MONGODB_URI')

mongoClient = pymongo.MongoClient(mongo_URI, ssl=True, ssl_cert_reqs='CERT_NONE')
questDB = mongoClient['Modron']['Quests']

botClient = discord.Client()

checkmark = '✅'

async def quest_command(message, args):
    quest = {}
    quest['title'] = args[1]
    dateOf = datetime.date(datetime.datetime.now().year, int(args[3]), int(args[4]))
    timeOf = datetime.time(int(args[6]), int(args[7]))
    quest['time'] = timeOf
    if dateOf < datetime.datetime.now().date():
        dateOf = datetime.date(datetime.datetime.now().year+1, dateOf.month, dateOf.day)
    quest['date'] = dateOf
    quest['creator'] = message.author
    quest['members'] = []

    questResponse = discord.Embed(title = 'Quest: %s' % quest['title'])
    questResponse.add_field(name='Creator', value=quest['creator'].mention)
    questResponse.add_field(name='Scheduled For', value=quest['date'].strftime('%A, %m/%d')+ ' @ '+quest['time'].strftime('%H:%S'))
    questResponse.add_field(name=chr(173), value=chr(173))
    questResponse.add_field(name='Party Members', value=quest['creator'].mention+'\n')
    questResponse.set_footer(text='React with a %s to join.' % checkmark)
    
    msg = await message.channel.send(embed = questResponse)
    await msg.add_reaction(checkmark)


#reads commands in and directs to the correct command
async def cmd_reader(message):
    msg = message.content
    if msg.startswith('$quest '):
        questRegex = re.compile(r'("(.{1,})") (([0-1]\d)\/(\d{2})) (([0-1]\d)\:(\d{2}))')
        questArgs = re.match(questRegex, msg[7:])
        if questArgs:
            await quest_command(message, questArgs.groups())
        else:
            await message.channel.send('Incorrect format for the $quest command')

@botClient.event
async def on_ready():
    print('Logged in as {}'.format(botClient.user))

@botClient.event
async def on_message(message):
    if message.author != botClient.user and message.content.startswith('$'):
        await cmd_reader(message) 
    elif message.author == botClient.user:
        return

@botClient.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == botClient.user and user != botClient.user:
        if len(reaction.message.embeds) > 0:
            if reaction.message.embeds[0].title.startswith('Quest:') and str(reaction.emoji) == checkmark and user.mention != reaction.message.embeds[0].fields[0].value:
                    party = reaction.message.embeds[0].fields[3]
                    newEmbed = reaction.message.embeds[0].set_field_at(3, name=party.name, value=party.value+' '+user.mention)
                    await reaction.message.edit(embed = newEmbed)

botClient.run(bot_token)