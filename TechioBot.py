import discord
import time
import json
import requests
import re
import asyncio
import praw
import random
import wikipedia
import whapi
from pprint import pprint
from pylatexenc.latex2text import LatexNodes2Text
# new, also install lxml just in case
import urllib.parse, urllib.request
from urllib.parse import urlparse, parse_qs

# all IDs and api_keys have been redacted
client = discord.Client()
discordKey = ''
triviaAPIurl = ''

redSecret = ''
redID = ''
reddit = praw.Reddit(client_id=redID, client_secret=redSecret, user_agent='')

tenor_api_key = ''


def trivStringCorrection(text):
    text = text.replace('&quot;', '"')
    text = text.replace("&#039;", "'")
    text = text.replace("&ldquo;", '“')
    text = text.replace("&rdquo;", '”')
    text = text.replace("&euml;","ë")
    return text

def getQuestion():
    trivia = requests.get(triviaAPIurl)
    result = json.loads(trivia.text)
    if result["response_code"] == 0:
        data = result["results"][0]
        question = data["question"]
        # Replace ASCII codes to proper symbols
        question = trivStringCorrection(question)

        type = data["type"]
        # correct answer
        correct = data["correct_answer"]
        correct = trivStringCorrection(correct)
        
        # list of incorrect answers
        incorrect = data["incorrect_answers"]
        
        # choices of answers
        incorrect.append(correct) # also add the correct answer to the choice list
        
        # Convert all choices to string
        choicesList = ' | '.join([str(item) for item in incorrect])        
        choicesList = trivStringCorrection(choicesList)

        if type == "boolean":
            question = 'True or False?\n' + question
        # Add choices string to question when necessary
        else:
            question = question + "\n" + choicesList 

        return [question, correct]
    else:
        return ["Couldn't find a question. ", "Try again!"]

def filterOnlyBots(member):
    return member.bot

def countUserMembers(message):
    membersInServer = message.guild.members
    # Filter to the list, returns a list of bot-members
    botsInServer = list(filter(filterOnlyBots, membersInServer))
    botsInServerCount = len(botsInServer)
    # (Total Member count - bot count) = Total user count
    return message.guild.member_count - botsInServerCount

def getMeme():
    memes = []
    subr = random.choice(['dankmemes', 'memes'])
    for subm in reddit.subreddit(subr).random_rising(limit=10):
        memes.append(subm)
    return memes

def getTwoSentence():
    horror = []
    for subm in reddit.subreddit("TwoSentenceHorror").random_rising(limit=10):
        horror.append(subm)
    return horror

def dadJoke():
    jokes = []
    for subm in reddit.subreddit("dadjokes").random_rising(limit=10):
        jokes.append(subm)
    return jokes

def getGif(query):
    r = requests.get("https://api.tenor.com/v1/search?q=%s&key=%s&limit=%s" % (query, tenor_api_key, 4))
    if r.status_code == 200:
        top_3gifs = json.loads(r.content)
    else:
        top_3gifs = None

    return top_3gifs['results'][random.randint(0,3)]['media'][0]['gif']['url']

def getTip():
    tips = []
    for subm in reddit.subreddit("lifeprotips").random_rising(limit=10):
        tips.append(subm)
    return tips

def getTitle(videoID):
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % videoID}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data["title"]

channel = []

@client.event
async def on_ready():
    print(f"The bot {client.user.name} is ready!")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Avengers: Endgame"))

