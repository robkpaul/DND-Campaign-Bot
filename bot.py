from dotenv import load_dotenv
import discord, logging, os, re, datetime, motor.motor_asyncio

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')
mongo_URI = os.getenv('MONGODB_URI')

mongoClient = motor.motor_asyncio.AsyncIOMotorClient(mongo_URI, serverSelectionTimeoutMS=5000, ssl=True, ssl_cert_reqs='CERT_NONE') # Client for the Motor MongoDB
questDB = mongoClient['Modron']['Quests'] # Goes to the specific Database then Collection for this project.

botClient = discord.Client() 

checkmark = '✅' # easier to type 'checkmark' than the emoji

async def quest_command(message, args):
    quest = {}
    #getting the elements of the quest from the provided arguments
    quest['title'] = args[1]
    dateTimeOf = datetime.datetime.strptime(args[2], '%m/%d %H:%M')
    dateTimeOf = dateTimeOf.replace(year=datetime.datetime.now().year)
    if dateTimeOf < datetime.datetime.now():
        dateTimeOf = dateTimeOf.replace(year=dateTimeOf.year+1)
    quest['datetime'] = dateTimeOf.strftime('%A, %m/%d/%y, %I:%M%p')
    quest['creator'] = message.author.id
    quest['members'] = []
    
    oldCounter = await questDB.find_one({'_id': 'counter'}) #gets the counter document from the database
    newCounter = {'_id': 'counter', 'quests': oldCounter['quests']+1}
    quest['_id'] = 'quest%s' % str(newCounter['quests'])
    
    await questDB.replace_one({'_id': 'counter'}, newCounter) # replaces the counter document in the database with the new one (basically just a +1 to the quest counter)
    await questDB.insert_one(quest) # inserts the current quest into the quest collection
    
    #creating the embed for the quest message
    questResponse = discord.Embed(title= quest['title'], description= quest['_id'])
    questResponse.add_field(name= 'Creator', value=message.author.mention)
    questResponse.add_field(name= 'Scheduled For', value= quest['datetime'])
    questResponse.add_field(name= chr(173), value= chr(173))
    questResponse.add_field(name= 'Party Members', value= message.author.mention)
    questResponse.set_footer(text= 'React with a %s to join.' % checkmark)
    
    msg = await message.channel.send(embed = questResponse) #sending the message
    await msg.add_reaction(checkmark) #adding a reaction to the message


#reads commands in and directs to the correct command
async def cmd_reader(message):
    msg = message.content
    if msg.startswith('$quest '):
        questRegex = re.compile(r'("(.{1,})") ([0-1]\d\/\d{2} [0-1]\d\:\d{2})')
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
            if reaction.message.embeds[0].description.startswith('quest') and str(reaction.emoji) == checkmark and user.mention != reaction.message.embeds[0].fields[0].value:
                    party = reaction.message.embeds[0].fields[3]
                    newEmbed = reaction.message.embeds[0].set_field_at(3, name=party.name, value=party.value+' '+user.mention)
                    await reaction.message.edit(embed = newEmbed)
                    questDoc = await questDB.find_one({'_id': reaction.message.embeds[0].description})
                    questDoc['members'].append(user.id)
                    await questDB.replace_one({'_id': reaction.message.embeds[0].description}, questDoc)

botClient.run(bot_token)