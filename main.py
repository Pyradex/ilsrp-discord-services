import os
import logging
from flask import Flask
from threading import Thread
from datetime import datetime

import nextcord
from nextcord.ext import commands, tasks

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(name)s: %(message)s'))
logger.addHandler(handler)

# Flask app for UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Bot setup
intents = nextcord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(intents=intents, help_command=None)

# Channel IDs
WELCOME_CHANNEL_ID = 1471660664022896902  # 「👋」introduction
PRIMARY_CHANNEL_ID = 1471639394212515916   # 「💬」primary
MEMBERCOUNT_VC_CHANNEL_ID = 1471998856806797524

# Image URLs
WELCOME_IMAGE_URL = "https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png?ex=69a4ee16&is=69a39c96&hm=5343d64cde59d1c5993880c0e03ead46db0c0b0c68707cc59dec7230aed383ca&"
FOOTER_IMAGE_URL = "https://cdn.discordapp.com/attachments/1472412365415776306/1477490966116962344/ilsrpfooter.png?ex=69a4f430&is=69a3a2b0&hm=7559b25f424c9e122886e2d5fec1a80f91f87d678c8ae868e802f2fec96c7f1e&"

# Sidebar color
SIDEBAR_COLOR = 0x4bbfff

def get_ordinal(n):
    """Get ordinal suffix (st, nd, rd, th) for a number."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return suffix

def get_member_count(guild):
    """Get member count excluding bots."""
    return len([m for m in guild.members if not m.bot])

@bot.event
async def on_ready():
    """Bot is ready and logged in."""
    logger.info(f'Bot logged in as {bot.user}')
    # Start the member count update task
    if not membercount_task.is_running():
        membercount_task.start()
    # Do initial member count update
    await update_membercount()

@bot.event
async def on_member_join(member):
    """Handle new member joins."""
    guild = member.guild
    
    # Get member count (excluding bots)
    member_count = get_member_count(guild)
    ordinal = get_ordinal(member_count)
    
    # Welcome channel - 3 embeds (image, text, image)
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel:
        embed1 = nextcord.Embed()
        embed1.set_image(url=WELCOME_IMAGE_URL)
        
        text_content = f"# <:ILSRP:1471990869166002291> Welcome to Illinois State Roleplay.\n" \
                       f"Hello, {member.mention}!\n" \
                       f"> Welcome to Illinois State Roleplay, a ER:LC Roleplay Community based on the state of Illinois in the United States.\n" \
                       f"> Want to learn more about the server? Check out ⁠<#1471702849401393264>!\n" \
                       f"> Reading our ⁠<#1471703130587795578> is necessary to ensure that you won't be moderated for rule-breaking.\n" \
                       f"> Do you need support or have questions? Create a support ticket in ⁠<#1471666959753154646>.\n" \
                       f"> Would you like full community access? Ensure that ⁠<#1471660766536011952> is complete with Melonly.\n" \
                       f"> Interact with others in <#1471639394212515916>.\n" \
                       f"\nHave a great day!\n\n" \
                       f"You are our {member_count}{ordinal} member in the Discord Communications of Illinois State Roleplay."
        
        embed2 = nextcord.Embed(description=text_content, color=SIDEBAR_COLOR)
        
        embed3 = nextcord.Embed()
        embed3.set_image(url=FOOTER_IMAGE_URL)
        
        # Send all 3 embeds as a single message
        await welcome_channel.send(embeds=[embed1, embed2, embed3])
    
    # Primary channel welcome message
    primary_channel = bot.get_channel(PRIMARY_CHANNEL_ID)
    if primary_channel:
        welcome_message = f"Welcome to Illinois State Roleplay, {member.mention}! You are our {member_count}{ordinal} community member.\n" \
                          f"> Enjoy your stay here!"
        await primary_channel.send(welcome_message)

@tasks.loop(minutes=10)
async def membercount_task():
    """Update member count VC name every 10 minutes."""
    await update_membercount()

async def update_membercount():
    """Update the member count in the VC channel."""
    for guild in bot.guilds:
        # Find the VC channel by ID
        vc_channel = guild.get_channel(MEMBERCOUNT_VC_CHANNEL_ID)
        if vc_channel:
            member_count = get_member_count(guild)
            try:
                await vc_channel.edit(name=f"Members: {member_count}")
                logger.info(f"Updated member count to {member_count} in {guild.name}")
            except Exception as e:
                logger.error(f"Failed to update VC name: {e}")

# Run the bot
if __name__ == "__main__":
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        logger.error("TOKEN environment variable not set!")
        print("ERROR: Please set the TOKEN environment variable!")
        exit(1)
    
    # Start Flask server for UptimeRobot
    keep_alive()
    
    # Run the bot
    bot.run(TOKEN)