@client.event
async def on_message(message):
    global channel
    if message.author == client.user:
        if "Poll:" in message.content:
            await message.add_reaction("✅")
            await message.add_reaction("❎")
            return
        else:
            return
    #if running:
    if message.channel in channel:
        return

    # Vote system
    if re.findall("^!vote( )?", message.content.lower()):
        count = 0
        args = message.content.lower().split(" ")
        if len(args) == 1:
            embedMessage = discord.Embed(title='Initate Poll', description="To start a simple poll, type '!vote QUESTION/STATEMENT'", color=0xFFC300)
            await message.channel.send(embed=embedMessage)
        else:
            args.remove("!vote")
            title= "Poll: **" + (" ".join(args)) + "**"
            vote_msg = await message.channel.send(f"{title}")
            await message.delete()
            await asyncio.sleep(30)
            vote_msg = await vote_msg.channel.fetch_message(vote_msg.id) # refetch message
            # default values
            positive = 0
            negative = 0
            for reaction in vote_msg.reactions:
                if reaction.emoji == '✅':
                    positive = reaction.count - 1 # compensate for the bot adding the first reaction
                if reaction.emoji == '❎':
                    negative = reaction.count - 1
            count = countUserMembers(message)
            await message.channel.send(f'Results: {round((positive/count)*100, 1)}% agree and {round((negative/count)*100, 1)}% disagree')
    
    # Hello
    elif re.findall("^!( )?hi((ya)?)$", message.content.lower()) or re.findall("^!( )?(h?)ello", message.content.lower()) or re.findall("^!.*hey(a?)$", message.content.lower()):
        await message.channel.send(f"Hi there, {message.author.name}!")
    
    elif re.findall("^!.*h(o)?w.*u( )?[?]?$", message.content.lower()):
        await message.channel.send(f"I'm fine {message.author.name}, thanks for asking!")

    # Help commands
    elif re.search("^!help$", message.content.lower()) or re.search("^!.*techio$", message.content.lower()):
        await message.channel.send(f"Hey {message.author.name}, my current commands are:\n1. Hello\n2. Favorite person?\n3. Friends?\n4. Member list\n5. Trivia Question\n6. Vote [Question]\n7. Meme\n8. Dad Jokes\n9. Two Sentence Horror\n10. Wiki [Query]\n11. WHow [Query]\n12. Life Pro Tips\n13. Guessing Game\n14. Text Game\n15. YouTube\n16. Connect/Disconnect voice channel [BETA]")

    # Favorite person
    elif re.findall("^!fav(o(u?)rite)?( )?(person)?[?]?$", message.content.lower()):
        await message.channel.send("No one has currently impressed me more than my creator!")

    # Friends
    elif re.findall("^!fri(e?)nd(s?)( )?[?]?", message.content.lower()):
        await message.channel.send(f"My good friend is Tobias right now!\n ... and you too, {message.author.name}")

    # Member list
    elif re.findall("^!me(m?)ber(s?)( )?(list)?[?]?$", message.content.lower()):
        count = 0
        await message.channel.send(f"Working on it... give me one second!")
        nameString = ''
        for name in message.guild.members:
            nameString += name.name + ', '
            count += 1
        await message.channel.send(nameString)
        await message.channel.send(f"Number of members: {count}")
    
    # Trivia questions
    elif re.findall("^!triv(ia)?( )?(q(uestio)?n)?[?]?$", message.content.lower()) or re.findall("^!.*question(s)?$", message.content.lower()):
        question = getQuestion()
        await message.channel.send(embed=discord.Embed(title=f'Question: {question[0]}',color=0x0000FF))
        #await message.channel.send(f'Question: {question[0]}')
        await asyncio.sleep(3)
        await message.channel.send(f'Answer: {question[1]}')

    # Good bot
    elif re.findall("^!.*(go(o?)d|nice)( )?bot(s?)[!]?$", message.content.lower()):
        await message.channel.send(f"Thank you {message.author.name}!")
    
    # Good night
    elif re.findall("^!(a( )?)?good( )?night(y?)[!]?$", message.content.lower()):
        await message.channel.send(f"A very good night to you too, {message.author.name}!")

    # Meme
    elif re.findall("^!( )?meme(s)?$", message.content.lower()):
        meme = getMeme()
        randomSub = random.choice(meme)
        name = randomSub.title
        url = randomSub.url

        em = discord.Embed(title=name,description=f"\n👍 {randomSub.score} | 💬 {randomSub.num_comments}",color=0xFFFFFF)
        em.set_image(url=url)   
        await message.channel.send(embed=em)

    # Dad joke
    elif re.findall("^!( )?(dad( )?)?joke(s)?( )?$", message.content.lower()):
        joke = dadJoke()
        randomSub = random.choice(joke)
        name = randomSub.title
        text = randomSub.selftext + f'\n👍 {randomSub.score} | 💬 {randomSub.num_comments}'

        em = discord.Embed(title=name,description=text,color=0xFFC300)
        await message.channel.send(embed=em)

    # Two Sentence Horror
    elif re.findall("^!( )?two( )?sentence( )?(horror)?( )?$", message.content.lower()):
        horror = getTwoSentence()
        randomSub = random.choice(horror)
        name = randomSub.title
        text = randomSub.selftext + f'\n👍 {randomSub.score} | 💬 {randomSub.num_comments}'

        em = discord.Embed(title=name,description=text,color=0xFF0000)
        await message.channel.send(embed=em)

    # Gif
    elif re.findall("^!gif .*$", message.content.lower()):
        print("Gif query is running")
        words = message.content.lower().split()
        words.remove("!gif")
        query = " ".join(words)
        print("Query formed")
        try:
            print("trying to get Gif...")
            theGif = getGif(query)
            print(theGif)
            await message.channel.send(theGif)
        except Exception as error:
            print("Gif 1 error:", error)


    # Wikipedia
    elif re.findall("^!wiki.*$", message.content.lower()):
        words = message.content.lower().split()
        words.remove("!wiki")
        query = " ".join(words)

        try:
            em = discord.Embed(title=wikipedia.page(query).title,description=LatexNodes2Text().latex_to_text(wikipedia.summary(query, sentences=3)),color=0xFFA500)
            await message.channel.send(embed=em)
        except:
            await message.channel.send(embed=discord.Embed(title="Hit a dead end!",description="Can't find what you're looking for, maybe try giving specifics in a bracket, e.g. Discord (software)",color=0xFFA500))
            await message.channel.send(f"Suggestions: {wikipedia.suggest(query)}")

    # Wikihow
    elif re.findall("^!whow.*$", message.content.lower()):
        words = message.content.lower().split()
        words.remove("!whow")
        query = " ".join(words)

        
        try:
            # Get article ID of the first search result
            article_id = whapi.search(query)[0]['article_id']
            # Get title of first search result by returning details of the article ID
            title = whapi.return_details(article_id)['title']
            # Get steps
            steps_raw = whapi.parse_steps(article_id)
            await message.channel.send(f"**{title}**")
            for step in steps_raw:
                if steps_raw[step]["description"] == '':
                    steps_raw[step]["description"] = ' '
                em = discord.Embed(title=f"**{(step.replace('_',' ')).upper()} : {steps_raw[step]['summary']}**",description=steps_raw[step]["description"],color=0x00B2EE)
                await message.channel.send(embed=em)
        except:
            await message.channel.send(embed=discord.Embed(title="Hit a dead end!",description="Can't find what you're looking for, maybe try being more specific",color=0xFFA500))

    # Life pro tip
    elif re.findall("^!( )?(life(pro)?)?tip(s)?( )?$", message.content.lower()) or re.findall("^!( )?lpt$", message.content.lower()):
        tips = getTip()
        randomSub = random.choice(tips)
        name = randomSub.title
        text = randomSub.selftext + f'\n👍 {randomSub.score} | 💬 {randomSub.num_comments}'
        em = discord.Embed(title=name,description=text,color=0x90EE90)
        await message.channel.send(embed=em)

    # Youtube
    elif re.findall("^!( )?youtube( )?$", message.content.lower()) or re.findall("^!( )?yt( )?$", message.content.lower()):
        
        def check2(author):
            '''Check if the message is from the same author and see if it can be converted into a string'''
            def inner_check(message):
                if message.author != author:
                    return False
                try:
                    str(message.content)
                    return True
                except ValueError:
                    return False
            return inner_check
        
        await message.channel.send("What do you want to search?")
        search = await client.wait_for('message', check=check2(message.author), timeout=20)
        try:
            search_query = urllib.parse.urlencode({
                "search_query": search.content
            })
            print("Search query:\n",search_query)
            html_content = urllib.request.urlopen(
                f"http://www.youtube.com/results?" + search_query
                )
            # using regular expressions to get Video IDs of different videos
            search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())

            print("Search Results:",search_results)
            # GET TITLE
            title = getTitle(search_results[0])
            
            await message.channel.send(f"TOP RESULT: **{title}**")
            await message.channel.send("https://www.youtube.com/watch?v=" + search_results[0])
            more_titles = "MORE RESULTS:\n"
            for i in range(1,4):
                more_titles += f"{i}. **{getTitle(search_results[i])}**\n"
            else: # else statement executed when for loop completely finished
                await message.channel.send(more_titles)
        except Exception as e:
            await message.channel.send(f"Sorry, something went wrong!")
            print(e)

    elif re.findall("^!( )?co((n)?nec(t)?)?$", message.content.lower()):
        try:
            vc_channel = message.author.voice.channel
            await vc_channel.connect()
        except Exception as e:
            print("Error:",e)
    
    elif re.findall("^!( )?disc(on(n)?ect)?( )?$", message.content.lower()):
        try:
            vc_channel = message.guild.voice_client
            if vc_channel:
                await vc_channel.disconnect()
            else:
                print("No channel found")
        except Exception as e:
            print("Error:",e)
        
    # Google search
    elif re.findall("^!search.*$", message.content.lower()):
        try:
            search_query = message.content.split()
            search_query.remove("!search")
            search_query = " ".join(search_query)
            print(search_query)
            search = google_search(search_query, google_api, search_id)
            pprint(search)
            # parsing JSON response -> getting title and description (snippet`)
            await message.channel.send(f'**{search["items"][0]["title"]}**: {search["items"][0]["snippet"]}')
            await message.channel.send(search["items"][0]["pagemap"]["metatags"][0]["og:image"])
        except Exception as e:
            print("Error:", e)

    # Guess game
    elif re.findall("^!( )?guess(ing)?( )?(gam(e)?)?( )?$", message.content.lower()):
        number = random.randint(1,10)
        guess = 3

        def check(author):
            def inner_check(message): 
                if message.author != author:
                    return False
                try: 
                    int(message.content) 
                    return True 
                except ValueError: 
                    return False
            return inner_check

        await message.channel.send("Pick a number between 1 and 10")
        while True:
            if guess == 0:
                    await message.channel.send(f"Sorry, you're out of guesses! The answer was {number}")
                    break
            try:
                msg = await client.wait_for('message', check=check(message.author), timeout=5)
                attempt = int(msg.content)
                
                if attempt > number:
                    guess -= 1
                    await message.channel.send(str(guess) + ' guesses left, try going lower!')
                    await asyncio.sleep(1)
                elif attempt < number:
                    guess -=1
                    await message.channel.send(str(guess) + ' guesses left, try going higher!')
                    await asyncio.sleep(1)
                elif attempt == number:
                    await message.channel.send('You guessed it! Good job!')
                    break
            except asyncio.TimeoutError:
                await message.channel.send("Oh you took too long to guess, sorry!")
                break
    
    # TO DO:
    # Add music to voice channel when playing for action feeling.
    # Lightning strike (which acts like poison giving extra damage) for three to four turns
    
    # Save scores for competitive PVP

    elif re.findall("^!( )?game( )?$", message.content.lower()) and message.channel not in channel:
        channel.append(message.channel)
        def check(author):
            '''Check if the message is from the same author and see if it can be converted into an integer'''
            def inner_check(message): 
                if message.author != author:
                    return False
                try: 
                    int(message.content) 
                    return True 
                except ValueError: 
                    return False
            return inner_check
        
        def check2(author):
            '''Check if the message is from the same author and see if it can be converted into a string'''
            def inner_check(message):
                if message.author != author:
                    return False
                try:
                    str(message.content)
                    return True
                except ValueError:
                    return False
            return inner_check

        try:
            enemies = {"Skeleton": 100, "Outrider": 150, "Clown": 120, "Bossy": 175, "Ethias-Tahten": 190}
            enemies_damages = {"Skeleton": 26, "Outrider": 32, "Clown": 46, "Bossy": 52, "Ethias-Tahten": 74, "Titan": 164, "Proxima Midnight": 200}
            score = 0
            max_heal = 45
            heals = 3
            gear_attack = 0
            gear_defense = 0
            gear_chance = 0
            enemy_dropchance = 35
            absorb_chance = 25
            crit_chance = 20
            crit_gunchance = 37
            crit_infinitychance = 50
            bullets = 6
            stones = 3 
            enemy, enemy_health = random.choice(list(enemies.items()))
            startword = "An" if enemy.startswith(('A','E','I','O','U')) else "A"
            await message.channel.send(f"{startword} **{enemy}** has appeared!")
            bullets = 8
            player_health = 250
            blocked = False
            shield_multiplier_active = False
            titan_absorbed = False
            refuelled = False
            gear_active = False
            will_power = 0
            healed = False

            while True:
                try:
                    await message.channel.send("```Choose your move: 1. Attack ⚔️ 2. Heal 🧪 3. Give Up!```")
                    msg = await client.wait_for('message', check=check(message.author), timeout=13)
                    move = int(msg.content)
                    ## ATTACK

                    if move == 1:
                        # Weapon
                        await message.channel.send(f"```Choose your weapon: 1. Sword 🗡️ 2. Gun  ̿̿/̵͇̿̿/’̿’̿ ̿ ̿̿ ̿̿ ̿̿  3. CA Shield 🔴 4. Infinity Stone 💎\nA-{gear_attack},C-{gear_chance},D-{gear_defense}```")
                        msg = await client.wait_for('message', check=check(message.author), timeout=13)
                        atk_move = int(msg.content)
                        if atk_move == 1:
                            # attack by sword - 13 to 38
                            damage = random.randint(27, 38) + (gear_attack)
                            
                        elif atk_move == 2:
                            # attack by gun
                            if bullets >= 0:
                                damage = random.randint(44, 51) + (gear_attack)
                                bullets -= 1
                                # check for critical qte chance
                                chance = random.randint(0, 100)
                                print("gun crit chance:", chance)
                                if chance < crit_gunchance + gear_chance:
                                    number = random.randint(10, 999)
                                    try:
                                        await message.channel.send(f"```Double-tap critical shot: {number}```")
                                        msg = await client.wait_for('message', check=check(message.author),timeout=3)
                                        attempt = int(msg.content)
                                        if attempt == number:
                                            chance = round(random.uniform(1.3, 1.75), 2)
                                            damage *= chance
                                            await message.channel.send(f"You double-tapped {enemy}  ̿̿/̵͇̿̿/’̿’̿ ̿ ̿̿ ̿̿ ̿̿ in the head for a **{chance} DMG multiplier!**")
                                            await message.channel.send("https://tenor.com/view/shoot-la-r%c3%a9volution-the-french-revolution-fire-aim-gif-18505734")
                                        else:
                                            await message.channel.send("You _messed up_ the double-tap shot!")
                                    except asyncio.TimeoutError:
                                        await message.channel.send("You _missed_ the double-tap!")
                            else:
                                await message.channel.send("No more bullets left")
                                damage = 0
                        # attack by CA shield
                        elif atk_move == 3:
                            await message.channel.send("```Choose sub-shield move: 1. Block  2. Throw```")
                            msg = await client.wait_for('message', check=check(message.author), timeout=13)
                            sub_shield_move = int(msg.content)
                            if sub_shield_move == 1:
                                damage = 0
                                blocked = True
                                chance = random.randint(0,100)
                                # Chance to double damage with shield throw
                                print("chance:",chance,"absorbchance:",absorb_chance + gear_chance + ((enemies_damages[enemy])/2))
                                if chance < absorb_chance + gear_chance + ((enemies_damages[enemy])/2):
                                    shield_multiplier_active = True 
                            elif sub_shield_move == 2:
                                if shield_multiplier_active==True:
                                    damage = random.randint(38,43) * 3 + (gear_attack)
                                    shield_multiplier_active = False
                                else:
                                    damage = random.randint(38,43) + (gear_attack)
                                
                                # critical strike with shield throw
                                chance = random.randint(0, 100)
                                # check for critical qte chance
                                if chance < crit_chance + gear_chance:
                                    for i in range(4):
                                        number = random.randint(10, 999)
                                        try:
                                            await message.channel.send(f"```Critical strike: {number}```")
                                            msg = await client.wait_for('message', check=check(message.author),timeout=3)
                                            attempt = int(msg.content)
                                            if attempt == number:
                                                startword2 = "Double-striked! " if i == 1 else "Triple-striked! " if i == 2 else "**Quadruple striked!!** " if i == 3 else "" 
                                                endword = "a " if i == 0 else "more " if i == 1 else "even more " if i == 2 else "_EVEN MORE_ "
                                                chance = round(random.uniform(1.01, 1.50),2)
                                                await message.channel.send(startword2 + f"You **critical striked** _{enemy}_ with " + endword + f"{chance} DMG multiplier!🔥")
                                                if i==2:
                                                    await message.channel.send("https://tenor.com/view/captain-america-avengers-endgame-avengers-endgame-mjolnir-gif-14666655")
                                                damage *= chance

                                            else:
                                                await message.channel.send(f"Argh, you _messed up_ the last strike!")
                                                break
                                        except asyncio.TimeoutError:
                                            await message.channel.send("You _missed_ the last strike chance!")
                                            break
                                        # resetting
                                        chance = random.randint(0, 100)
                                        print(f"shield chance{i+1}:",chance)
                                        if chance < crit_chance + (i * 2) + gear_chance:
                                            continue
                                        else:
                                            break
                            else:
                                await message.channel.send("-. _ .- /  What are you doing??")
                                damage = 0
                        # attack by infinity stone
                        elif atk_move == 4:               
                            if stones > 0:
                                damage = random.randint(95, 99) + (gear_attack) #95 - 99
                                # don't start qte-s if damage is high
                                if damage < enemy_health:
                                    if enemy == "Titan":
                                        chance = random.randint(0, 100)
                                        if chance < crit_infinitychance + gear_chance:
                                            await message.channel.send(f"There's a chance for absorbing his life force!")
                                            success = 0
                                            for i in range(0, 4):
                                                number = random.randint(10, 999)
                                                startword2 = "keep going!! A" if i > 0 else "A"
                                                await message.channel.send(f"```{startword2}bsorb partial life force! {number}```")
                                                try:
                                                    msg = await client.wait_for('message', check=check(message.author), timeout=3)
                                                    attempt = int(msg.content)
                                                    if attempt == number:
                                                        damage += 50
                                                        success += 1
                                                        titan_absorbed = True if success >= 3 else False
                                                        continue
                                                    else:
                                                        await message.channel.send(f"Noo you _messed up_!")
                                                        break
                                                except asyncio.TimeoutError:
                                                    await message.channel.send(f"Noo you _missed_!")
                                                    break
                                stones -= 1
                            else:
                                await message.channel.send("No infinity stones available!!")
                                damage = 0
                        else:
                            await message.channel.send("-. _ .- /  What are you doing??")
                            damage = 0
                        
                        score_multiplier = score//10 if score > 19 else 1.5 if score > 9 else 1
                        print("Raw damage:", damage - gear_attack)
                        print("Gear attack damage:", damage)
                        damage *= score_multiplier
                        print("Modified damage:", damage)
                        


                        ## WHEN MOVE IS CHOSEN (APPLYING DAMAGE AND OTHER THINGS)
                        enemy_health -= round(damage,2)
                        additional_op = " with kinetic energy absorbed into the shield" if shield_multiplier_active==True else ""
                        output_message = f"_{message.author.name}_ dealt **{round(damage,2)} DMG** to _{enemy}_" if blocked==False else f"_{message.author.name}_ used CA Shield to block" + additional_op + "!"
                        await message.channel.send(output_message)
                        
                        # this chance is for choosing GIFs
                        chance = random.randint(0,3)
                        if blocked:
                            shield_gif = "https://tenor.com/view/captain-america-block-shield-punch-winter-soldier-gif-4489434" if chance < 3 else "https://tenor.com/view/wonder-woman-wonder-woman-movie-shield-gal-gadot-blocking-gif-5717903"
                            await message.channel.send(shield_gif)
                        elif atk_move == 3 and sub_shield_move == 2:
                            shield_attack_gif = "https://tenor.com/view/throwing-shield-captain-america-chris-evans-the-avengers-gif-10638908" if chance < 2 else "https://tenor.com/view/captain-america-gif-14090424"
                            await message.channel.send(shield_attack_gif)
                        elif atk_move == 1:
                            await message.channel.send("https://tenor.com/view/akame-akame-ga-kill-anime-sword-slash-gif-17468655")
                        elif atk_move == 4:
                            await message.channel.send("https://tenor.com/view/snap-marvel-thanos-gauntlet-gif-13267601")

                    ## HEAL
                    elif move == 2:
                        if heals > 0:
                            health_increase = random.randint(max_heal - 5, max_heal) + gear_defense
                            player_health += health_increase
                            healed = True
                            heals -= 1
                            await message.channel.send(f"Health increased by **{health_increase}**.")
                            damage = 0
                        else:
                            await message.channel.send("No more health potions left!")
                            healed = False
                    # Quit
                    elif move == 3:
                        await message.channel.send(f"_{message.author.name}_ decided to give up.")
                        break
                    # Invalid option
                    else:
                        await message.channel.send("-. _ .- /  What are you doing??")
                    # If enemy killed
                    if enemy_health <= 0:
                        if enemy == "Titan":
                            await message.channel.send("**Titan**: Ahh... (coughs)... you mortal!")
                            await asyncio.sleep(1)
                            await message.channel.send("**Titan**: How did you defeat me?!")
                            await asyncio.sleep(1)
                            await message.channel.send(f"```1. 'You are just pathetic!' 2. 'I don't know, but you fought well, Titan.' 3. Walk away.```")
                            try:
                                msg = await client.wait_for('message', check=check(message.author), timeout=5)
                                attempt = int(msg.content)
                            except asyncio.TimeoutError:
                                attempt = 3
                            if attempt == 1 and refuelled == False:
                                await message.channel.send("**Titan**: ARGH! You dare speak to me like that, mortal?!")
                                await asyncio.sleep(1)
                                await message.channel.send("The Titan replenishes his health, fuelled by his rage. Absorbing his rage, you, too, have refilled your health.")
                                player_health += 250 + gear_defense
                                enemy_health = enemies["Titan"]
                                refuelled = True
                                continue
                            elif attempt == 2:
                                await message.channel.send("**Titan**: Mortal, you... you have my respect.\nYou shall have my equipment")
                                await message.channel.send(f"```Choose a gear piece: 1. Damage Increase Gear 2. Chance Increase Gear 3. Defense Increase Gear```")
                                msg = await client.wait_for('message', check=check(message.author), timeout=13)
                                choice = int(msg.content)
                                if choice == 1:
                                    gear_attack += 15
                                    await message.channel.send("_Base damage_ increased")
                                elif choice == 2:
                                    gear_chance += 15
                                    await message.channel.send("_Chances_ increased")
                                elif choice == 3:
                                    gear_defense += 35
                                    await message.channel.send("_Defense_ increased")
                                else:
                                        await message.channel.send("No gear piece chosen")
                            elif attempt == 3:
                                await message.channel.send("You defeated the Titan and walked away, greatly increasing your willpower.")
                                will_power += 20
                                score += 2
                                await message.channel.send(f"```So you killed a mf'ing {enemy}, well done!\nScore: {score}```")
                                refuelled = False
                            else:
                                await message.channel.send(f"You showed the Titan his place! Score significantly increased!")
                                score += 4
                                await message.channel.send(f"```So you killed a mf'ing {enemy}, well done!\nScore: {score}```")
                                refuelled = False
                        elif enemy == "Proxima Midnight":
                            await message.channel.send("**Midnight**: You will pay for this with your life.")
                            await asyncio.sleep(1)
                            await message.channel.send("She teleports away to safety, not accepting defeat and swearing to destroy you later!")
                            await asyncio.sleep(1.1)
        
                        else:
                            score += 1
                            await message.channel.send(f"```You killed the {enemy}, well done!\nScore: {score}```")
                            
                            ## GEAR PIECE AFTER KILLING ENEMY
                            # chance to get gear piece
                            chance = random.randint(0, 100)
                            # extra chance if you don't have a gear_piece
                            chance -= 25 if gear_active == False else 0
                            if chance < enemy_dropchance + gear_chance:
                                await asyncio.sleep(1)
                                await message.channel.send(f"```The enemy dropped gear! Choose a gear piece: 1. Damage Increase Gear 2. Chance Increase Gear 3. Defense Increase Gear```")
                                msg = await client.wait_for('message', check=check(message.author), timeout=13)
                                choice = int(msg.content)
                                if choice == 1:
                                    gear_attack += 10
                                    await message.channel.send("_Base damage_ increased")
                                    gear_active = True
                                elif choice == 2:
                                    gear_chance += 10
                                    await message.channel.send("_Chances_ increased")
                                    gear_active = True
                                elif choice == 3:
                                    gear_defense += 10
                                    await message.channel.send("_Defense_ increased")
                                    gear_active = True
                                else:
                                    await message.channel.send("No gear piece chosen")

                        ## HEALTH ABSORB AFTER KILLING ENEMY
                        health_increase = round(random.randint(max_heal - 10, max_heal + 10) + ((enemies_damages[enemy])/2.5),2)
                        player_health += health_increase + gear_defense
                        bullets += 2
                        word2 = "residual energy force" if enemy == "Proxima Midnight" else "life force"
                        await message.channel.send(f"You gained _{enemy}'s_ {word2}! Health increased by **{health_increase}**. | Bullets regained to: {bullets}")
                        will_power += 50 if enemy == "Proxima Midnight" else 45 if enemy == "Titan" else 10
                        print(f"{enemy} and willpower increased to {will_power}")

                        ## RESETTING VALUES
                        chance = random.randint(0,100)
                        # chance to get heals
                        chance += 100 if enemy == "Titan" else 0
                        if chance < enemy_dropchance + gear_chance:
                            await message.channel.send(f" -> {enemy} also dropped a health potion 🧪! <-")
                            heals += 1
                        # chance to get infinity stone
                        if chance < (enemy_dropchance-10) + gear_chance:
                            await message.channel.send(f" --> The enemy was also hiding an infinity stone 💎! It belongs to you now, {message.author.name}! <--\n")
                            stones += 1
                            
                        await asyncio.sleep(0.75)
                        await message.channel.send("\n_You are continuing on your journey and..._")
                        ## RESTARTING LOOP
                        await asyncio.sleep(1.5)
                        if score >= 10: #score should be above 10 for titan
                            enemies.update({"Titan":750})
                        if score >= 15:
                            enemies.update({"Proxima Midnight":1000})
                        enemy, enemy_health = random.choice(list(enemies.items()))
                        enemy_health += score
                        startword = "An" if enemy.startswith(('A','E','I','O','U')) else "Oh, by the Gods! A" if enemy.startswith('T') else "OH NO! Black Order's" if enemy == "Proxima Midnight" else "A"
                        await message.channel.send(f"{startword} **{enemy}** has appeared!")
                        if enemy == "Proxima Midnight":
                            await message.channel.send("https://imgur.com/6Fj3QK4")
                        await asyncio.sleep(1)
                        continue

                    ## AFTER CHOOSING A MOVE
                    await asyncio.sleep(1)
                    ## ENEMY MOVE

                    ## PROXIMA QTE's
                    if enemy == "Proxima Midnight":
                        if move != 2:
                            enemy_damage = random.randint(enemies_damages[enemy] - 10, enemies_damages[enemy]) + (score * 1.01) - gear_defense
                            if enemy_health > 0:
                                if blocked == False:
                                    await message.channel.send("Midnight is engaging in quick ATOMIC-SPLICE slashes!")
                
                                    for i in range(0,7): #0 - 7
                                        # this chance is for qte-s for Proxima
                                        chance = random.randint(0,1)
                                        weap = random.choice(["sword","shield","stone","phase","invulnerable","kameha","dash","energy","nuclear"]) if chance == 1 else random.randint(0, 999)
                                        await message.channel.send(f"```Counter-move: {weap}```")
                                        try:
                                            if chance == 1:
                                                msg = await client.wait_for('message', check=check2(message.author), timeout=3)
                                                attempt = str(msg.content)
                                            else:
                                                msg = await client.wait_for('message', check=check(message.author), timeout=3)
                                                attempt = int(msg.content)
                                            if attempt == weap:
                                                damage += random.randint(60, 75) + gear_attack
                                                print(damage,"to midnight")
                                            else:
                                                await message.channel.send(f"YOU MISSED! Lost **{enemy_damage} HP**!")
                                                player_health -= enemy_damage
                                        except:
                                            await message.channel.send(f"YOU MISSED! Lost **{enemy_damage} HP**!")
                                            player_health -= enemy_damage
                                    startword4 = " only" if damage < 275 else ""
                                    await message.channel.send(f"_{message.author.name}_ dealt{startword4} **{round(damage,2)} DMG** to _{enemy}_")
                                    enemy_health -= round(damage,2)
                                    if enemy_health <= 0:
                                        await message.channel.send(f"_Midnight_ takes a deep breath - in an attempt to survive another round against you, though it is certain she will not!")
                                        enemy_health = 0
                                else:
                                    await message.channel.send(f"_{enemy}_ would have dealt **{enemy_damage} DMG** if _{message.author.name}_ didn't block in time!")
                                    blocked = False
                                    if shield_multiplier_active:
                                        await asyncio.sleep(0.5)
                                        await message.channel.send(f"_{enemy}'s_ DMG has been absorbed into the shield making it ready for a powerful attack!")
                            else:
                                await message.channel.send(f"_Midnight_ takes a deep breath - in an attempt to survive another round against you, though it is certain she will not!")
                                enemy_health = 0
                        else:
                            # enemy shouldn't be able to hit player when healing
                            enemy_damage = 0
                            await message.channel.send(f"_{enemy}_ couldn't touch _{message.author.name}_ as he was protected by healing immunity for a brief second!")
                    ## any other enemy - normal mechanics
                    else:
                        enemy_move = random.randint(1, 2)
                        # enemy decides to heal
                        if enemy_move == 2 and enemy_health < 40:
                            enemy_damage = 0
                            enemy_health_gain = round( random.randint( int((enemies[enemy])/6), int((enemies[enemy])/4) ) , 2)
                            enemy_health += enemy_health_gain + (score * 1.01)
                            await message.channel.send(f"_{enemy}_ healed by **{enemy_health_gain}**!")
                        # enemy decides to attack
                        else:
                            # enemy damage assignment
                            # reducing damage of enemy by gear_defense
                            enemy_damage = random.randint((enemies_damages[enemy]) - 10, enemies_damages[enemy]) + (score * 1.01) - gear_defense
                            if enemy == "Titan" and titan_absorbed:
                                enemy_damage /= 2.2
                                titan_absorbed = False
                            if blocked==False:
                                if healed == False:
                                    # player takes damage here!
                                    player_health -= enemy_damage
                                    await message.channel.send(f"_{enemy}_ dealt **{enemy_damage} DMG** to _{message.author.name}_!")
                                else:
                                    # enemy shouldn't be able to hit player when healing
                                    await message.channel.send(f"_{enemy}_ couldn't touch _{message.author.name}_ as he was protected by healing immunity for a brief second!")
                                    healed = False
                            # if blocked
                            else:
                                await message.channel.send(f"_{enemy}_ would have dealt **{enemy_damage} DMG** if _{message.author.name}_ didn't block in time!")
                                blocked = False
                                if shield_multiplier_active:
                                    await asyncio.sleep(0.5)
                                    await message.channel.send(f"_{enemy}'s_ DMG has been absorbed into the shield making it ready for a powerful attack!")
                

                    # Death
                    if player_health <= 0:
                        await message.channel.send(f"_{message.author.name}_, your life was taken by _{enemy}_!")
                        if will_power >= 75:
                            await message.channel.send(f"```By the force of your sheer will power, you can get back up and fight to see a higher score.\n1. Revive 2. Give up```")
                            try:
                                msg = await client.wait_for('message', check=check(message.author), timeout=5)
                                choice = int(msg.content)
                                if choice == 1:
                                    player_health = 100 + gear_defense
                                    await message.channel.send("**You got back up!**")
                                    await message.channel.send("https://tenor.com/view/birl-gif-5943422")
                                    will_power -= 75
                                else:
                                    await message.channel.send("You gave up!")
                                    break
                            except asyncio.TimeoutError:
                                await message.channel.send("You took too long to respond. You have given up!")
                                break
                        else:
                            break

                    # --AFTER ENEMY HAS CHOSEN MOVE = ALL MOVES COMPLETE--
                    await asyncio.sleep(0.5)
                    await message.channel.send(f"\n_{enemy}'s_ health: {round(enemy_health,2)} | _{message.author.name}'s_ Health: {round(player_health,2)}.")
                    await asyncio.sleep(0.5)
                    await message.channel.send(f"Bullets in magazine : {bullets} | Stones available : {stones} | Health potions : {heals}")

                except asyncio.TimeoutError:
                    await message.channel.send("You took too long to respond!")
                    break
            
            await message.channel.send(f"\nGame has ended - thanks for playing, _{message.author.name}_!")
        
        except Exception as error:
            await message.channel.send("Something went wrong! This command is still in beta mode.")
            print("Error:",error)
    
        channel.remove(message.channel)


# Token
client.run(discordKey)  