import os
import logging
from flask import Flask, request, jsonify, session, redirect
from threading import Thread
from datetime import datetime
import asyncio
import aiohttp

import nextcord
from nextcord.ext import commands, tasks
from nextcord import ui
from nextcord.interactions import Interaction

# Import database
from database import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nextcord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(name)s: %(message)s'))
logger.addHandler(handler)

# Flask app for UptimeRobot and OAuth
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

# OAuth configuration
ROBLOX_CLIENT_ID = os.environ.get("ROBLOX_CLIENT_ID", "")
ROBLOX_CLIENT_SECRET = os.environ.get("ROBLOX_CLIENT_SECRET", "")
ROBLOX_REDIRECT_URI = os.environ.get("ROBLOX_REDIRECT_URI", "")
VERIFY_CHANNEL_ID = 1471660766536011952  # Channel for verification messages

# Discord OAuth (optional)
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
DISCORD_OAUTH_SCOPE = "identify email"

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/api/roblox/login')
def roblox_login():
    """Redirect to Roblox OAuth login."""
    if not ROBLOX_CLIENT_ID:
        return jsonify({"error": "Roblox OAuth not configured"}), 500
    
    # Generate state for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    auth_url = f"https://www.roblox.com/oauth/authorize?response_type=code&client_id={ROBLOX_CLIENT_ID}&redirect_uri={ROBLOX_REDIRECT_URI}&scope=openid"
    return redirect(auth_url)

@app.route('/api/roblox/callback')
def roblox_callback():
    """Handle Roblox OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Verify state
    if state != session.get('oauth_state'):
        return jsonify({"error": "Invalid state"}), 400
    
    # Exchange code for token
    token_url = "https://apis.roblox.com/oauth/v1/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": ROBLOX_CLIENT_ID,
        "client_secret": ROBLOX_CLIENT_SECRET,
        "redirect_uri": ROBLOX_REDIRECT_URI
    }
    
    try:
        import requests
        response = requests.post(token_url, data=data)
        if response.status_code != 200:
            return jsonify({"error": "Failed to get token"}), 400
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Get user info from Roblox
        user_url = "https://users.roblox.com/v1/users/authenticated"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        
        if user_response.status_code != 200:
            return jsonify({"error": "Failed to get user info"}), 400
        
        user_data = user_response.json()
        
        # Store in session for linking
        session['roblox_id'] = user_data.get("id")
        session['roblox_username'] = user_data.get("name")
        
        return jsonify({
            "success": True,
            "roblox_id": user_data.get("id"),
            "roblox_username": user_data.get("name"),
            "message": "Please use /link command in Discord to link this account"
        })
    
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        return jsonify({"error": str(e)}), 500

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

# Verification button view
class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        button = ui.Button(
            label="Verify with ILSRP Systems",
            style=nextcord.ButtonStyle.primary,
            custom_id="verify_button",
            emoji="<:ILSRP:1471990869166002291>"
        )
        button.callback = self.verify_button_callback
        self.add_item(button)
    
    async def verify_button_callback(self, interaction: Interaction):
        # Create a modal for Roblox username input
        modal = VerifyModal()
        await interaction.response.send_modal(modal)

class VerifyModal(ui.Modal):
    def __init__(self):
        super().__init__("Link Roblox Account")
        
        self.username_input = ui.TextInput(
            label="Roblox Username",
            placeholder="Enter your Roblox username",
            style=nextcord.TextInputStyle.short,
            required=True,
            min_length=3,
            max_length=20
        )
        self.add_item(self.username_input)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        roblox_username = self.username_input.value
        
        # Verify Roblox user exists
        roblox_id = await get_roblox_id(roblox_username)
        
        if not roblox_id:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Verification Failed",
                description=f"Could not find a Roblox account with username **@{roblox_username}**.\n\nPlease check the spelling and try again.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Check if already linked
        existing_user = await db.get_user(roblox_id=roblox_id)
        
        if existing_user and existing_user.get("discord_id") != interaction.user.id:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Already Linked",
                description="This Roblox account is already linked to another Discord account.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Check blacklist
        is_blacklisted = await db.is_blacklisted(
            discord_id=interaction.user.id,
            roblox_id=roblox_id,
            guild_id=interaction.guild.id
        )
        
        if is_blacklisted:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Blacklisted",
                description="You are blacklisted from the verification system. Contact staff for assistance.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Link accounts
        success = await db.add_verification(
            discord_id=interaction.user.id,
            roblox_id=roblox_id,
            roblox_username=roblox_username,
            discord_username=str(interaction.user),
            guild_id=interaction.guild.id,
            discord_join_date=interaction.user.joined_at,
            guild_join_date=interaction.user.joined_at
        )
        
        if success:
            # Add verified role if exists
            verified_role = nextcord.utils.get(interaction.guild.roles, name="Verified")
            if verified_role:
                await interaction.user.add_roles(verified_role)
            
            # Send to verification channel
            verify_channel = bot.get_channel(VERIFY_CHANNEL_ID)
            if verify_channel:
                embed = nextcord.Embed(
                    title="<:ILSRP:1471990869166002291> | New Verification",
                    description=f"**{interaction.user.mention}** has verified their account!",
                    color=SIDEBAR_COLOR
                )
                embed.add_field(name="Discord", value=f"{interaction.user} ({interaction.user.id})", inline=True)
                embed.add_field(name="Roblox", value=f"@{roblox_username} ({roblox_id})", inline=True)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                await verify_channel.send(embed=embed)
            
            # Success embed
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Verified Successfully!",
                description=f"Your Discord account has been linked to **@{roblox_username}**!\n\nYou now have full community access.",
                color=0x00ff00
            )
            await interaction.send(embed=embed, ephemeral=True)
        else:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Verification Error",
                description="An error occurred while linking your account. Please try again later.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)

async def get_roblox_id(username: str):
    """Get Roblox user ID from username."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.roblox.com/users/search?keyword={username}&maxRows=1") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("Results"):
                        return data["Results"][0]["Id"]
    except Exception as e:
        logger.error(f"Error getting Roblox ID: {e}")
    return None

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

