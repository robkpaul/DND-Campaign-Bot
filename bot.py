from dotenv import load_dotenv
from discord.ext import commands
import discord, logging, os, datetime, motor.motor_asyncio

logging.basicConfig(level=logging.INFO)
load_dotenv()
bot_token = os.getenv('DISCORD_BOT_TOKEN')
mongo_URI = os.getenv('MONGODB_URI')

mongoClient = motor.motor_asyncio.AsyncIOMotorClient(mongo_URI, serverSelectionTimeoutMS=5000, ssl=True, ssl_cert_reqs='CERT_NONE') # Client for the Motor MongoDB
questDB = mongoClient['Modron']['Quests'] # Goes to the specific Database then Collection for this project.

botIntents = discord.Intents.default()
botIntents.members = True

bot = commands.Bot(command_prefix='.', intents=botIntents) 

checkmark = '✅' # easier to type 'checkmark' than the emoji

@bot.command()
async def ping(ctx):
    await ctx.send(f'Latency: {bot.latency}')

@bot.command()
async def quest(ctx, title, date, time):
    if ctx.author != bot.user:
        questData = {}
        questData['title'] = title
        dateTimeOf = datetime.datetime.strptime(date+time, '%m/%d%H:%M')
        dateTimeOf = dateTimeOf.replace(year=datetime.datetime.now().year)
        if dateTimeOf < datetime.datetime.now():
            dateTimeOf = dateTimeOf.replace(year=dateTimeOf.year+1)
        questData['datetime'] = dateTimeOf.strftime('%A, %m/%d/%y, %I:%M%p')
        questData['creator'] = ctx.author.id
        questData['members'] = []
        
        oldCounter = await questDB.find_one({'_id': 'counter'}) #gets the counter document from the database
        newCounter = {'_id': 'counter', 'quests': oldCounter['quests']+1}
        questData['_id'] = 'quest%s' % str(newCounter['quests'])
        
        await questDB.replace_one({'_id': 'counter'}, newCounter) # replaces the counter document in the database with the new one (basically just a +1 to the quest counter)
        await questDB.insert_one(questData) # inserts the current quest into the quest collection
        
        #creating the embed for the quest message
        questResponse = discord.Embed(title= questData['title'], description= questData['_id'])
        questResponse.add_field(name= 'Creator', value=ctx.author.mention)
        questResponse.add_field(name= 'Scheduled For', value= questData['datetime'])
        questResponse.add_field(name= chr(173), value= chr(173))
        questResponse.add_field(name= 'Party Members', value= ctx.author.mention)
        questResponse.set_footer(text= 'React with a %s to join.' % checkmark)
        
        msg = await ctx.send(embed = questResponse) #sending the message
        await msg.add_reaction(checkmark) #adding a reaction to the message

@bot.event
async def on_ready():
    logging.info('Logged in as {}'.format(bot.user))

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user and user != bot.user:
        if len(reaction.message.embeds) > 0:
            if reaction.message.embeds[0].description.startswith('quest') and str(reaction.emoji) == checkmark and user.mention != reaction.message.embeds[0].fields[0].value:
                    party = reaction.message.embeds[0].fields[3]
                    newEmbed = reaction.message.embeds[0].set_field_at(3, name=party.name, value=party.value+' '+user.mention)
                    await reaction.message.edit(embed = newEmbed)
                    questDoc = await questDB.find_one({'_id': reaction.message.embeds[0].description})
                    questDoc['members'].append(user.id)
                    await questDB.replace_one({'_id': reaction.message.embeds[0].description}, questDoc)

@bot.event
async def on_reaction_remove(reaction, user):
    if reaction.message.author == bot.user and user != bot.user:
        if len(reaction.message.embeds) > 0:
            if reaction.message.embeds[0].description.startswith('quest') and str(reaction.emoji) == checkmark and user.mention != reaction.message.embeds[0].fields[0].value:
                party = reaction.message.embeds[0].fields[3]
                if user.name == user.display_name:
                    newParty = party.value.replace('<@{}>'.format(user.id), '', 1)
                else:
                    newParty = party.value.replace('<@!{}>'.format(user.id), '', 1)
                newEmbed = reaction.message.embeds[0].set_field_at(3, name=party.name, value=newParty)
                await reaction.message.edit(embed = newEmbed)
                questDoc = await questDB.find_one({'_id': reaction.message.embeds[0].description})
                questDoc['members'].remove(user.id)
                await questDB.replace_one({'_id': reaction.message.embeds[0].description}, questDoc)


bot.run(bot_token)