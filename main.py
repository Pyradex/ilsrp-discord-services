# ============================================================
# DOT DISCORD BOT - coollol.py
# ============================================================
import os
import asyncio
import time
import sqlite3
import json
import re
from datetime import datetime, timedelta

from flask import Flask
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running."

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# ============================================================
# BOT SETUP
# ============================================================
import nextcord
from nextcord.ext import commands

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)

# ============================================================
# CONFIG
# ============================================================
MEMBER_COUNT_CHANNEL = 1425200856944345218
VERIFICATION_CHANNEL = 1411669470040031282
WELCOME_CHANNEL = 1411676037154340874
APPLICATION_CHANNEL = 1411677337346379859
DEPLOYMENT_CHANNEL = 1467622434395000993
LOG_CHANNEL = 1475715734096056413
MOD_LOG_CHANNEL = 1475718363350175965

# Role IDs for commands
SAY_ROLES = [1411694510429438053, 1411694596911796234]
PURGE_ROLES = [1411694596911796234, 1411694510429438053]
DMROLE_ROLES = [1411694596911796234]
DMUSER_ROLES = [1411694596911796234, 1411694510429438053, 1411694617715281963, 1411694640951853208]
DEPLOYMENT_PING_ROLE = 1411695097170624512
DEPLOYMENT_ROLES = [1411694596911796234, 1411694510429438053]

# Moderation roles
MOD_ROLES = [1411694640951853208, 1411694617715281963, 1411694510429438053, 1411694596911796234]
KICK_ROLES = [1411694617715281963, 1411694510429438053, 1411694596911796234]
BAN_ROLES = [1411694510429438053, 1411694596911796234]
CLEAR_CASE_ROLES = [1411694617715281963, 1411694510429438053, 1411694596911796234]
DELETE_LOG_ROLES = [1411694596911796234]

AFK_ROLES = [1411694640951853208, 1411694617715281963, 1411694510429438053, 1411694596911796234]
VERIFICATION_ROLE = 1467239847444877332

SIDEBAR_COLOR = 0xf9ce4c
WELCOME_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698142061006889/welcomedot.png?ex=699e6e7e&is=699d1cfe&hm=29990ae9a8ebf06a9a27f9b9cf874a1014c35303d207c99adf94496f3c7e4193&"
FOOTER_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475698084817408220/footerisrp_1.png?ex=699e6e70&is=699d1cf0&hm=53dec095fb33d98d05e4bcff6ffa0224b2cb66fe6f38b9181254ef286cc4e1ef&"
HELP_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475708680304594944/bot_utils_dot.png?ex=699e784e&is=699d26ce&hm=547f72dad68ad0023cb575f10725ff244058722e648d41a96b694a175dc3818f&"
DEPLOYMENT_IMAGE = "https://cdn.discordapp.com/attachments/1468116527583723725/1475711782525079712/deploywdot.png?ex=699e7b32&is=699d29b2&hm=3fa79c8d76c0fc9551b22b338e36c7004920faed960e4284bb28c46a4ed82c43&"