# ==================== /GETINFO COMMAND ====================

@bot.slash_command(name="getinfo", description="Get user information (Melonly style)")
async def getinfo(interaction: Interaction, user: nextcord.Member = None):
    """Get information about a user similar to Melonly verification."""
    await interaction.response.defer()
    
    target_user = user or interaction.user
    guild = interaction.guild
    
    # Get user from database
    db_user = await db.get_user(discord_id=target_user.id)
    
    # Get user roles (excluding @everyone)
    roles = [role.mention for role in target_user.roles if role.name != "@everyone"]
    roles_text = ", ".join(roles) if roles else "No roles"
    
    # Create embed similar to Melonly
    embed = nextcord.Embed(
        title=f"<:ILSRP:1471990869166002291> | User Information",
        color=SIDEBAR_COLOR
    )
    embed.set_thumbnail(url=target_user.display_avatar.url)
    
    # User basic info
    embed.add_field(
        name="<:discord:1076415080524386324> Discord",
        value=f"**Username:** {target_user}\n"
              f"**ID:** `{target_user.id}`\n"
              f"**Tag:** {target_user.mention}\n"
              f"**Created:** <t:{int(target_user.created_at.timestamp())}:R>\n"
              f"**Joined:** <t:{int(target_user.joined_at.timestamp())}:R>",
        inline=True
    )
    
    # Verification status
    if db_user:
        verified_at = db_user.get("verified_at")
        verified_text = f"<t:{int(verified_at.timestamp())}:R>" if verified_at else "Unknown"
        
        embed.add_field(
            name="<:roblox:1076415080524386324> Roblox (Verified)",
            value=f"**Username:** @{db_user.get('roblox_username', 'N/A')}\n"
                  f"**ID:** `{db_user.get('roblox_id', 'N/A')}`\n"
                  f"**Verified:** {verified_text}",
            inline=True
        )
        
        # Add verification badge
        embed.description = f"✅ **This user is verified with ILSRP Systems**"
    else:
        embed.add_field(
            name="<:roblox:1076415080524386324> Roblox (Not Verified)",
            value="❌ This user has not verified with ILSRP Systems\n\n"
                  "Use `/verify` to link your Roblox account",
            inline=True
        )
    
    # Staff status
    db_staff = await db.get_staff(discord_id=target_user.id, guild_id=guild.id)
    
    if db_staff:
        staff_role = db_staff.get("role", "Staff")
        staff_team = db_staff.get("team", "Unknown")
        
        embed.add_field(
            name="<:staff:1076415080524386324> Staff Team",
            value=f"**Role:** {staff_role}\n"
                  f"**Team:** {staff_team}\n"
                  f"**Joined:** <t:{int(db_staff.get('joined_at', datetime.utcnow()).timestamp())}:R>",
            inline=True
        )
    
    # Server info
    embed.add_field(
        name="<:server:1076415080524386324> Server",
        value=f"**Member Since:** <t:{int(target_user.joined_at.timestamp())}:D>\n"
              f"**Roles:** {roles_text}",
        inline=False
    )
    
    # Footer
    embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
    embed.timestamp = datetime.utcnow()
    
    await interaction.send(embed=embed, ephemeral=False)

