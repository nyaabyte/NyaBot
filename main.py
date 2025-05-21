import discord
from discord.ext import commands
import dotenv

intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content

class MyBot(commands.Bot):
  async def setup_hook(self):
    # Sync commands here, before on_ready is called
    synced = await self.tree.sync()
    print(f"Synced {len(synced)} commands")
    await self.tree.sync(guild=discord.Object(id=1374118081009553509)) # update commands in nyabyte
    print("Synced commands with guild")

bot = MyBot(command_prefix="!", intents=intents)

#things

# update status
def update_status(bot, statusId):
  if statusId == 1:
    return discord.Activity(
      name="over NyaByte",
      type=discord.ActivityType.watching
    )
  return discord.Game(
    name="Invalid status ID"
  )

async def handle_horny_points(message, user_id, points):
    # Check if the user is already in the database
    new_points = 0
    with open("horny_points.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith(str(user_id)):
                # User found, update points
                current_points = int(line.split(",")[1].split("#")[0])
                new_points = current_points + points
                lines[lines.index(line)] = f"{user_id},{new_points}#{message.author.display_name}\n"
                break
        else:
            # User not found, add them to the database
            lines.append(f"{user_id},{points}#{message.author.display_name}\n")
            new_points = points

    # Write the updated data back to the file
    with open("horny_points.txt", "w") as f:
        f.writelines(lines)
    
    # send the message
    embed = discord.Embed(
        title="Horny Points",
        description=f"{message.author.display_name}, you have been given {points} horny points.\nYou now have {new_points} horny points.",
        color=discord.Color.red()
    )
    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
    embed.set_footer(text="This action was performed automatically.")
    await message.channel.send(embed=embed, delete_after=10)

async def horny_filter(message, manual=False):
    filter_words = open("filter_words.txt").read().splitlines()
    if any(word in message.content.lower() for word in filter_words) or manual:
        # check if word is not a part of another word
        if not manual:
            for word in filter_words:
                if word in message.content.lower():
                    # check if the word is not part of another word
                    if message.content.lower().count(word) == 1:
                        # check if the word is not part of another word
                        if message.content.lower().index(word) == 0 or message.content.lower()[message.content.lower().index(word) - 1] == " ":
                            break
            else:
                return
        await message.delete()
        # send a fancy embed
        embed = discord.Embed(
            title="Filtered word detected!",
            description=f"{message.author.display_name}, your message was deleted because it contained a filtered word.\nPlease refrain from using this word again in the future.\nFor more information, please look at the spoilered words in the message below.",
            color=discord.Color.red()
        )
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        # generate the original message but with filtered words in a spoiler
        filtered_message = message.content
        if not manual:
            for word in filter_words:
                filtered_message = filtered_message.replace(word, f"||{word}||")
        else:
            filtered_message = "||" + filtered_message + "||"
        embed.add_field(name="Original message", value=filtered_message, inline=False)
        if manual:
            embed.set_footer(text="This action was performed manually.")
        else:
            embed.set_footer(text="This action was performed automatically.")
        await message.channel.send(message.author.mention, embed=embed, delete_after=10)
        # add point to horny point db
        infraction_count = 0
        # count amount of banned words
        for word in filter_words:
            infraction_count += message.content.lower().count(word)
            # check if the word is not part of another word
            if message.content.lower().count(word) == 1:
                # check if the word is not part of another word
                if message.content.lower().index(word) == 0 or message.content.lower()[message.content.lower().index(word) - 1] == " ":
                    break
            else:
                return
        
        if manual:
            infraction_count = 1
        await handle_horny_points(message, message.author.id, infraction_count)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=update_status(bot, 1))
    print("Bot is ready!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # process word filter
    await horny_filter(message)
    await bot.process_commands(message)

@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="hornyboard", description="Shows the horny points leaderboard from least to most")
async def hornyboard(interaction: discord.Interaction):
    with open("horny_points.txt", "r") as f:
        lines = f.readlines()
        lines.sort(key=lambda x: int(x.split(",")[1].split("#")[0]))
        embed = discord.Embed(
            title="Horny Points Leaderboard",
            description="Here are the top 10 users with the least horny points:",
            color=discord.Color.red()
        )
        for line in lines[:10]:
            user_id, points = line.split(",")
            user_id = int(user_id)
            points = int(points.split("#")[0])
            user = await bot.fetch_user(user_id)
            embed.add_field(name=line.split("#")[1], value=f"{points} points", inline=False)
        # embed.set_footer(text="This action was performed automatically.")
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="horny", description="Deletes a horny message and gives the poster a warning")
async def horny(interaction: discord.Interaction, message_url: str):
    # Get the message ID from the URL
    message_id = int(message_url.split("/")[-1])
    channel_id = int(message_url.split("/")[-2])
    channel = bot.get_channel(channel_id)
    if channel is None:
        await interaction.response.send_message("Channel not found.", delete_after=3)
        return
    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        await interaction.response.send_message("Message not found.", delete_after=3)
        return

    await horny_filter(message, manual=True)
    await handle_horny_points(message, message.author.id, 1)
    await interaction.response.send_message("Message deleted and user warned.", delete_after=3)

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run(dotenv.get_key('.env', 'DISCORD_TOKEN'))