# ============================================================
# DATABASE SETUP
# ============================================================
conn = sqlite3.connect('afk.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS afk (
    user_id INTEGER PRIMARY KEY,
    reason TEXT,
    start_time INTEGER,
    pings TEXT DEFAULT '[]'
)''')
conn.commit()

# ============================================================
# LOGGING FUNCTIONS
# ============================================================
async def log_action(action_type: str, data: dict):
    """Log action to the log channel"""
    try:
        channel = bot.get_channel(LOG_CHANNEL)
        if not channel:
            return
        
        timestamp = int(time.time())
        
        # Store as JSON for bot to read later
        log_data = {
            "type": action_type,
            "timestamp": timestamp,
            **data
        }
        
        embed = nextcord.Embed(
            description=f"`[LOG]` {json.dumps(log_data)}",
            color=SIDEBAR_COLOR
        )
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error logging action: {e}")

async def load_logs_from_channel():
    """Load previous logs from channel on startup to restore AFK states"""
    try:
        channel = bot.get_channel(LOG_CHANNEL)
        if not channel:
            return
        
        # Load last 100 messages
        async for message in channel.history(limit=100):
            if message.embeds and message.embeds[0].description.startswith("`[LOG]`"):
                try:
                    log_json = message.embeds[0].description.replace("`[LOG]` ", "")
                    log_data = json.loads(log_json)
                    
                    # Restore AFK states
                    if log_data.get("type") == "AFK_SET":
                        user_id = log_data.get("user_id")
                        reason = log_data.get("reason")
                        start_time = log_data.get("start_time")
                        if user_id and reason and start_time:
                            # Check if already exists
                            c.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
                            if not c.fetchone():
                                c.execute("INSERT OR REPLACE INTO afk (user_id, reason, start_time, pings) VALUES (?, ?, ?, '[]')", 
                                         (user_id, reason, start_time))
                                conn.commit()
                                print(f"Restored AFK for user {user_id}")
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Error loading logs: {e}")

# ============================================================
# AFK DATABASE FUNCTIONS
# ============================================================
def get_afk(user_id):
    c.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        return {"reason": result[1], "start_time": result[2], "pings": json.loads(result[3])}
    return None

def set_afk(user_id, reason):
    c.execute("INSERT OR REPLACE INTO afk (user_id, reason, start_time, pings) VALUES (?, ?, ?, '[]')", (user_id, reason, int(time.time())))
    conn.commit()

def remove_afk(user_id):
    c.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
    conn.commit()

def add_ping(user_id, pinger_id, message_content, channel_id, message_id):
    current = get_afk(user_id)
    if current:
        pings = current["pings"]
        pings.append({
            "pinger_id": pinger_id, 
            "message": message_content, 
            "time": int(time.time()),
            "channel_id": channel_id,
            "message_id": message_id
        })
        pings = pings[-50:]
        c.execute("UPDATE afk SET pings = ? WHERE user_id = ?", (json.dumps(pings), user_id))
        conn.commit()

def can_use_afk(member):
    return any(role.id in AFK_ROLES for role in member.roles)

def can_use_say(member):
    return any(role.id in SAY_ROLES for role in member.roles)

def can_use_purge(member):
    return any(role.id in PURGE_ROLES for role in member.roles)

def can_use_dmrole(member):
    return any(role.id in DMROLE_ROLES for role in member.roles)

def can_use_dmuser(member):
    return any(role.id in DMUSER_ROLES for role in member.roles)

def can_use_deployment(member):
    return any(role.id in DEPLOYMENT_ROLES for role in member.roles)

def can_use_mod(member):
    return any(role.id in MOD_ROLES for role in member.roles)

def can_use_kick(member):
    return any(role.id in KICK_ROLES for role in member.roles)

def can_use_ban(member):
    return any(role.id in BAN_ROLES for role in member.roles)

def can_clear_case(member):
    return any(role.id in CLEAR_CASE_ROLES for role in member.roles)

def can_delete_log(member):
    return any(role.id in DELETE_LOG_ROLES for role in member.roles)

def get_member_top_role_position(member):
    """Get the highest role position for hierarchy check"""
    if not member.roles:
        return 0
    return max(role.position for role in member.roles)

def has_higher_roles(mod, target):
    """Check if mod has higher role than target"""
    return get_member_top_role_position(mod) > get_member_top_role_position(target)

# ============================================================
# MODERATION LOGGING
# ============================================================
async def log_moderation(case_type: str, target, moderator, reason: str, duration: str = None, case_number: int = None):
    """Log moderation action to mod log channel"""
    try:
        channel = bot.get_channel(MOD_LOG_CHANNEL)
        if not channel:
            return None
        
        timestamp = int(time.time())
        
        if case_number is None:
            # Get next case number
            case_number = 1
        
        # Create JSON log for bot reading
        log_data = {
            "type": case_type,
            "case_number": case_number,
            "target_id": target.id,
            "moderator_id": moderator.id,
            "reason": reason,
            "duration": duration,
            "timestamp": timestamp
        }
        
        # Human readable embed
        embed = nextcord.Embed(
            title=f"Case #{case_number} | {case_type.upper()}",
            color=0xff6b6b if case_type in ["ban", "kick", "warn"] else 0x4bbfff,
            timestamp=nextcord.utils.utcnow()
        )
        embed.add_field(name="Community Member", value=target.mention, inline=True)
        embed.add_field(name="Issued By", value=moderator.mention, inline=True)
        embed.add_field(name="Punishment", value=case_type.capitalize(), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        if duration:
            embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Timestamp", value=f"<t:{timestamp}:F>", inline=True)
        
        # Send with JSON data in code block
        msg = await channel.send(content=f"`[MOD]` {json.dumps(log_data)}", embed=embed)
        
        return case_number
    except Exception as e:
        print(f"Error logging moderation: {e}")
        return None

async def load_mod_logs():
    """Load moderation logs from channel on startup"""
    try:
        channel = bot.get_channel(MOD_LOG_CHANNEL)
        if not channel:
            return []
        
        logs = []
        async for message in channel.history(limit=100):
            if message.content.startswith("`[MOD]`"):
                try:
                    log_json = message.content.replace("`[MOD]` ", "")
                    log_data = json.loads(log_json)
                    logs.append({
                        "message_id": message.id,
                        **log_data
                    })
                except:
                    continue
        return logs
    except Exception as e:
        print(f"Error loading mod logs: {e}")
        return []

# ============================================================
# TIME PARSING
# ============================================================
def parse_duration(duration_str: str):
    """Parse duration string like 1s, 1m, 1h, 1d, 1w"""
    if not duration_str:
        return None
    
    duration_str = duration_str.lower().strip()
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    try:
        if duration_str[-1] in multipliers:
            value = int(duration_str[:-1])
            return value * multipliers[duration_str[-1]]
        else:
            return int(duration_str)
    except:
        return None

# ============================================================
# MEMBER COUNT UPDATE (Every 5 minutes)
# ============================================================
async def update_member_count():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(MEMBER_COUNT_CHANNEL)
            if channel and channel.guild:
                count = len([m for m in channel.guild.members if not m.bot])
                await channel.edit(name=f"Members: {count}")
        except Exception as e:
            print(f"Error updating member count: {e}")
        await asyncio.sleep(300)

# ============================================================
# VERIFICATION MESSAGE (Every 12 hours)
# ============================================================
last_verification_message_id = None

async def find_and_delete_previous_verification():
    """Find and delete previous verification message on startup"""
    global last_verification_message_id
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL)
        if channel:
            # Look for the last message sent by the bot in this channel
            async for msg in channel.history(limit=10):
                if msg.author == bot.user and "> <@&" in msg.content and "Verify with Bloxlink" in msg.content:
                    last_verification_message_id = msg.id
                    try:
                        await msg.delete()
                        print(f"Deleted previous verification message: {msg.id}")
                    except:
                        pass
                    break
    except Exception as e:
        print(f"Error finding previous verification: {e}")

async def send_verification_message():
    global last_verification_message_id
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(VERIFICATION_CHANNEL)
            if channel:
                # Delete old verification message if exists
                if last_verification_message_id:
                    try:
                        old_msg = await channel.fetch_message(last_verification_message_id)
                        await old_msg.delete()
                    except:
                        pass
                msg = await channel.send(f"> <@&{VERIFICATION_ROLE}> Make sure to click **Verify with Bloxlink** for proper DOT access.")
                last_verification_message_id = msg.id
        except Exception as e:
            print(f"Error sending verification: {e}")
        await asyncio.sleep(43200)

# ============================================================
# APPLICATION STATUS MESSAGE (One time on startup)
# ============================================================
async def send_application_message():
    await bot.wait_until_ready()
    try:
        channel = bot.get_channel(APPLICATION_CHANNEL)
        if channel:
            await channel.send("## <:DOT_PRPC:1467614174740877436> `Status: Available to Applicants ✅`")
    except Exception as e:
        print(f"Error sending application message: {e}")

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def create_dm_embed(message_content, sender_name):
    # Ensure same width by using a consistent title field
    embed1 = nextcord.Embed(
        title="DOT Message",
        description=f"**{sender_name}** has sent you a new message!\n\n\"{message_content}\"",
        color=SIDEBAR_COLOR
    )
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    return [embed1, embed2]

def create_help_embeds(prefix: str):
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=HELP_IMAGE)
    
    commands_list = ""
    if prefix == ">":
        commands_list = f"""`Command:` {prefix}say
`Definition:` Deletes your message and sends the specified content as the bot.
`Permissions:` Management & Directive Roles

`Command:` {prefix}afk
`Definition:` Sets your status as Away From Keyboard.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}purge
`Definition:` Deletes messages in the current channel (1-100).
`Permissions:` Management & Directive Roles

`Command:` {prefix}dmrole
`Definition:` Sends a DM to all members with a specific role.
`Permissions:` Directive Role

`Command:` {prefix}dmuser
`Definition:` Sends a DM to a specific user by ID.
`Permissions:` Directive & Management Roles

`Command:` {prefix}deployment
`Definition:` Initiates a DOT deployment session.
`Permissions:` Management & Directive Roles

`Command:` {prefix}warn
`Definition:` Warn a member.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}timeout/{prefix}mute
`Definition:` Timeout a member. Format: {prefix}timeout @user 1d reason
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}kick
`Definition:` Kick a member from the server.
`Permissions:` Management+ Roles

`Command:` {prefix}ban
`Definition:` Ban a member. Format: {prefix}ban @user duration reason
`Permissions:` Directive Roles

`Command:` {prefix}unban
`Definition:` Unban a user by ID.
`Permissions:` Directive Roles

`Command:` {prefix}modlogs
`Definition:` View moderation logs for a member.
`Permissions:` Everyone

`Command:` {prefix}clearcase
`Definition:` Clear a moderation case by number.
`Permissions:` Management+ Roles

`Command:` {prefix}deletelog
`Definition:` Delete a moderation log completely.
`Permissions:` Directive Role Only

`Command:` {prefix}join
`Definition:` Join a voice channel.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}leave
`Definition:` Leave the voice channel.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}play
`Definition:` Play music from YouTube or Spotify.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}pause
`Definition:` Pause the music.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}resume
`Definition:` Resume the music.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}skip
`Definition:` Skip the current track.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}stop
`Definition:` Stop music and clear queue.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}queue
`Definition:` View the music queue.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}np
`Definition:` Show now playing.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}panel
`Definition:` Show music control panel.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` {prefix}help
`Definition:` Shows this help message.
`Permissions:` Everyone"""
    else:
        commands_list = f"""`Command:` /say
`Definition:` Deletes your message and sends the specified content as the bot.
`Permissions:` Management & Directive Roles

`Command:` /afk
`Definition:` Sets your status as Away From Keyboard.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /purge
`Definition:` Deletes messages in the current channel (1-100).
`Permissions:` Management & Directive Roles

`Command:` /dmrole
`Definition:` Sends a DM to all members with a specific role.
`Permissions:` Directive Role

`Command:` /dmuser
`Definition:` Sends a DM to a specific user by ID.
`Permissions:` Directive & Management Roles

`Command:` /deployment
`Definition:` Initiates a DOT deployment session.
`Permissions:` Management & Directive Roles

`Command:` /warn
`Definition:` Warn a member.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /timeout
`Definition:` Timeout a member.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /kick
`Definition:` Kick a member from the server.
`Permissions:` Management+ Roles

`Command:` /ban
`Definition:` Ban a member.
`Permissions:` Directive Roles

`Command:` /unban
`Definition:` Unban a user by ID.
`Permissions:` Directive Roles

`Command:` /modlogs
`Definition:` View moderation logs for a member.
`Permissions:` Everyone

`Command:` /clearcase
`Definition:` Clear a moderation case by number.
`Permissions:` Management+ Roles

`Command:` /join
`Definition:` Join a voice channel.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /leave
`Definition:` Leave the voice channel.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /play
`Definition:` Play music from YouTube or Spotify.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /pause
`Definition:` Pause the music.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /resume
`Definition:` Resume the music.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /skip
`Definition:` Skip the current track.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /stop
`Definition:` Stop music and clear queue.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /queue
`Definition:` View the music queue.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /np
`Definition:` Show now playing.
`Permissions:` DOT Rookie Operator+ Roles

`Command:` /help
`Definition:` Shows this help message.
`Permissions:` Everyone"""
    embed2 = nextcord.Embed(
        title=f"# <:DOT_PRPC:1467614174740877436>・__{prefix}help・Utilities Documentation__",
        description=commands_list,
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    return [embed1, embed2, embed3]

# ============================================================
# ON MESSAGE
# ============================================================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # ===== SAY COMMAND =====
    if message.content.startswith(">say ") and can_use_say(message.author):
        content = message.content[5:].strip()
        try:
            await message.delete()
        except:
            pass
        await message.channel.send(content)
        await log_action("SAY", {"user_id": message.author.id, "content": content, "channel_id": message.channel.id})
        return
    
    # ===== VERIFICATION CHANNEL AUTO-DELETE =====
    if message.channel.id == VERIFICATION_CHANNEL:
        if "https://discord.com/channels/" not in message.content:
            try:
                await message.delete()
            except:
                pass
    
    # ===== AFK SYSTEM =====
    afk_data = get_afk(message.author.id)
    if afk_data:
        remove_afk(message.author.id)
        
        elapsed = int(time.time()) - afk_data["start_time"]
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        
        pings = afk_data["pings"]
        ping_count = len(pings)
        
        # Log AFK return
        await log_action("AFK_RETURN", {
            "user_id": message.author.id,
            "reason": afk_data["reason"],
            "start_time": afk_data["start_time"],
            "duration": elapsed,
            "ping_count": ping_count
        })
        
        # Build welcome back message
        if ping_count == 0:
            description = f"Welcome back, {message.author.display_name}. You are now available.\n> Duration of AFK: **{hours} hours, {minutes} minutes, and {seconds} seconds.**\n> You were not pinged, while you were AFK."
            delete_after = None
        else:
            ping_text = ""
            for ping in pings[-5:]:
                pinger = message.guild.get_member(ping["pinger_id"])
                pinger_name = pinger.name if pinger else "Unknown"
                channel = bot.get_channel(ping["channel_id"])
                channel_mention = f"#{channel.name}" if channel else "Unknown"
                msg_link = f"https://discord.com/channels/{message.guild.id}/{ping['channel_id']}/{ping['message_id']}"
                
                ping_text += f"\n`Who?` {pinger_name}\n`What?` {ping['message']}\n`When?` <t:{ping['time']}:F>\n`Where?` [{channel_mention}]({msg_link})\n"
            
            description = f"Welcome back, {message.author.display_name}. You are now available.\n> Duration of AFK: **{hours} hours, {minutes} minutes, and {seconds} seconds.**\n> Below lists a summary of the DOT community members that had mentioned you, while you were AFK.{ping_text}"
            delete_after = 30 if ping_count >= 3 else 120
        
        embed1 = nextcord.Embed(description=description, color=SIDEBAR_COLOR)
        embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
        embed2.set_image(url=FOOTER_IMAGE)
        
        await message.channel.send(embeds=[embed1, embed2], delete_after=delete_after)
    
    # Check for mentions of AFK users
    for mention in message.mentions:
        afk_info = get_afk(mention.id)
        if afk_info:
            add_ping(mention.id, message.author.id, message.content, message.channel.id, message.id)
            
            elapsed = int(time.time()) - afk_info["start_time"]
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            
            # Log ping
            await log_action("AFK_PING", {
                "afk_user_id": mention.id,
                "pinged_by": message.author.id,
                "message": message.content,
                "channel_id": message.channel.id
            })
            
            embed = nextcord.Embed(
                description=f"**{mention.name}** is currently AFK: **{afk_info['reason']}**\nAway for: **{hours}h {minutes}m**",
                color=SIDEBAR_COLOR
            )
            embed.set_image(url=FOOTER_IMAGE)
            
            await message.reply(embed=embed)
    
    await bot.process_commands(message)

# ============================================================
# WELCOME EMBED
# ============================================================
@bot.event
async def on_member_join(member):
    if member.bot:
        return
    
    channel = bot.get_channel(WELCOME_CHANNEL)
    if not channel:
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=WELCOME_IMAGE)
    
    embed2 = nextcord.Embed(
        description=f"# Welcome to President Roleplay Community・Department of Transportation.\n\n"
                   f"Hello {member.display_name}\n\n"
                   f"**Welcome to PRPC・Department of Transportation!**\n"
                   f"> - DOT primarily focuses on enhancing the convoy organization mechanics of Presidential Roleplay.\n"
                   f"> - We also engage in political and security affairs with the Mayor, ensuring that his safety and protection is prevalent.\n\n"
                   f"# Review our __key__ channels:\n\n"
                   f"> - Ensure proper Roblox OAuthentication in <#1411669470040031282>.\n"
                   f"> - Read more about the logistics and contributions of DOT in <#1411679034068176927>.\n"
                   f"> - You must follow the ⁠<#1411675000892690505>, which also include PRPC's community regulations.\n"
                   f"> - Want to apply? Head on over to ⁠<#1411677337346379859>.\n"
                   f"> - Need further assistance with anything. Contact <#1411677021976920074> or make <#1467242635482628278>.\n"
                   f"> - Lastly, you are able to configure your pings/mentions in ⁠<#1411684343495266375>.\n\n"
                   f"# __Additional Information__\n"
                   f"Note: The Department of Transportation is primarily ran by MasterGato567 [Director Gato], kalokmanklm [Assistant Director Ka Lok], and Mys1icX [Assistant Director Pyra]. Please refrain from contacting them, unless absolutely necessarily, and follow the chain of command of online individuals, by contacting a Technician, then Operator, then Engineer, then Manager.\n\n"
                   f"Thank you so much for joining the Department of Transportation, and we hope you have a fun roleplay experience and friendly communication environment.",
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=member.mention, embeds=[embed1, embed2, embed3])
    await log_action("MEMBER_JOIN", {"user_id": member.id, "username": member.name})

# ============================================================
# SLASH COMMANDS
# ============================================================

@bot.slash_command(name="help", description="Show help documentation")
async def help_slash(interaction: nextcord.Interaction):
    embeds = create_help_embeds("/")
    await interaction.response.send_message(embeds=embeds)

@bot.slash_command(name="afk", description="Set AFK status")
async def afk(interaction: nextcord.Interaction, reason: str = "AFK"):
    if not can_use_afk(interaction.user):
        await interaction.response.send_message("This command is only permissable for usage by a DOT Rookie Operator+.", ephemeral=True)
        return
    
    set_afk(interaction.user.id, reason)
    
    # Log AFK set
    await log_action("AFK_SET", {
        "user_id": interaction.user.id,
        "reason": reason,
        "start_time": int(time.time())
    })
    
    try:
        old_nick = interaction.user.display_name
        if not old_nick.startswith("[AFK]"):
            try:
                await interaction.user.edit(nick=f"[AFK] {old_nick}")
            except nextcord.Forbidden:
                await interaction.user.send("I am unable to update your nickname due to your highest role being above my role. You are AFK though.")
    except Exception:
        pass
    
    embed1 = nextcord.Embed(
        description=f"{interaction.user.mention}, you are now away from keyboard for **{reason}**. See you later!",
        color=SIDEBAR_COLOR
    )
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    
    await interaction.response.send_message(embeds=[embed1, embed2])

@bot.slash_command(name="say", description="Send a message as the bot")
async def say_slash(interaction: nextcord.Interaction, message: str):
    if not can_use_say(interaction.user):
        await interaction.response.send_message("The command `/say` is only permissable to Management and Directive members.", ephemeral=True)
        return
    
    await interaction.response.send_message(message)
    await log_action("SAY", {"user_id": interaction.user.id, "content": message, "type": "slash"})

@bot.slash_command(name="purge", description="Purge messages in channel")
async def purge_slash(interaction: nextcord.Interaction, amount: int):
    if not can_use_purge(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if amount < 1 or amount > 100:
        await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"Deleted {len(deleted)} messages.", ephemeral=True)
        await log_action("PURGE", {
            "user_id": interaction.user.id,
            "amount": len(deleted),
            "channel_id": interaction.channel.id
        })
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

@bot.slash_command(name="dmrole", description="DM all users with a specific role")
async def dmrole_slash(interaction: nextcord.Interaction, role_id: str, message: str):
    if not can_use_dmrole(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        role_id = int(role_id)
    except ValueError:
        await interaction.response.send_message("Invalid role ID.", ephemeral=True)
        return
    
    role = interaction.guild.get_role(role_id)
    if not role:
        await interaction.response.send_message("Role not found.", ephemeral=True)
        return
    
    embeds = create_dm_embed(message, interaction.user.display_name)
    success = 0
    failed = 0
    
    for member in role.members:
        try:
            await member.send(embeds=embeds)
            success += 1
        except:
            failed += 1
    
    await interaction.response.send_message(f"Message sent to {success} members. Failed: {failed}", ephemeral=True)
    await log_action("DMROLE", {
        "user_id": interaction.user.id,
        "role_id": role_id,
        "message": message,
        "success": success,
        "failed": failed
    })

@bot.slash_command(name="dmuser", description="DM a specific user")
async def dmuser_slash(interaction: nextcord.Interaction, user_id: str, message: str):
    if not can_use_dmuser(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
    except ValueError:
        await interaction.response.send_message("Invalid user ID.", ephemeral=True)
        return
    
    user = await bot.fetch_user(user_id)
    if not user:
        await interaction.response.send_message("User not found.", ephemeral=True)
        return
    
    embeds = create_dm_embed(message, interaction.user.display_name)
    
    try:
        await user.send(embeds=embeds)
        await interaction.response.send_message(f"Message sent to {user.name}.", ephemeral=True)
        await log_action("DMUSER", {
            "sender_id": interaction.user.id,
            "target_id": user_id,
            "message": message
        })
    except Exception as e:
        await interaction.response.send_message(f"Failed to send message: {e}", ephemeral=True)

@bot.slash_command(name="deployment", description="Initiate a DOT deployment session")
async def deployment_slash(interaction: nextcord.Interaction, initial_roleplay: str = "Normal"):
    if not can_use_deployment(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel = bot.get_channel(DEPLOYMENT_CHANNEL)
    if not channel:
        await interaction.response.send_message("Deployment channel not found.", ephemeral=True)
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=DEPLOYMENT_IMAGE)
    
    embed2 = nextcord.Embed(
        description=f"# A DOT Deployment is being initiated!\n\n"
                   f"> - Host: {interaction.user.mention}\n"
                   f"> - Initial Roleplay: **{initial_roleplay}**\n"
                   f"> - Location: DOT Building\n\n"
                   f"Welcome to another session.\n"
                   f"> - In elections, be sure that cars are organized neatly behind the staff vehicle with the assistance of person-pushing and tools.\n"
                   f"> - Refuel Staff + Convoy Vehicles.\n"
                   f"> - Fix Broken Tires from Weaponry or Spike Strips/Tool Abuse\n"
                   f"> - Report Tool Abusers to PRPC Staff.\n"
                   f"> - Before the president moves, make sure a DOT Unit **sets up** a proper entrance and parking system to ensure good coordination. This will help you receive a promotion.\n"
                   f"> - High-Ranks observe Technicians and Operators for promotions and good, efficient conduct.\n"
                   f"> - Suggestions based on observations will be passed on for SHR to implement new policies/changes to the procedures of DOT personnel.",
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=f"<@&{DEPLOYMENT_PING_ROLE}>", embeds=[embed1, embed2, embed3])
    await interaction.response.send_message("Deployment message sent!", ephemeral=True)
    await log_action("DEPLOYMENT", {
        "user_id": interaction.user.id,
        "initial_roleplay": initial_roleplay
    })

# ============================================================
# PREFIX COMMANDS
# ============================================================

@bot.command(name="help")
async def help_prefix(ctx):
    embeds = create_help_embeds(">")
    await ctx.send(embeds=embeds)

@bot.command(name="afk")
async def afk_prefix(ctx, *, reason="AFK"):
    if not can_use_afk(ctx.author):
        await ctx.send("This command is only permissable for usage by a DOT Rookie Operator+.")
        return
    
    set_afk(ctx.author.id, reason)
    
    # Log AFK set
    await log_action("AFK_SET", {
        "user_id": ctx.author.id,
        "reason": reason,
        "start_time": int(time.time())
    })
    
    try:
        old_nick = ctx.author.display_name
        if not old_nick.startswith("[AFK]"):
            try:
                await ctx.author.edit(nick=f"[AFK] {old_nick}")
            except nextcord.Forbidden:
                await ctx.author.send("I am unable to update your nickname due to your highest role being above my role. You are AFK though.")
    except Exception:
        pass
    
    embed1 = nextcord.Embed(
        description=f"{ctx.author.mention}, you are now away from keyboard for **{reason}**. See you later!",
        color=SIDEBAR_COLOR
    )
    embed2 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed2.set_image(url=FOOTER_IMAGE)
    
    await ctx.send(embeds=[embed1, embed2])

@bot.command(name="purge")
async def purge_prefix(ctx, amount: int):
    if not can_use_purge(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    if amount < 1 or amount > 100:
        await ctx.send("Amount must be between 1 and 100.")
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {len(deleted)} messages.", delete_after=5)
        await log_action("PURGE", {
            "user_id": ctx.author.id,
            "amount": len(deleted),
            "channel_id": ctx.channel.id
        })
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="dmrole")
async def dmrole_prefix(ctx, role_id: int, *, message: str):
    if not can_use_dmrole(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Role not found.")
        return
    
    embeds = create_dm_embed(message, ctx.author.display_name)
    success = 0
    failed = 0
    
    for member in role.members:
        try:
            await member.send(embeds=embeds)
            success += 1
        except:
            failed += 1
    
    await ctx.send(f"Message sent to {success} members. Failed: {failed}", delete_after=10)
    await log_action("DMROLE", {
        "user_id": ctx.author.id,
        "role_id": role_id,
        "message": message,
        "success": success,
        "failed": failed
    })

@bot.command(name="dmuser")
async def dmuser_prefix(ctx, user_id: int, *, message: str):
    if not can_use_dmuser(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    user = await bot.fetch_user(user_id)
    if not user:
        await ctx.send("User not found.")
        return
    
    embeds = create_dm_embed(message, ctx.author.display_name)
    
    try:
        await user.send(embeds=embeds)
        await ctx.send(f"Message sent to {user.name}.", delete_after=10)
        await log_action("DMUSER", {
            "sender_id": ctx.author.id,
            "target_id": user_id,
            "message": message
        })
    except Exception as e:
        await ctx.send(f"Failed to send message: {e}")

@bot.command(name="deployment")
async def deployment_prefix(ctx, *, initial_roleplay="Normal"):
    if not can_use_deployment(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    channel = bot.get_channel(DEPLOYMENT_CHANNEL)
    if not channel:
        await ctx.send("Deployment channel not found.")
        return
    
    embed1 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed1.set_image(url=DEPLOYMENT_IMAGE)
    
    embed2 = nextcord.Embed(
        description=f"# A DOT Deployment is being initiated!\n\n"
                   f"> - Host: {ctx.author.mention}\n"
                   f"> - Initial Roleplay: **{initial_roleplay}**\n"
                   f"> - Location: DOT Building\n\n"
                   f"Welcome to another session.\n"
                   f"> - In elections, be sure that cars are organized neatly behind the staff vehicle with the assistance of person-pushing and tools.\n"
                   f"> - Refuel Staff + Convoy Vehicles.\n"
                   f"> - Fix Broken Tires from Weaponry or Spike Strips/Tool Abuse\n"
                   f"> - Report Tool Abusers to PRPC Staff.\n"
                   f"> - Before the president moves, make sure a DOT Unit **sets up** a proper entrance and parking system to ensure good coordination. This will help you receive a promotion.\n"
                   f"> - High-Ranks observe Technicians and Operators for promotions and good, efficient conduct.\n"
                   f"> - Suggestions based on observations will be passed on for SHR to implement new policies/changes to the procedures of DOT personnel.",
        color=SIDEBAR_COLOR
    )
    
    embed3 = nextcord.Embed(color=SIDEBAR_COLOR)
    embed3.set_image(url=FOOTER_IMAGE)
    
    await channel.send(content=f"<@&{DEPLOYMENT_PING_ROLE}>", embeds=[embed1, embed2, embed3])
    await ctx.send("Deployment message sent!", delete_after=10)
    await log_action("DEPLOYMENT", {
        "user_id": ctx.author.id,
        "initial_roleplay": initial_roleplay
    })

# ============================================================
# MODERATION COMMANDS
# ============================================================

async def get_target_from_input(ctx_or_interaction, user_input):
    """Get a member from mention, ID, or role"""
    guild = ctx_or_interaction.guild
    
    # Try mention
    if isinstance(user_input, nextcord.Member):
        return user_input
    
    # Try parsing as ID
    try:
        user_id = int(user_input)
        member = guild.get_member(user_id)
        if member:
            return member
    except:
        pass
    
    # Try role mention/ID
    try:
        role_id = int(str(user_input).replace("<@&", "").replace(">", ""))
        role = guild.get_role(role_id)
        if role:
            return role
    except:
        pass
    
    return None

# === WARN COMMAND ===
@bot.slash_command(name="warn", description="Warn a member")
async def warn_slash(interaction: nextcord.Interaction, member: nextcord.Member, reason: str):
    if not can_use_mod(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if not has_higher_roles(interaction.user, member):
        await interaction.response.send_message("You cannot punish someone with a higher role than you.", ephemeral=True)
        return
    
    case_num = await log_moderation("warn", member, interaction.user, reason)
    
    embed = nextcord.Embed(
        title="✅ Warning Issued",
        description=f"**{member.display_name}** has been warned.\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="warn")
async def warn_prefix(ctx, member, *, reason):
    if not can_use_mod(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    target = await get_target_from_input(ctx, member)
    if not target:
        await ctx.send("User not found.")
        return
    
    if isinstance(target, nextcord.Role):
        # Warn all members with role
        success = 0
        for m in target.members:
            if has_higher_roles(ctx.author, m):
                await log_moderation("warn", m, ctx.author, reason)
                success += 1
        await ctx.send(f"Warned {success} members with role {target.name}.")
        return
    
    if not has_higher_roles(ctx.author, target):
        await ctx.send("You cannot punish someone with a higher role than you.")
        return
    
    case_num = await log_moderation("warn", target, ctx.author, reason)
    
    embed = nextcord.Embed(
        title="✅ Warning Issued",
        description=f"**{target.display_name}** has been warned.\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# === TIMEOUT/MUTE COMMAND ===
@bot.slash_command(name="timeout", description="Timeout a member")
async def timeout_slash(interaction: nextcord.Interaction, member: nextcord.Member, duration: str, reason: str):
    if not can_use_mod(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if not has_higher_roles(interaction.user, member):
        await interaction.response.send_message("You cannot punish someone with a higher role than you.", ephemeral=True)
        return
    
    seconds = parse_duration(duration)
    if seconds is None or seconds <= 0:
        await interaction.response.send_message("Invalid duration. Use format: 1s, 1m, 1h, 1d, 1w", ephemeral=True)
        return
    
    if seconds > 2419200:  # 4 weeks
        await interaction.response.send_message("Maximum timeout duration is 4 weeks.", ephemeral=True)
        return
    
    try:
        await member.timeout(nextcord.utils.utcnow() + timedelta(seconds=seconds), reason=reason)
    except:
        await interaction.response.send_message("I cannot timeout this user. They may have a higher role.", ephemeral=True)
        return
    
    case_num = await log_moderation("timeout", member, interaction.user, reason, duration)
    
    embed = nextcord.Embed(
        title="✅ Member Timed Out",
        description=f"**{member.display_name}** has been timed out.\n**Duration:** {duration}\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="timeout")
async def timeout_prefix(ctx, member, duration, *, reason):
    if not can_use_mod(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    target = await get_target_from_input(ctx, member)
    if not target:
        await ctx.send("User not found.")
        return
    
    if isinstance(target, nextcord.Role):
        await ctx.send("Please mention a user, not a role, for timeout.")
        return
    
    if not has_higher_roles(ctx.author, target):
        await ctx.send("You cannot punish someone with a higher role than you.")
        return
    
    seconds = parse_duration(duration)
    if seconds is None or seconds <= 0:
        await ctx.send("Invalid duration. Use format: 1s, 1m, 1h, 1d, 1w")
        return
    
    if seconds > 2419200:
        await ctx.send("Maximum timeout duration is 4 weeks.")
        return
    
    try:
        await target.timeout(nextcord.utils.utcnow() + timedelta(seconds=seconds), reason=reason)
    except:
        await ctx.send("I cannot timeout this user.")
        return
    
    case_num = await log_moderation("timeout", target, ctx.author, reason, duration)
    
    embed = nextcord.Embed(
        title="✅ Member Timed Out",
        description=f"**{target.display_name}** has been timed out.\n**Duration:** {duration}\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# Alias for timeout
@bot.command(name="mute")
async def mute_prefix(ctx, member, duration, *, reason):
    await ctx.invoke(timeout_prefix, member=member, duration=duration, reason=reason)

# === KICK COMMAND ===
@bot.slash_command(name="kick", description="Kick a member")
async def kick_slash(interaction: nextcord.Interaction, member: nextcord.Member, reason: str):
    if not can_use_kick(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if not has_higher_roles(interaction.user, member):
        await interaction.response.send_message("You cannot punish someone with a higher role than you.", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
    except:
        await interaction.response.send_message("I cannot kick this user.", ephemeral=True)
        return
    
    case_num = await log_moderation("kick", member, interaction.user, reason)
    
    embed = nextcord.Embed(
        title="✅ Member Kicked",
        description=f"**{member.display_name}** has been kicked.\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="kick")
async def kick_prefix(ctx, member, *, reason):
    if not can_use_kick(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    target = await get_target_from_input(ctx, member)
    if not target:
        await ctx.send("User not found.")
        return
    
    if isinstance(target, nextcord.Role):
        await ctx.send("Please mention a user, not a role, for kick.")
        return
    
    if not has_higher_roles(ctx.author, target):
        await ctx.send("You cannot punish someone with a higher role than you.")
        return
    
    try:
        await target.kick(reason=reason)
    except:
        await ctx.send("I cannot kick this user.")
        return
    
    case_num = await log_moderation("kick", target, ctx.author, reason)
    
    embed = nextcord.Embed(
        title="✅ Member Kicked",
        description=f"**{target.display_name}** has been kicked.\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# === BAN COMMAND ===
@bot.slash_command(name="ban", description="Ban a member")
async def ban_slash(interaction: nextcord.Interaction, member: nextcord.Member, duration: str = None, *, reason: str):
    if not can_use_ban(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if not has_higher_roles(interaction.user, member):
        await interaction.response.send_message("You cannot punish someone with a higher role than you.", ephemeral=True)
        return
    
    delete_message_seconds = 0
    if duration and duration.lower() != "permanent":
        seconds = parse_duration(duration)
        if seconds and seconds > 0:
            delete_message_seconds = min(seconds, 604800)  # Max 7 days
            duration_text = duration
        else:
            duration_text = "Permanent"
    else:
        duration_text = "Permanent"
    
    try:
        await member.ban(reason=reason, delete_message_seconds=delete_message_seconds)
    except:
        await interaction.response.send_message("I cannot ban this user.", ephemeral=True)
        return
    
    case_num = await log_moderation("ban", member, interaction.user, reason, duration_text)
    
    embed = nextcord.Embed(
        title="✅ Member Banned",
        description=f"**{member.display_name}** has been banned.\n**Duration:** {duration_text}\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="ban")
async def ban_prefix(ctx, member, *args):
    if not can_use_ban(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    # Parse: >ban user duration reason OR >ban user reason
    if len(args) >= 2:
        # Check if second arg is a duration
        duration = args[0]
        reason = " ".join(args[1:])
        seconds = parse_duration(duration)
        if seconds and seconds > 0:
            duration_text = duration
        else:
            duration_text = "Permanent" if not duration.replace("per", "").replace("perm", "") else "Permanent"
            reason = " ".join(args)
    else:
        duration_text = "Permanent"
        reason = " ".join(args) if args else "No reason provided"
    
    target = await get_target_from_input(ctx, member)
    if not target:
        await ctx.send("User not found.")
        return
    
    if isinstance(target, nextcord.Role):
        await ctx.send("Please mention a user, not a role, for ban.")
        return
    
    if not has_higher_roles(ctx.author, target):
        await ctx.send("You cannot punish someone with a higher role than you.")
        return
    
    try:
        await target.ban(reason=reason, delete_message_seconds=0)
    except:
        await ctx.send("I cannot ban this user.")
        return
    
    case_num = await log_moderation("ban", target, ctx.author, reason, duration_text)
    
    embed = nextcord.Embed(
        title="✅ Member Banned",
        description=f"**{target.display_name}** has been banned.\n**Duration:** {duration_text}\n**Reason:** {reason}\n**Case:** #{case_num}",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# === UNBAN COMMAND ===
@bot.slash_command(name="unban", description="Unban a member")
async def unban_slash(interaction: nextcord.Interaction, user_id: str, *, reason: str = "No reason provided"):
    if not can_use_ban(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
    except:
        await interaction.response.send_message("Invalid user ID.", ephemeral=True)
        return
    
    try:
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user, reason=reason)
    except:
        await interaction.response.send_message("User not found or not banned.", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Member Unbanned",
        description=f"**{user.name}** has been unbanned.\n**Reason:** {reason}",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="unban")
async def unban_prefix(ctx, user_id, *, reason="No reason provided"):
    if not can_use_ban(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    try:
        user_id = int(user_id)
    except:
        await ctx.send("Invalid user ID.")
        return
    
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
    except:
        await ctx.send("User not found or not banned.")
        return
    
    embed = nextcord.Embed(
        title="✅ Member Unbanned",
        description=f"**{user.name}** has been unbanned.\n**Reason:** {reason}",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# === MODLOGS COMMAND ===
@bot.slash_command(name="modlogs", description="View moderation logs for a member")
async def modlogs_slash(interaction: nextcord.Interaction, member: nextcord.Member):
    await interaction.response.defer()
    
    logs = await load_mod_logs()
    user_logs = [log for log in logs if log.get("target_id") == member.id]
    
    if not user_logs:
        await interaction.followup.send(f"No moderation logs found for **{member.display_name}**.", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title=f"📋 Moderation Logs - {member.display_name}",
        color=SIDEBAR_COLOR
    )
    
    for log in user_logs[-10:]:
        case_num = log.get("case_number", "?")
        case_type = log.get("type", "?").upper()
        reason = log.get("reason", "No reason")
        mod_id = log.get("moderator_id")
        timestamp = log.get("timestamp", 0)
        
        mod = interaction.guild.get_member(mod_id)
        mod_name = mod.display_name if mod else "Unknown"
        
        embed.add_field(
            name=f"Case #{case_num} | {case_type}",
            value=f"**Reason:** {reason}\n**By:** {mod_name}\n**Date:** <t:{timestamp}:d>",
            inline=False
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.command(name="modlogs")
async def modlogs_prefix(ctx, member):
    logs = await load_mod_logs()
    
    # Try to find target
    target = await get_target_from_input(ctx, member)
    if not target:
        await ctx.send("User not found.")
        return
    
    if isinstance(target, nextcord.Role):
        await ctx.send("Please mention a user, not a role.")
        return
    
    user_logs = [log for log in logs if log.get("target_id") == target.id]
    
    if not user_logs:
        await ctx.send(f"No moderation logs found for **{target.display_name}**.")
        return
    
    embed = nextcord.Embed(
        title=f"📋 Moderation Logs - {target.display_name}",
        color=SIDEBAR_COLOR
    )
    
    for log in user_logs[-10:]:
        case_num = log.get("case_number", "?")
        case_type = log.get("type", "?").upper()
        reason = log.get("reason", "No reason")
        mod_id = log.get("moderator_id")
        timestamp = log.get("timestamp", 0)
        
        mod = ctx.guild.get_member(mod_id)
        mod_name = mod.display_name if mod else "Unknown"
        
        embed.add_field(
            name=f"Case #{case_num} | {case_type}",
            value=f"**Reason:** {reason}\n**By:** {mod_name}\n**Date:** <t:{timestamp}:d>",
            inline=False
        )
    
    await ctx.send(embed=embed)

# === CLEARCASE COMMAND ===
@bot.slash_command(name="clearcase", description="Clear a moderation case")
async def clearcase_slash(interaction: nextcord.Interaction, case_number: int):
    if not can_clear_case(interaction.user):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    logs = await load_mod_logs()
    case_log = next((log for log in logs if log.get("case_number") == case_number), None)
    
    if not case_log:
        await interaction.response.send_message(f"Case #{case_number} not found.", ephemeral=True)
        return
    
    # Check if user can clear this type of case
    case_type = case_log.get("type", "").lower()
    if case_type in ["kick", "ban"]:
        if not any(role.id in [1411694510429438053, 1411694596911796234] for role in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to clear kick/ban cases.", ephemeral=True)
            return
    
    # Try to delete the message
    try:
        channel = bot.get_channel(MOD_LOG_CHANNEL)
        message = await channel.fetch_message(case_log.get("message_id"))
        await message.delete()
    except:
        pass
    
    embed = nextcord.Embed(
        title="✅ Case Cleared",
        description=f"Case #{case_number} has been cleared.",
        color=SIDEBAR_COLOR
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="clearcase")
async def clearcase_prefix(ctx, case_number: int):
    if not can_clear_case(ctx.author):
        await ctx.send("You don't have permission to use this command.")
        return
    
    logs = await load_mod_logs()
    case_log = next((log for log in logs if log.get("case_number") == case_number), None)
    
    if not case_log:
        await ctx.send(f"Case #{case_number} not found.")
        return
    
    # Check if user can clear this type of case
    case_type = case_log.get("type", "").lower()
    if case_type in ["kick", "ban"]:
        if not any(role.id in [1411694510429438053, 1411694596911796234] for role in ctx.author.roles):
            await ctx.send("You don't have permission to clear kick/ban cases.")
            return
    
    # Try to delete the message
    try:
        channel = bot.get_channel(MOD_LOG_CHANNEL)
        message = await channel.fetch_message(case_log.get("message_id"))
        await message.delete()
    except:
        pass
    
    embed = nextcord.Embed(
        title="✅ Case Cleared",
        description=f"Case #{case_number} has been cleared.",
        color=SIDEBAR_COLOR
    )
    await ctx.send(embed=embed)

# === DELETELOG COMMAND (Only 1411694596911796234) ===
@bot.command(name="deletelog")
async def deletelog_prefix(ctx, case_number: int):
    if not can_delete_log(ctx.author):
        await ctx.send("You don't have permission to delete logs.")
        return
    
    logs = await load_mod_logs()
    case_log = next((log for log in logs if log.get("case_number") == case_number), None)
    
    if not case_log:
        await ctx.send(f"Case #{case_number} not found.")
        return
    
    # Delete the message
    try:
        channel = bot.get_channel(MOD_LOG_CHANNEL)
        message = await channel.fetch_message(case_log.get("message_id"))
        await message.delete()
        await ctx.send(f"Log for Case #{case_number} has been deleted.")
    except:
        await ctx.send("Could not delete the log message.")

# ============================================================
# ON READY
# ============================================================
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        await bot.sync_all_application_commands()
        print("Slash commands synced!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    # Load previous logs to restore AFK states
    await load_logs_from_channel()
    
    # Find and delete previous verification message, then send new one
    await find_and_delete_previous_verification()
    
    # Send initial verification message on startup and track its ID
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL)
        if channel:
            msg = await channel.send(f"> <@&{VERIFICATION_ROLE}> Make sure to click **Verify with Bloxlink** for proper DOT access.")
            last_verification_message_id = msg.id
    except Exception as e:
        print(f"Error sending initial verification: {e}")
    
    bot.loop.create_task(update_member_count())
    bot.loop.create_task(send_verification_message())
    bot.loop.create_task(send_application_message())

# ============================================================
# RUN BOT
# ============================================================
# Load music cog
try:
    bot.load_extension("music")
    print("Music cog loaded!")
except Exception as e:
    print(f"Error loading music cog: {e}")

bot.run(os.environ.get("DISCORD_TOKEN"))