# ==================== /VERIFY COMMAND ====================

@bot.slash_command(name="verify", description="Verify your Roblox account")
async def verify(interaction: Interaction):
    """Start the verification process."""
    # Check if already verified
    existing = await db.get_user(discord_id=interaction.user.id)
    
    if existing:
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Already Verified",
            description=f"You are already verified as **@{existing.get('roblox_username')}**!\n\n"
                       f"To update your linked account, use `/unverify` first.",
            color=SIDEBAR_COLOR
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    # Show verification modal
    modal = VerifyModal()
    await interaction.response.send_modal(modal)

# ==================== /UNVERIFY COMMAND ====================

@bot.slash_command(name="unverify", description="Unlink your Roblox account")
async def unverify(interaction: Interaction):
    """Unlink Roblox account from Discord."""
    await interaction.response.defer(ephemeral=True)
    
    # Check if verified
    existing = await db.get_user(discord_id=interaction.user.id)
    
    if not existing:
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Not Verified",
            description="You are not currently verified.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    # Delete verification
    success = await db.delete_user(interaction.user.id)
    
    if success:
        # Remove verified role
        verified_role = nextcord.utils.get(interaction.guild.roles, name="Verified")
        if verified_role:
            await interaction.user.remove_roles(verified_role)
        
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Unverified",
            description="Your Roblox account has been unlinked from your Discord account.",
            color=0x00ff00
        )
        await interaction.send(embed=embed, ephemeral=True)
    else:
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Error",
            description="An error occurred. Please try again later.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)

# ==================== TICKET SYSTEM ====================

# Ticket categories with their properties
TICKET_CATEGORIES = {
    "general": {
        "name": "General Inquiry",
        "emoji": "<:GeneralInquiry:1471679744767426581>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224780317425715/ilsrpgi.png?ex=69a999db&is=69a8485b&hm=f6a80728c4a0db259056ac373c6708d549eacc43ef233ce175a8fe757318d38c&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1471690459251478662,
        "ping_role": "evaluation",  # Lowest staff that can handle
        "min_role": "intern_evaluator"
    },
    "appeal": {
        "name": "Punishment Appeal",
        "emoji": "<:PunishmentAppeal:1471679782818418852>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224780774740118/ilsrppa.png?ex=69a999db&is=69a8485b&hm=2b8ad4a2733659f6bbabd3a96beaf1b09d3c3084fc470505d21bedf26e330ab0&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1471690532714450964,
        "ping_role": "evaluation",
        "min_role": "intern_evaluator"
    },
    "staff_report": {
        "name": "Staff Team Report",
        "emoji": "<:StaffReport:1473438936285052968>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224782162923550/ilsrpstr.png?ex=69a999dc&is=69a8485c&hm=49e912d2cb215643d57bbec53dc042d1b1b31b87e8a5ad7f0910a1b96da53177&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1473508050819223683,
        "ping_role": "supervision",
        "min_role": "intern_supervisor"
    },
    "employment": {
        "name": "Employment Enquiry",
        "emoji": "<:EmploymentEnquiry:1473439147275325511>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224779797463195/ilsrpee.png?ex=69a999db&is=69a8485b&hm=20ba2409ec1850702099ca094153692467a76d74d938bb9c9b8409b6e9b07beb&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1478222898035691560,
        "ping_role": "management",
        "min_role": "intern_manager"
    },
    "partnership": {
        "name": "Server Partnership",
        "emoji": "<:ServerPartnership:1473439109686104134>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224781491830784/ilsrpsp.png?ex=69a999db&is=69a8485b&hm=2727fed75b275ae22216a0d71dd030c738ffdbd08f99f5859c72069074f1d4ba&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1478923656972472420,
        "ping_role": "executive",
        "min_role": "executive"
    },
    "management": {
        "name": "Management Request",
        "emoji": "<:ManagementRequest:1471679839667879956>",
        "banner": "https://media.discordapp.net/attachments/1472412365415776306/1478224779235430450/ilsrpmgr.png?ex=69a999db&is=69a8485b&hm=f7b8801df95757d885b8acdef6f3849f0e8143a82ea672a60992767af5f9eade&=&format=webp&quality=lossless&width=2400&height=1200",
        "transcript_channel": 1471690561655279783,
        "ping_role": "management",
        "min_role": "intern_manager"
    }
}

# Role hierarchy for ticket permissions
ROLE_HIERARCHY = {
    "trial_moderator": 1,
    "junior_moderator": 2,
    "senior_moderator": 3,
    "lead_moderator": 4,
    "trial_administrator": 5,
    "junior_administrator": 6,
    "senior_administrator": 7,
    "lead_administrator": 8,
    "intern_evaluator": 9,
    "junior_evaluator": 10,
    "senior_evaluator": 11,
    "top_evaluator": 12,
    "intern_supervisor": 13,
    "junior_supervisor": 14,
    "senior_supervisor": 15,
    "top_supervisor": 16,
    "intern_manager": 17,
    "junior_manager": 18,
    "senior_manager": 19,
    "top_manager": 20,
    "executive": 21,
    "associate_executive": 22,
    "partner_executive": 23,
    "name_executive": 24,
    "co_owner": 25,
    "owner": 26
}

# Get role IDs from the utilities bot or environment
def get_role_id_from_name(role_name: str, guild) -> int:
    """Get role ID by name."""
    role_mapping = {
        "owner": 1471642523821674618,
        "co_owner": 1471642550271082690,
        "executive": 1471642126663024640,
        "associate_executive": 1471642323657031754,
        "partner_executive": 1471642626863141059,
        "name_executive": 1471642668630020268,
        "top_manager": 1471687503135248625,
        "senior_manager": 1471646332799418601,
        "junior_manager": 1471640133462659236,
        "intern_manager": 1471646520909758666,
        "top_supervisor": 1471646257679171687,
        "senior_supervisor": 1471646221604098233,
        "junior_supervisor": 1471646134098460743,
        "intern_supervisor": 1471640008011026666,
        "top_evaluator": 1472073458321063987,
        "senior_evaluator": 1472073396451020953,
        "junior_evaluator": 1472073148949336215,
        "intern_evaluator": 1472073043554734100,
        "lead_administrator": 1471645738734714982,
        "senior_administrator": 1471645702357520468,
        "junior_administrator": 1471646093287755796,
        "trial_administrator": 1471647027896254557,
        "lead_moderator": 1471642772359479420,
        "senior_moderator": 1471642726796628048,
        "junior_moderator": 1471646011741966517,
        "trial_moderator": 1471646061369098375,
    }
    return role_mapping.get(role_name.lower())

def check_user_role_level(user, min_role_name: str) -> bool:
    """Check if user has required role level for ticket."""
    min_level = ROLE_HIERARCHY.get(min_role_name, 1)
    
    for role in user.roles:
        role_name = role.name.lower().replace(" ", "_")
        if role_name in ROLE_HIERARCHY:
            if ROLE_HIERARCHY[role_name] >= min_level:
                return True
    return False

def get_ping_mention(category: str, guild) -> str:
    """Get the ping mention for a category."""
    category_data = TICKET_CATEGORIES.get(category)
    if not category_data:
        return ""
    
    min_role = category_data.get("min_role", "intern_evaluator")
    role_id = get_role_id_from_name(min_role, guild)
    
    if role_id:
        role = guild.get_role(role_id)
        if role:
            return role.mention
    
    return ""

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Create select menu for ticket categories
        options = []
        for key, cat in TICKET_CATEGORIES.items():
            options.append(ui.SelectOption(
                label=cat["name"],
                value=key,
                emoji=cat["emoji"]
            ))
        
        select = ui.Select(
            placeholder="Select a ticket category",
            options=options,
            custom_id="ticket_category_select"
        )
        select.callback = self.ticket_select_callback
        self.add_item(select)
    
    async def ticket_select_callback(self, interaction: Interaction):
        await interaction.response.defer()
        
        category_key = interaction.data["values"][0]
        category = TICKET_CATEGORIES[category_key]
        
        # Check blacklist
        is_blacklisted = await db.is_blacklisted(
            discord_id=interaction.user.id,
            guild_id=interaction.guild.id
        )
        
        if is_blacklisted:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Blacklisted",
                description="You are blacklisted from creating tickets. Contact staff for assistance.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Create ticket channel
        ticket_number = await db.get_ticket_count(interaction.guild.id) + 1
        channel_name = f"{category['emoji']}-{category['name'].lower().replace(' ', '-')}-{interaction.user.name.lower()}"
        
        # Get category for channel creation
        category_obj = nextcord.utils.get(interaction.guild.categories, name="Tickets")
        if not category_obj:
            category_obj = nextcord.utils.get(interaction.guild.categories, name="SUPPORT")
        
        # Create the ticket channel
        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            interaction.user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        }
        
        # Add role permissions based on category
        for role_name, level in ROLE_HIERARCHY.items():
            role_id = get_role_id_from_name(role_name, interaction.guild)
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    min_level = ROLE_HIERARCHY.get(category.get("min_role", "intern_evaluator"), 1)
                    if level >= min_level:
                        overwrites[role] = nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        try:
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category_obj,
                topic=f"User: {interaction.user} | Category: {category['name']} | ID: {ticket_number}",
                overwrites=overwrites
            )
            
            # Create ticket in database
            await db.create_ticket(
                ticket_id=ticket_number,
                guild_id=interaction.guild.id,
                user_id=interaction.user.id,
                category=category_key,
                channel_id=ticket_channel.id
            )
            
            # Send ticket embed with banner
            embed = nextcord.Embed(
                title=f"{category['emoji']} | {category['name']}",
                description=f"Welcome {interaction.user.mention}!\n\n"
                           f"Please describe your issue and wait for staff to respond.\n\n"
                           f"Ticket ID: `{ticket_number}`",
                color=SIDEBAR_COLOR
            )
            embed.set_image(url=category["banner"])
            
            # Add close button
            close_view = CloseTicketView(ticket_number)
            await ticket_channel.send(
                content=f"{interaction.user.mention} {get_ping_mention(category_key, interaction.guild)}",
                embed=embed,
                view=close_view
            )
            
            # Confirm to user
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Ticket Created",
                description=f"Your ticket has been created: {ticket_channel.mention}\n\n"
                           f"Category: {category['emoji']} {category['name']}",
                color=0x00ff00
            )
            await interaction.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Error",
                description=f"Failed to create ticket: {str(e)}",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)

class CloseTicketView(ui.View):
    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        
        close_button = ui.Button(
            label="Close Ticket",
            style=nextcord.ButtonStyle.danger,
            custom_id=f"close_ticket_{ticket_id}",
            emoji="🔒"
        )
        close_button.callback = self.close_callback
        self.add_item(close_button)
    
    async def close_callback(self, interaction: Interaction):
        await interaction.response.defer()
        
        # Check if user can close (ticket owner or staff)
        ticket = await db.get_ticket(ticket_id=self.ticket_id)
        
        if not ticket:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Error",
                description="Ticket not found.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        user_can_close = (
            interaction.user.id == ticket.get("user_id") or 
            check_user_role_level(interaction.user, "intern_evaluator")
        )
        
        if not user_can_close:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Permission Denied",
                description="Only the ticket owner or staff members can close this ticket.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Close ticket
        await db.close_ticket(self.ticket_id, str(interaction.user))
        
        # Send closing message
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Ticket Closed",
            description=f"This ticket has been closed by {interaction.user.mention}.\n\n"
                       "The transcript will be saved.",
            color=0xff0000
        )
        await interaction.send(embed=embed)
        
        # Move transcript to category channel
        category = ticket.get("category")
        category_data = TICKET_CATEGORIES.get(category, {})
        transcript_channel_id = category_data.get("transcript_channel")
        
        if transcript_channel_id:
            transcript_channel = interaction.guild.get_channel(transcript_channel_id)
            if transcript_channel:
                # Get all messages for transcript
                messages = []
                async for msg in interaction.channel.history(limit=100):
                    if msg.author.bot:
                        continue
                    timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    messages.append(f"[{timestamp}] {msg.author}: {msg.content}")
                
                messages.reverse()
                transcript_text = "\n".join(messages) if messages else "No messages"
                
                # Send transcript
                transcript_embed = nextcord.Embed(
                    title=f"<:ILSRP:1471990869166002291> | Ticket #{self.ticket_id} Transcript",
                    description=f"**Category:** {category_data.get('emoji')} {category_data.get('name')}\n"
                               f"**User:** <@{ticket.get('user_id')}>\n"
                               f"**Closed by:** {interaction.user}",
                    color=SIDEBAR_COLOR
                )
                
                if len(transcript_text) > 4000:
                    # Split into chunks
                    chunks = [transcript_text[i:i+4000] for i in range(0, len(transcript_text), 4000)]
                    for i, chunk in enumerate(chunks):
                        await transcript_channel.send(f"```\n{chunk}\n```")
                else:
                    await transcript_channel.send(embed=transcript_embed)
                    await transcript_channel.send(f"```\n{transcript_text}\n```")
        
        # Delete channel after delay
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except:
            pass

@bot.slash_command(name="ticket", description="Create a support ticket")
async def ticket(interaction: Interaction):
    """Create a support ticket."""
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | Create Support Ticket",
        description="Select a category from the dropdown below to create a support ticket.\n\n"
                   "**Ticket Categories:**\n"
                   f"{TICKET_CATEGORIES['general']['emoji']} General Inquiry - Questions and general support\n"
                   f"{TICKET_CATEGORIES['appeal']['emoji']} Punishment Appeal - Appeal a punishment\n"
                   f"{TICKET_CATEGORIES['staff_report']['emoji']} Staff Team Report - Report a staff member\n"
                   f"{TICKET_CATEGORIES['employment']['emoji']} Employment Enquiry - Apply for department\n"
                   f"{TICKET_CATEGORIES['partnership']['emoji']} Server Partnership - Partner with us\n"
                   f"{TICKET_CATEGORIES['management']['emoji']} Management Request - Management inquiries",
        color=SIDEBAR_COLOR
    )
    
    view = TicketView()
    await interaction.send(embed=embed, view=view, ephemeral=True)

# ==================== TICKET PANEL COMMAND ====================

TICKET_PANEL_CHANNEL_ID = 1471666959753154646  # Assistance channel

@bot.slash_command(name="ticketpanel", description="Send the ticket panel (Admin only)")
async def ticketpanel(interaction: Interaction):
    """Send the ticket panel to the assistance channel."""
    # Check permissions
    if not check_user_role_level(interaction.user, "associate_executive"):
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Permission Denied",
            description="You need to be **Associate Executive** or higher to use this command.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | 🎫 Support Tickets",
        description="Welcome to the ILSRP Support Center!\n\n"
                   "Select a category below to create a ticket. Our staff team will assist you as soon as possible.\n\n"
                   "**How it works:**\n"
                   "1. Select a category from the dropdown\n"
                   "2. Describe your issue\n"
                   "3. Wait for staff to respond\n\n"
                   "**Categories:",
        color=SIDEBAR_COLOR
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png")
    
    view = TicketView()
    
    # Send to the assistance channel
    channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed, view=view)
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Ticket Panel Sent",
            description="The ticket panel has been sent to the assistance channel.",
            color=0x00ff00
        )
        await interaction.send(embed=embed, ephemeral=True)
    else:
        await interaction.send(f"Channel not found: {TICKET_PANEL_CHANNEL_ID}", ephemeral=True)

# ==================== BLACKLIST COMMANDS ====================

@bot.slash_command(name="blacklist", description="Blacklist management")
async def blacklist(interaction: Interaction):
    """Blacklist management menu."""
    # Check permissions
    if not check_user_role_level(interaction.user, "associate_executive"):
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Permission Denied",
            description="You need to be **Associate Executive** or higher to manage the blacklist.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    view = BlacklistView()
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | Blacklist Management",
        description="Select an option below:",
        color=SIDEBAR_COLOR
    )
    await interaction.send(embed=embed, view=view, ephemeral=True)

class BlacklistView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        select = ui.Select(
            placeholder="Select an option",
            options=[
                ui.SelectOption(label="Add to Blacklist", description="Blacklist a user", emoji="🚫"),
                ui.SelectOption(label="Remove from Blacklist", description="Remove a user from blacklist", emoji="✅"),
                ui.SelectOption(label="View Blacklist", description="View all blacklisted users", emoji="📋")
            ]
        )
        select.callback = self.blacklist_callback
        self.add_item(select)
    
    async def blacklist_callback(self, interaction: Interaction):
        value = interaction.data["values"][0]
        
        if value == "Add to Blacklist":
            modal = BlacklistAddModal()
            await interaction.response.send_modal(modal)
        elif value == "Remove from Blacklist":
            modal = BlacklistRemoveModal()
            await interaction.response.send_modal(modal)
        elif value == "View Blacklist":
            await interaction.response.defer(ephemeral=True)
            blacklist = await db.get_blacklist(interaction.guild.id)
            
            if not blacklist:
                embed = nextcord.Embed(
                    title="<:ILSRP:1471990869166002291> | Blacklist",
                    description="No blacklisted users.",
                    color=SIDEBAR_COLOR
                )
                await interaction.send(embed=embed, ephemeral=True)
                return
            
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Blacklisted Users",
                color=SIDEBAR_COLOR
            )
            
            for item in blacklist[:10]:
                user_mention = f"<@{item.get('discord_id')}>" if item.get('discord_id') else "Unknown"
                embed.add_field(
                    name=f"User",
                    value=f"{user_mention}\n"
                          f"Reason: {item.get('reason', 'No reason')}\n"
                          f"Added by: {item.get('added_by', 'Unknown')}\n"
                          f"Date: <t:{int(item.get('added_at').timestamp())}:R>",
                    inline=False
                )
            
            await interaction.send(embed=embed, ephemeral=True)

class BlacklistAddModal(ui.Modal):
    def __init__(self):
        super().__init__("Add to Blacklist")
        
        self.user_id = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter the user's ID or @mention",
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.reason = ui.TextInput(
            label="Reason",
            placeholder="Reason for blacklisting",
            style=nextcord.TextInputStyle.paragraph,
            required=True
        )
        self.add_item(self.user_id)
        self.add_item(self.reason)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Parse user ID
        user_input = self.user_id.value
        user_id = None
        
        if user_input.startswith("<@"):
            user_id = int(user_input.replace("<@", "").replace("!", "").replace(">", ""))
        else:
            try:
                user_id = int(user_input)
            except:
                pass
        
        if not user_id:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Invalid User",
                description="Please provide a valid user ID or @mention.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Add to blacklist
        success = await db.add_blacklist(
            discord_id=user_id,
            guild_id=interaction.guild.id,
            reason=self.reason.value,
            added_by=str(interaction.user)
        )
        
        if success:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Blacklisted",
                description=f"User <@{user_id}> has been blacklisted.\n\nReason: {self.reason.value}",
                color=0x00ff00
            )
        else:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Error",
                description="Failed to blacklist user.",
                color=0xff0000
            )
        await interaction.send(embed=embed, ephemeral=True)

class BlacklistRemoveModal(ui.Modal):
    def __init__(self):
        super().__init__("Remove from Blacklist")
        
        self.user_id = ui.TextInput(
            label="User ID or @mention",
            placeholder="Enter the user's ID or @mention",
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.user_id)
    
    async def callback(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Parse user ID
        user_input = self.user_id.value
        user_id = None
        
        if user_input.startswith("<@"):
            user_id = int(user_input.replace("<@", "").replace("!", "").replace(">", ""))
        else:
            try:
                user_id = int(user_input)
            except:
                pass
        
        if not user_id:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Invalid User",
                description="Please provide a valid user ID or @mention.",
                color=0xff0000
            )
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        # Remove from blacklist
        success = await db.remove_blacklist(discord_id=user_id)
        
        if success:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Removed",
                description=f"User <@{user_id}> has been removed from the blacklist.",
                color=0x00ff00
            )
        else:
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Not Found",
                description="User was not in the blacklist.",
                color=0xff0000
            )
        await interaction.send(embed=embed, ephemeral=True)

# ==================== TICKET CONFIG COMMAND ====================

@bot.slash_command(name="ticketconfig", description="Configure ticket system (Admin only)")
async def ticketconfig(interaction: Interaction):
    """Configure ticket system settings."""
    # Check permissions
    if not check_user_role_level(interaction.user, "associate_executive"):
        embed = nextcord.Embed(
            title="<:ILSRP:1471990869166002291> | Permission Denied",
            description="You need to be **Associate Executive** or higher to configure the ticket system.",
            color=0xff0000
        )
        await interaction.send(embed=embed, ephemeral=True)
        return
    
    view = TicketConfigView()
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | Ticket Configuration",
        description="Select a configuration option:",
        color=SIDEBAR_COLOR
    )
    await interaction.send(embed=embed, view=view, ephemeral=True)

class TicketConfigView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        select = ui.Select(
            placeholder="Select an option",
            options=[
                ui.SelectOption(label="View Stats", description="View ticket statistics", emoji="📊"),
                ui.SelectOption(label="Open Tickets", description="View all open tickets", emoji="🎫"),
                ui.SelectOption(label="Reset Panel", description="Reset the ticket panel", emoji="🔄")
            ]
        )
        select.callback = self.config_callback
        self.add_item(select)
    
    async def config_callback(self, interaction: Interaction):
        value = interaction.data["values"][0]
        
        if value == "View Stats":
            await interaction.response.defer(ephemeral=True)
            stats = await db.get_category_stats(interaction.guild.id)
            
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Ticket Statistics",
                color=SIDEBAR_COLOR
            )
            
            total_tickets = await db.get_ticket_count(interaction.guild.id)
            embed.description = f"**Total Tickets:** {total_tickets}\n\n"
            
            for stat in stats:
                cat = TICKET_CATEGORIES.get(stat["_id"], {})
                embed.add_field(
                    name=f"{cat.get('emoji', '')} {cat.get('name', stat['_id'])}",
                    value=f"Total: {stat['total']} | Open: {stat['open']} | Closed: {stat['closed']}",
                    inline=False
                )
            
            await interaction.send(embed=embed, ephemeral=True)
        
        elif value == "Open Tickets":
            await interaction.response.defer(ephemeral=True)
            tickets = await db.get_open_tickets(interaction.guild.id)
            
            if not tickets:
                embed = nextcord.Embed(
                    title="<:ILSRP:1471990869166002291> | Open Tickets",
                    description="No open tickets.",
                    color=SIDEBAR_COLOR
                )
                await interaction.send(embed=embed, ephemeral=True)
                return
            
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | Open Tickets",
                color=SIDEBAR_COLOR
            )
            
            for ticket in tickets[:10]:
                cat = TICKET_CATEGORIES.get(ticket.get("category"), {})
                channel = interaction.guild.get_channel(ticket.get("channel_id"))
                user = interaction.guild.get_member(ticket.get("user_id"))
                
                embed.add_field(
                    name=f"Ticket #{ticket.get('ticket_id')}",
                    value=f"Category: {cat.get('emoji', '')} {cat.get('name', 'Unknown')}\n"
                          f"User: {user.mention if user else 'Unknown'}\n"
                          f"Channel: {channel.mention if channel else 'Deleted'}\n"
                          f"Status: {ticket.get('status', 'open')}",
                    inline=False
                )
            
            await interaction.send(embed=embed, ephemeral=True)
        
        elif value == "Reset Panel":
            # Send new ticket panel
            embed = nextcord.Embed(
                title="<:ILSRP:1471990869166002291> | 🎫 Support Tickets",
                description="Select a category from the dropdown below to create a support ticket.",
                color=SIDEBAR_COLOR
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png")
            
            view = TicketView()
            
            channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed, view=view)
                embed = nextcord.Embed(
                    title="<:ILSRP:1471990869166002291> | Panel Reset",
                    description="The ticket panel has been reset.",
                    color=0x00ff00
                )
            else:
                embed = nextcord.Embed(
                    title="<:ILSRP:1471990869166002291> | Error",
                    description="Channel not found.",
                    color=0xff0000
                )
            await interaction.send(embed=embed, ephemeral=True)

# ==================== VERIFICATION MESSAGE ====================

async def send_verification_message():
    """Send verification message to the verification channel."""
    channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if not channel:
        logger.error(f"Verification channel {VERIFY_CHANNEL_ID} not found")
        return
    
    embed = nextcord.Embed(
        title="<:ILSRP:1471990869166002291> | Verify with ILSRP Systems",
        description="Welcome to Illinois State Roleplay!\n\n"
                   "To get full community access, verify your account by linking your Roblox account.\n\n"
                   "**How to verify:**\n"
                   "1. Click the button below\n"
                   "2. Enter your Roblox username\n"
                   "3. Complete the verification\n\n"
                   "This links your Discord account to your Roblox account for community access.",
        color=SIDEBAR_COLOR
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png")
    
    view = VerifyView()
    await channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    """Bot is ready and logged in."""
    logger.info(f'Bot logged in as {bot.user}')
    
    # Connect to database
    await db.connect()
    
    # Start the member count update task
    if not membercount_task.is_running():
        membercount_task.start()
    
    # Do initial member count update
    await update_membercount()
    
    # Send verification message (only once)
    # Uncomment below after testing
    # await send_verification_message()

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

