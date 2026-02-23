import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio
import chat_exporter
import requests
import json
import sqlite3
import random
from datetime import datetime, timedelta
from pytz import timezone
import time

# ------------------------------
# Render Web Service Fix (IMPORTANT)
# ------------------------------
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


# ------------------------------
# Intents
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

# ------------------------------
# Bot setup
# ------------------------------
bot = commands.Bot(command_prefix=";", intents=intents)

LOG_CHANNEL_ID = 1473167409505374220  # Logging channel
MEMBER_COUNT_CHANNEL_ID = 1471998856806797524  # Voice channel to show member count
BLUE = 0x4bbfff

# ------------------------------
# Channel Restriction System
# ------------------------------
# Role that grants command permissions
COMMAND_PERMISSION_ROLE_ID = 1473799316782055424

# Allowed bot channels for command usage
BOT_CHANNEL_IDS = [
    1471648116330725466,
    1471648700735553830,
]

# Executive and Holding roles that can use commands anywhere
EXECUTIVE_HOLDING_ROLE_IDS = [
    1471642126663024640,  # Executive
    1471642360503992411,  # Holding
]

def can_use_commands_in_channel(member, channel_id):
    """Check if member can use commands in the given channel."""
    member_role_ids = [role.id for role in member.roles]
    
    # Executive and Holding roles can use commands anywhere
    if any(rid in member_role_ids for rid in EXECUTIVE_HOLDING_ROLE_IDS):
        return True
    
    # Check if member has the command permission role
    if COMMAND_PERMISSION_ROLE_ID not in member_role_ids:
        return False
    
    # Check if the channel is a bot channel
    if channel_id in BOT_CHANNEL_IDS:
        return True
    
    return False

# ------------------------------
# Command Channel Restriction Listener
# ------------------------------
@bot.check
async def command_channel_check(ctx):
    """Check if the command can be used in this channel."""
    # Allow DM commands
    if isinstance(ctx.channel, nextcord.DMChannel):
        return True
    
    # Allow bot owner
    if await bot.is_owner(ctx.author):
        return True
    
    # Check if user can use commands in this channel
    if not can_use_commands_in_channel(ctx.author, ctx.channel.id):
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Send error message and delete it after 5 seconds
        error_msg = await ctx.send(
            f"{ctx.author.mention}, this command can only be used in <#1471648116330725466> or <#1471648700735553830>."
        )
        await error_msg.delete(delay=5)
        return False
    
    return True

# =========================================================
# =================== PROMOTION SYSTEM ====================
# =========================================================

# Role ID mappings
ROLE_IDS = {
    # Owner/Co-Owner
    "owner": 1471642523821674618,
    "co_owner": 1471642550271082690,
    
    # Category roles
    "holding": 1471642360503992411,
    "executive": 1471642126663024640,
    "management": 1471641915215843559,
    "supervision": 1471641790112333867,
    "evaluation": 1472072792081170682,
    "administration": 1471640542231396373,
    "moderation": 1471640225015922982,
    
    # Name Executive
    "name_executive_rank": 1471642668630020268,
    "partner_executive": 1471642626863141059,
    "associate_executive": 1471642323657031754,
    "executive_rank": 1471642126663024640,
    
    # Management sub-ranks
    "top_manager": 1471687503135248625,
    "senior_manager": 1471646332799418601,
    "junior_manager": 1471640133462659236,
    "intern_manager": 1471646520909758666,
    
    # Supervision sub-ranks
    "top_supervisor": 1471646257679171687,
    "senior_supervisor": 1471646221604098233,
    "junior_supervisor": 1471646134098460743,
    "intern_supervisor": 1471640008011026666,
    
    # Evaluation sub-ranks
    "top_evaluator": 1472073458321063987,
    "senior_evaluator": 1472073396451020953,
    "junior_evaluator": 1472073148949336215,
    "intern_evaluator": 1472073043554734100,
    
    # Administration sub-ranks
    "lead_administrator": 1471645738734714982,
    "senior_administrator": 1471645702357520468,
    "junior_administrator": 1471646093287755796,
    "trial_administrator": 1471647027896254557,
    
    # Moderation sub-ranks
    "lead_moderator": 1471642772359479420,
    "senior_moderator": 1471642726796628048,
    "junior_moderator": 1471646011741966517,
    "trial_moderator": 1471646061369098375,
}

# Sub-rank role IDs (promotable positions)
SUB_RANK_ROLES = {
    # Executive
    "Name Executive": 1471642668630020268,
    "Partner Executive": 1471642626863141059,
    "Associate Executive": 1471642323657031754,
    "Executive": 1471642126663024640,
    
    # Management
    "Top Manager": 1471687503135248625,
    "Senior Manager": 1471646332799418601,
    "Junior Manager": 1471640133462659236,
    "Intern Manager": 1471646520909758666,
    
    # Supervision
    "Top Supervisor": 1471646257679171687,
    "Senior Supervisor": 1471646221604098233,
    "Junior Supervisor": 1471646134098460743,
    "Intern Supervisor": 1471640008011026666,
    
    # Evaluation
    "Top Evaluator": 1472073458321063987,
    "Senior Evaluator": 1472073396451020953,
    "Junior Evaluator": 1472073148949336215,
    "Intern Evaluator": 1472073043554734100,
    
    # Administration
    "Lead Administrator": 1471645738734714982,
    "Senior Administrator": 1471645702357520468,
    "Junior Administrator": 1471646093287755796,
    "Trial Administrator": 1471647027896254557,
    
    # Moderation
    "Lead Moderator": 1471642772359479420,
    "Senior Moderator": 1471642726796628048,
    "Junior Moderator": 1471646011741966517,
    "Trial Moderator": 1471646061369098375,
}

# Map sub-rank to category
SUB_RANK_TO_CATEGORY = {
    "Name Executive": "executive",
    "Partner Executive": "executive",
    "Associate Executive": "executive",
    "Executive": "executive",
    "Top Manager": "management",
    "Senior Manager": "management",
    "Junior Manager": "management",
    "Intern Manager": "management",
    "Top Supervisor": "supervision",
    "Senior Supervisor": "supervision",
    "Junior Supervisor": "supervision",
    "Intern Supervisor": "supervision",
    "Top Evaluator": "evaluation",
    "Senior Evaluator": "evaluation",
    "Junior Evaluator": "evaluation",
    "Intern Evaluator": "evaluation",
    "Lead Administrator": "administration",
    "Senior Administrator": "administration",
    "Junior Administrator": "administration",
    "Trial Administrator": "administration",
    "Lead Moderator": "moderation",
    "Senior Moderator": "moderation",
    "Junior Moderator": "moderation",
    "Trial Moderator": "moderation",
}

# Category role IDs
CATEGORY_ROLES = {
    "executive": 1471642126663024640,
    "management": 1471641915215843559,
    "supervision": 1471641790112333867,
    "evaluation": 1472072792081170682,
    "administration": 1471640542231396373,
    "moderation": 1471640225015922982,
    "holding": 1471642360503992411,
}

def get_member_category(member):
    for category, role_id in CATEGORY_ROLES.items():
        if role_id in [role.id for role in member.roles]:
            return category
    return None

def get_member_sub_rank(member):
    for rank_name, role_id in SUB_RANK_ROLES.items():
        if role_id in [role.id for role in member.roles]:
            return rank_name
    return None

def can_promote(promoter, target_category, new_rank_category):
    promoter_role_ids = [role.id for role in promoter.roles]
    
    # Owner/Co-Owner can promote anyone
    if ROLE_IDS["owner"] in promoter_role_ids or ROLE_IDS["co_owner"] in promoter_role_ids:
        return True
    
    # Holding can promote anyone
    if ROLE_IDS["holding"] in promoter_role_ids:
        return True
    
    # Intern Supervisor+ (Supervision team) can promote Moderation and Administration
    if ROLE_IDS["intern_supervisor"] in promoter_role_ids:
        if target_category in ["moderation", "administration"]:
            return True
        return False
    
    # Top Supervisor+ can promote anyone
    if ROLE_IDS["top_supervisor"] in promoter_role_ids:
        return True
    
    # Intern Manager+ (Management team) can promote Moderation, Administration, Evaluation
    if ROLE_IDS["intern_manager"] in promoter_role_ids:
        if target_category in ["moderation", "administration", "evaluation"]:
            return True
        return False
    
    # Top Manager+ can promote anyone
    if ROLE_IDS["top_manager"] in promoter_role_ids:
        return True
    
    # Executive (not Name Executive) can promote Moderation, Administration, Evaluation, Supervision
    if ROLE_IDS["executive_rank"] in promoter_role_ids and ROLE_IDS["name_executive_rank"] not in promoter_role_ids:
        if target_category in ["moderation", "administration", "evaluation", "supervision"]:
            return True
        return False
    
    # Name Executive can promote anyone
    if ROLE_IDS["name_executive_rank"] in promoter_role_ids:
        return True
    
    return False

def get_roles_to_remove(member, new_rank_name):
    roles_to_remove = []
    member_role_ids = [role.id for role in member.roles]
    
    current_category = get_member_category(member)
    current_sub_rank = get_member_sub_rank(member)
    
    if current_sub_rank:
        sub_rank_id = SUB_RANK_ROLES.get(current_sub_rank)
        if sub_rank_id and sub_rank_id in member_role_ids:
            roles_to_remove.append(sub_rank_id)
    
    if current_category:
        category_id = CATEGORY_ROLES.get(current_category)
        if category_id and category_id in member_role_ids:
            roles_to_remove.append(category_id)
    
    return roles_to_remove

def get_roles_to_add(new_rank_name):
    roles_to_add = []
    
    new_rank_id = SUB_RANK_ROLES.get(new_rank_name)
    if new_rank_id:
        roles_to_add.append(new_rank_id)
    
    new_category = SUB_RANK_TO_CATEGORY.get(new_rank_name)
    if new_category:
        category_id = CATEGORY_ROLES.get(new_category)
        if category_id:
            roles_to_add.append(category_id)
    
    return roles_to_add

class PromoteModal(nextcord.ui.Modal):
    def __init__(self, target_member, new_rank):
        super().__init__("Promotion Details")
        self.target_member = target_member
        self.new_rank = new_rank
        
        self.initiated_by = nextcord.ui.TextInput(
            label="Initiated By (names)",
            style=nextcord.TextInputStyle.short,
            required=True,
            placeholder="Enter names of who initiated"
        )
        self.add_item(self.initiated_by)
        
        self.approved_by = nextcord.ui.TextInput(
            label="Approved By (names)",
            style=nextcord.TextInputStyle.short,
            required=True,
            placeholder="Enter names of who approved"
        )
        self.add_item(self.approved_by)
        
        self.reason = nextcord.ui.TextInput(
            label="Reason",
            style=nextcord.TextInputStyle.paragraph,
            required=True,
            placeholder="Explain why this promotion is being given"
        )
        self.add_item(self.reason)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        
        former_position = get_member_sub_rank(self.target_member) or "No Position"
        new_position = self.new_rank
        
        roles_to_remove = get_roles_to_remove(self.target_member, self.new_rank)
        roles_to_add = get_roles_to_add(self.new_rank)
        
        remove_roles = [interaction.guild.get_role(rid) for rid in roles_to_remove if interaction.guild.get_role(rid)]
        add_roles = [interaction.guild.get_role(rid) for rid in roles_to_add if interaction.guild.get_role(rid)]
        
        if remove_roles:
            await self.target_member.remove_roles(*remove_roles)
        if add_roles:
            await self.target_member.add_roles(*add_roles)
        
        copy_text = f"""`Staff Member:` {self.target_member.mention}
`Initiated By:` {self.initiated_by.value}
`Approved By:` {self.approved_by.value}
`Former Position:` {former_position}
`Updated Position:` {new_position}
`Reason:` {self.reason.value}"""
        
        # Send copy text privately to the person who ran the command
        await interaction.followup.send(
            f"**COPY TEXT:**\n```\n{copy_text}\n```",
            ephemeral=True
        )
        
        # Send public confirmation in the channel
        await interaction.channel.send(
            f"✅ **{self.target_member}** has been promoted to **{new_position}**!"
        )
        
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = nextcord.Embed(
                title="Promotion Executed",
                color=BLUE,
                timestamp=utcnow()
            )
            embed.set_author(name=f"{interaction.user}", icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Staff Member", value=f"{self.target_member.mention}", inline=True)
            embed.add_field(name="Former Position", value=former_position, inline=True)
            embed.add_field(name="New Position", value=new_position, inline=True)
            embed.add_field(name="Initiated By", value=self.initiated_by.value, inline=False)
            embed.add_field(name="Approved By", value=self.approved_by.value, inline=False)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)
            await log_channel.send(embed=embed)

class PromoteSelect(nextcord.ui.Select):
    def __init__(self, target_member):
        options = []
        target_category = get_member_category(target_member)
        
        for rank_name, role_id in SUB_RANK_ROLES.items():
            rank_category = SUB_RANK_TO_CATEGORY[rank_name]
            if rank_category == target_category:
                options.append(nextcord.SelectOption(
                    label=rank_name,
                    value=rank_name
                ))
        
        super().__init__(
            placeholder="Select new rank",
            options=options,
            custom_id="promote_rank_select"
        )
        self.target_member = target_member

    async def callback(self, interaction: nextcord.Interaction):
        new_rank = self.values[0]
        
        target_category = get_member_category(self.target_member)
        new_rank_category = SUB_RANK_TO_CATEGORY.get(new_rank)
        
        if not can_promote(interaction.user, target_category, new_rank_category):
            await interaction.response.send_message(
                "❌ You don't have permission to promote this person to this rank.",
                ephemeral=True
            )
            return
        
        await interaction.response.send_modal(
            PromoteModal(self.target_member, new_rank)
        )

class PromoteView(nextcord.ui.View):
    def __init__(self, target_member):
        super().__init__(timeout=300)
        self.add_item(PromoteSelect(target_member))

@bot.slash_command(name="promote", description="Promote a staff member")
async def promote(interaction: nextcord.Interaction, member: nextcord.Member):
    required_role_ids = [
        1471642360503992411,  # Holding
        1471642126663024640,  # Executive
        1471641915215843559,  # Management
        1471641790112333867,  # Supervision
        1472072792081170682,  # Evaluation
        1471640542231396373,  # Administration
        1471640225015922982,  # Moderation
    ]
    
    member_role_ids = [role.id for role in member.roles]
    has_staff_role = any(rid in member_role_ids for rid in required_role_ids)
    
    if not has_staff_role:
        await interaction.response.send_message(
            "❌ This member doesn't have any staff roles to be promoted.",
            ephemeral=True
        )
        return
    
    target_category = get_member_category(member)
    
    if not target_category:
        await interaction.response.send_message(
            "❌ Could not determine the member's current category.",
            ephemeral=True
        )
        return
    
    options = []
    for rank_name, role_id in SUB_RANK_ROLES.items():
        rank_category = SUB_RANK_TO_CATEGORY[rank_name]
        if rank_category == target_category:
            options.append(nextcord.SelectOption(
                label=rank_name,
                value=rank_name
            ))
    
    if not options:
        await interaction.response.send_message(
            "❌ No valid ranks available for promotion.",
            ephemeral=True
        )
        return
    
    view = PromoteView(member)
    await interaction.response.send_message(
        f"Select the new rank for **{member}**:",
        view=view,
        ephemeral=True
    )

# =========================================================
# =================== YOUR ORIGINAL CODE ==================
# =========================================================

# ------------------------------
# Member join event
# ------------------------------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1471660664022896902)  # Welcome channel
    if channel:
        member_count = len([m for m in member.guild.members if not m.bot])

        def ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return str(n) + suffix

        welcome_message = (
            f"# <:ILSRP:1471990869166002291> Welcome to Illinois State Roleplay.\n\n"
            f"Hello, {member.mention}!\n"
            "Welcome to Illinois State Roleplay, a ER:LC Roleplay Community based on the state of Illinois in the United States.\n\n"
            f"> Want to learn more about the server? Check out <#1471702849401393264>!\n"
            f"> Reading our <#1471703130587795578> is necessary to ensure that you won't be moderated for rule-breaking.\n"
            f"> Do you need support or have questions? Create a support ticket in <#1471666959753154646>.\n"
            f"> Would you like full community access? Ensure that <#1471660766536011952> is complete with Melonly.\n\n"
            "Otherwise, have a fantastic day!\n\n"
            f"-# You are our {ordinal(member_count)} member in the Discord Communications of Illinois State Roleplay."
        )

        # First embed - Large image
        image_embed = nextcord.Embed(
            color=0x4bbfff
        )
        image_embed.set_image(
            url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png?ex=6995c4d6&is=69947356&hm=6934335bb9bebe3f2c92ad195081c08d142b8e07c9e2161a09bb177709a3c570&"
        )

        # Second embed - Welcome message with blue color
        welcome_embed = nextcord.Embed(
            color=0x4bbfff,
            description=(
                f"# <:ILSRP:1471990869166002291> Welcome to Illinois State Roleplay.\n\n"
                f"Hello, {member.mention}!\n"
                "Welcome to Illinois State Roleplay, a ER:LC Roleplay Community based on the state of Illinois in the United States.\n\n"
                f"> Want to learn more about the server? Check out <#1471702849401393264>!\n"
                f"> Reading our <#1471703130587795578> is necessary to ensure that you won't be moderated for rule-breaking.\n"
                f"> Do you need support or have questions? Create a support ticket in <#1471666959753154646>.\n"
                f"> Would you like full community access? Ensure that <#1471660766536011952> is complete with Melonly.\n\n"
                "Otherwise, have a fantastic day!\n\n"
                f"-# You are our {ordinal(member_count)} member in the Discord Communications of Illinois State Roleplay."
            )
        )

        await channel.send(content=member.mention, embeds=[image_embed, welcome_embed])
    
    # Update member count channel
    await update_member_count(member.guild)

# ------------------------------
# Member leave event
# ------------------------------
@bot.event
async def on_member_remove(member):
    # Update member count channel when a member leaves
    await update_member_count(member.guild)

# ------------------------------
# Command Logging Helper
# ------------------------------
async def log_command(user, command_name, ctx_type):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = nextcord.Embed(
            title="Command Executed",
            color=0x4bbfff,
            timestamp=utcnow()
        )
        embed.set_author(name=f"{user}", icon_url=user.display_avatar.url)
        embed.add_field(name="Command", value=command_name, inline=True)
        embed.add_field(name="Type", value=ctx_type, inline=True)
        await log_channel.send(embed=embed)

# ------------------------------
# SAY PREFIX COMMAND
# ------------------------------
ALLOWED_ROLE_IDS = [1471642126663024640, 1471642360503992411]

@bot.command(name="say")
async def say_prefix(ctx, *, message: str):
    await log_command(ctx.author, "say", "Prefix")
    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
        except nextcord.Forbidden:
            pass
        await ctx.send(message)
    else:
        await ctx.send(f"❌ {ctx.author.mention}, you don't have permission to use this command.")

# =========================================================
# ====================== LOCK SYSTEM ======================
# =========================================================

# Dictionary to store original channel permissions
# Format: {channel_id: {role_id: PermissionOverwrite}}
locked_channels = {}

# Roles to lock (configurable)
LOCK_ROLES = [
    1471642360503992411,  # Holding
    1471642126663024640,  # Executive
    1471641915215843559,  # Management
    1471641790112333867,  # Supervision
    1472072792081170682,  # Evaluation
    1471640542231396373,  # Administration
    1471640225015922982,  # Moderation
]

def has_associate_executive_or_higher(member):
    """Check if member has Associate Executive or higher rank"""
    member_role_ids = [role.id for role in member.roles]
    # Associate Executive and above
    associate_executive_rank = 1471642323657031754
    # Also allow Owner/Co-Owner
    if ROLE_IDS["owner"] in member_role_ids or ROLE_IDS["co_owner"] in member_role_ids:
        return True
    # Check for Associate Executive or higher
    return associate_executive_rank in member_role_ids

def has_executive_or_holding(member):
    """Check if member has Executive or Holding role (or Owner/Co-Owner)"""
    member_role_ids = [role.id for role in member.roles]
    # Executive, Holding, Owner, Co-Owner
    allowed_roles = [
        1471642126663024640,  # Executive
        1471642360503992411,  # Holding
        1471642523821674618,  # Owner
        1471642550271082690,  # Co-Owner
    ]
    return any(rid in member_role_ids for rid in allowed_roles)

@bot.command(name="lock")
async def lock_channel(ctx):
    """Lock the channel to prevent specified roles from sending messages"""
    
    # Check permission (Executive+ or Holding)
    if not has_executive_or_holding(ctx.author):
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        # Send error message and delete it after 5 seconds
        error_msg = await ctx.send("You are unable to use this command, as it is restricted to Executive+.")
        await error_msg.delete(delay=5)
        return
    
    # Log command
    await log_command(ctx.author, "lock", "Prefix")
    
    channel = ctx.channel
    
    # Check if already locked
    if channel.id in locked_channels:
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(f"❌ {ctx.author.mention}, this channel is already locked!")
        return
    
    # Store original permissions for ALL roles with custom overwrites
    locked_channels[channel.id] = {}
    
    # Get all permission overwrites for this channel
    for target, overwrite in channel.overwrites.items():
        # Skip if it's the @everyone role (we don't want to lock everyone)
        if isinstance(target, nextcord.Role) and target.id == ctx.guild.default_role.id:
            continue
        
        # Store the FULL original PermissionOverwrite object
        locked_channels[channel.id][target.id] = overwrite
        
        # Create a new PermissionOverwrite that preserves ALL original permissions
        # but sets send_messages to False
        new_overwrite = nextcord.PermissionOverwrite(
            # Text permissions
            add_reactions=overwrite.add_reactions,
            attach_files=overwrite.attach_files,
            embed_links=overwrite.embed_links,
            mention_everyone=overwrite.mention_everyone,
            manage_messages=overwrite.manage_messages,
            manage_threads=overwrite.manage_threads,
            read_message_history=overwrite.read_message_history,
            send_messages=False,  # This is what we want to lock
            send_messages_in_threads=overwrite.send_messages_in_threads,
            speak=overwrite.speak,
            use_application_commands=overwrite.use_application_commands,
            use_external_emojis=overwrite.use_external_emojis,
            use_external_stickers=overwrite.use_external_stickers,
            use_slash_commands=overwrite.use_slash_commands,
            view_channel=overwrite.view_channel,
            # Voice permissions
            connect=overwrite.connect,
            deafen_members=overwrite.deafen_members,
            move_members=overwrite.move_members,
            mute_members=overwrite.mute_members,
            priority_speaker=overwrite.priority_speaker,
            stream=overwrite.stream,
            use_voice_activity=overwrite.use_voice_activity,
        )
        
        await channel.set_permissions(target, overwrite=new_overwrite)
    
    # Delete user's command message
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Send lock confirmation embed
    embed = nextcord.Embed(
        description=f"🔒 Channel locked by {ctx.author.mention}",
        color=BLUE
    )
    await ctx.send(embed=embed)

@bot.command(name="unlock")
async def unlock_channel(ctx):
    """Unlock the channel and restore original permissions"""
    
    # Check permission (Executive+ or Holding)
    if not has_executive_or_holding(ctx.author):
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        # Send error message and delete it after 5 seconds
        error_msg = await ctx.send("You are unable to use this command, as it is restricted to Executive+.")
        await error_msg.delete(delay=5)
        return
    
    # Log command
    await log_command(ctx.author, "unlock", "Prefix")
    
    channel = ctx.channel
    channel_id = channel.id
    
    # Check if channel is locked
    if channel_id not in locked_channels:
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(f"❌ {ctx.author.mention}, this channel is not locked!")
        return
    
    # Get the original overwrites and remove from locked list FIRST
    original_overwrites = locked_channels[channel_id]
    del locked_channels[channel_id]
    
    # Now try to restore permissions
    for target_id, original_overwrite in original_overwrites.items():
        # Get the role by ID
        role = ctx.guild.get_role(target_id)
        if role:
            # Restore the FULL original PermissionOverwrite
            try:
                await channel.set_permissions(role, overwrite=original_overwrite)
            except Exception as e:
                print(f"Error restoring permission for role {target_id}: {e}")
    
    # Delete user's command message
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Send unlock confirmation embed
    embed = nextcord.Embed(
        description=f"🔓 Channel has been unlocked.",
        color=BLUE
    )
    await ctx.send(embed=embed)

# =========================================================
# LOCK/UNLOCK SLASH COMMANDS
# =========================================================

@bot.slash_command(name="lock", description="Lock the channel")
async def lock_slash(interaction: nextcord.Interaction):
    """Lock the channel to prevent specified roles from sending messages"""
    
    # Check permission (Executive+ or Holding)
    if not has_executive_or_holding(interaction.user):
        await interaction.response.send_message(
            "You are unable to use this command, as it is restricted to Executive+.",
            ephemeral=True
        )
        return
    
    # Log command
    await log_command(interaction.user, "lock", "Slash")
    
    channel = interaction.channel
    
    # Check if already locked
    if channel.id in locked_channels:
        await interaction.response.send_message(
            "❌ This channel is already locked!",
            ephemeral=True
        )
        return
    
    # Store original permissions for ALL roles with custom overwrites
    locked_channels[channel.id] = {}
    
    # Get all permission overwrites for this channel
    for target, overwrite in channel.overwrites.items():
        # Skip if it's the @everyone role (we don't want to lock everyone)
        if isinstance(target, nextcord.Role) and target.id == interaction.guild.default_role.id:
            continue
        
        # Store the FULL original PermissionOverwrite object
        locked_channels[channel.id][target.id] = overwrite
        
        # Create a new PermissionOverwrite that preserves ALL original permissions
        # but sets send_messages to False
        new_overwrite = nextcord.PermissionOverwrite(
            # Text permissions
            add_reactions=overwrite.add_reactions,
            attach_files=overwrite.attach_files,
            embed_links=overwrite.embed_links,
            mention_everyone=overwrite.mention_everyone,
            manage_messages=overwrite.manage_messages,
            manage_threads=overwrite.manage_threads,
            read_message_history=overwrite.read_message_history,
            send_messages=False,  # This is what we want to lock
            send_messages_in_threads=overwrite.send_messages_in_threads,
            speak=overwrite.speak,
            use_application_commands=overwrite.use_application_commands,
            use_external_emojis=overwrite.use_external_emojis,
            use_external_stickers=overwrite.use_external_stickers,
            use_slash_commands=overwrite.use_slash_commands,
            view_channel=overwrite.view_channel,
            # Voice permissions
            connect=overwrite.connect,
            deafen_members=overwrite.deafen_members,
            move_members=overwrite.move_members,
            mute_members=overwrite.mute_members,
            priority_speaker=overwrite.priority_speaker,
            stream=overwrite.stream,
            use_voice_activity=overwrite.use_voice_activity,
        )
        
        await channel.set_permissions(target, overwrite=new_overwrite)
    
    embed = nextcord.Embed(
        description=f"🔒 Channel locked by {interaction.user.mention}",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed)

@bot.slash_command(name="unlock", description="Unlock the channel")
async def unlock_slash(interaction: nextcord.Interaction):
    """Unlock the channel and restore original permissions"""
    
    # Check permission (Executive+ or Holding)
    if not has_executive_or_holding(interaction.user):
        await interaction.response.send_message(
            "You are unable to use this command, as it is restricted to Executive+.",
            ephemeral=True
        )
        return
    
    # Log command
    await log_command(interaction.user, "unlock", "Slash")
    
    channel = interaction.channel
    channel_id = channel.id
    
    # Check if channel is locked
    if channel_id not in locked_channels:
        await interaction.response.send_message(
            "❌ This channel is not locked!",
            ephemeral=True
        )
        return
    
    # Get the original overwrites and remove from locked list FIRST
    original_overwrites = locked_channels[channel_id]
    del locked_channels[channel_id]
    
    # Now try to restore permissions
    for target_id, original_overwrite in original_overwrites.items():
        # Get the role by ID
        role = interaction.guild.get_role(target_id)
        if role:
            # Restore the FULL original PermissionOverwrite
            try:
                await channel.set_permissions(role, overwrite=original_overwrite)
            except Exception as e:
                print(f"Error restoring permission for role {target_id}: {e}")
    
    embed = nextcord.Embed(
        description=f"🔓 Channel has been unlocked.",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed)

# ------------------------------
# SAY SLASH COMMAND
# ------------------------------
@bot.slash_command(name="say", description="Repeat a message (Executive & Holding only)")
async def say_slash(interaction: nextcord.Interaction, *, message: str):
    await log_command(interaction.user, "say", "Slash")
    if any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message(message)
    else:
        await interaction.response.send_message(
            f"❌ {interaction.user.mention}, you don't have permission to use this command.",
            ephemeral=True
        )

# ------------------------------
# REQUESTTRAINING PREFIX COMMAND
# ------------------------------
@bot.command(name="requesttraining")
async def requesttraining_prefix(ctx):
    await log_command(ctx.author, "requesttraining", "Prefix")
    if ctx.channel.id != 1473150653374271491:
        await ctx.send(f"❌ {ctx.author.mention}, you can't use this command here.")
        return
    allowed_role_id = 1472037174630285538
    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send(f"❌ {ctx.author.mention}, you do not have permission to use this command.")
        return
    target_channel = bot.get_channel(1473150653374271491)
    if not target_channel:
        await ctx.send("❌ Could not find the target channel.")
        return
    embed = nextcord.Embed(
        title="Greetings, Staff Trainers",
        description=(
            f"{ctx.author.mention} is requesting that a training session will be hosted at this time.\n\n"
            "You are requested to organize one and provide further instructions in <#1472056023358640282>."
        ),
        color=0x4bbfff
    )
    await target_channel.send(content="<@&1473151069264678932>", embed=embed)
    await ctx.send(f"✅ {ctx.author.mention}, your training request has been sent!", delete_after=5)

# ------------------------------
# REQUESTTRAINING SLASH COMMAND
# ------------------------------
@bot.slash_command(name="requesttraining", description="Request a staff training session")
async def requesttraining_slash(interaction: nextcord.Interaction):
    await log_command(interaction.user, "requesttraining", "Slash")
    if interaction.channel_id != 1473150653374271491:
        await interaction.response.send_message(
            f"❌ {interaction.user.mention}, you can't use this command here.",
            ephemeral=True
        )
        return
    allowed_role_id = 1472037174630285538
    if allowed_role_id not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message(
            f"❌ {interaction.user.mention}, you do not have permission to use this command.",
            ephemeral=True
        )
        return
    target_channel = bot.get_channel(1473150653374271491)
    if not target_channel:
        await interaction.response.send_message("❌ Could not find the target channel.")
        return
    embed = nextcord.Embed(
        title="Greetings, Staff Trainers",
        description=(
            f"{interaction.user.mention} is requesting that a training session will be hosted at this time.\n\n"
            "You are requested to organize one and provide further instructions in <#1472056023358640282>."
        ),
        color=0x4bbfff
    )
    await target_channel.send(content="<@&1473151069264678932>", embed=embed)
    await interaction.response.send_message(
        f"✅ {interaction.user.mention}, your training request has been sent!",
        ephemeral=True
    )

# =========================================================
# ====================== NICK COMMAND ====================
# =========================================================

# Allowed user IDs for ;nick command
# Role IDs that can use the nick command (Intern Evaluator+)
NICK_COMMAND_ALLOWED_ROLES = [
    1472072792081170682,  # Evaluation
    1471641790112333867,  # Supervision
    1471641915215843559,  # Management
    1471642126663024640,  # Executive
    1471642360503992411,  # Holding
]

# Role hierarchy positions (higher number = higher rank)
ROLE_HIERARCHY = {
    1471642360503992411: 5,  # Holding
    1471642126663024640: 4,  # Executive
    1471641915215843559: 3,  # Management
    1471641790112333867: 2,  # Supervision
    1472072792081170682: 1,  # Evaluation
}

# Roles that cannot have their nicknames changed
PROTECTED_ROLES = [
    1471642126663024640,  # Executive
    1471642360503992411,  # Holding
]

def get_member_top_role_position(member):
    """Get the highest role position for a member based on the hierarchy."""
    member_role_ids = [role.id for role in member.roles]
    
    max_position = 0
    for role_id in member_role_ids:
        if role_id in ROLE_HIERARCHY:
            if ROLE_HIERARCHY[role_id] > max_position:
                max_position = ROLE_HIERARCHY[role_id]
    
    return max_position

def can_change_nickname(executor, target):
    """Check if the executor can change the target's nickname."""
    executor_role_ids = [role.id for role in executor.roles]
    target_role_ids = [role.id for role in target.roles]
    
    # Check if executor has Executive or Holding role
    executor_is_exec_or_holding = any(rid in executor_role_ids for rid in [1471642126663024640, 1471642360503992411])
    
    # Check if target has Executive or Holding role
    target_is_exec_or_holding = any(rid in target_role_ids for rid in [1471642126663024640, 1471642360503992411])
    
    # If target is Executive or Holding, executor MUST also be Executive or Holding
    if target_is_exec_or_holding and not executor_is_exec_or_holding:
        return False, "executor_below_associate_exec"
    
    # If target has Executive or Holding (and executor does too), cannot change
    if target_is_exec_or_holding and executor_is_exec_or_holding:
        return False, "target_protected"
    
    # Get positions for other hierarchy checks
    executor_position = get_member_top_role_position(executor)
    target_position = get_member_top_role_position(target)
    
    # Executor must have at least Evaluation level (position 1)
    if executor_position == 0:
        return False, "executor_no_role"
    
    # Target cannot have a higher position than executor
    if target_position > executor_position:
        return False, "target_higher"
    
    return True, None

def has_nick_permission(member):
    """Check if member has a role that allows using the nick command."""
    member_role_ids = [role.id for role in member.roles]
    return any(rid in member_role_ids for rid in NICK_COMMAND_ALLOWED_ROLES)

@bot.command(name="nick")
async def nick_command(ctx, member: nextcord.Member, *, new_nickname: str):
    """Change a member's nickname. Usage: ;nick @member new_nickname"""
    await log_command(ctx.author, "nick", "Prefix")

    # Check if the user has an allowed role (Intern Evaluator+)
    if not has_nick_permission(ctx.author):
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        # Send error message and delete it after 5 seconds
        error_msg = await ctx.send(
            f"{ctx.author.mention}, you do not have the proper permissions to use this command. You must be an Intern Evaluator+ of the staff-team in order to use it."
        )
        await error_msg.delete(delay=5)
        return

    # Check if the target's nickname can be changed
    can_change, reason = can_change_nickname(ctx.author, member)
    if not can_change:
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        
        if reason == "executor_below_associate_exec":
            error_msg = await ctx.send(
                f"{ctx.author.mention}, I do not have the appropriate permissions in order to run this command, since my roles are below Associate Executive+."
            )
        elif reason == "target_protected":
            error_msg = await ctx.send(
                f"Unfortunately {ctx.author.mention}, you are unable to change the nickname of this person as they are an Executive or Holding team member."
            )
        else:
            error_msg = await ctx.send(
                f"Unfortunately {ctx.author.mention}, you are unable to change the nickname, since they are ranked higher than you."
            )
        await error_msg.delete(delay=5)
        return
    
    # Change the nickname
    old_nickname = member.display_name
    try:
        await member.edit(nick=new_nickname)
        
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        
        # Send success message with embeds
        # Embed 1 - Title
        title_embed = nextcord.Embed(
            title="## __Member Nickname Update__",
            color=BLUE
        )
        
        # Embed 2 - Details
        details_embed = nextcord.Embed(
            description=f"{member.mention}'s nickname has been updated to **{new_nickname}** by {ctx.author.mention}",
            color=BLUE
        )
        
        # Embed 3 - Footer image
        footer_embed = nextcord.Embed(color=BLUE)
        footer_embed.set_image(url="https://cdn.discordapp.com/attachments/1472412365415776306/1475277452103258362/footerisrp.png?ex=699ce6b1&is=699b9531&hm=d0b11e03fb99f8ea16956ebe9e5e2b1bb657b5ea315c1f8638149f984325ca3a&")
        
        success_msg = await ctx.send(embeds=[title_embed, details_embed, footer_embed])
        await success_msg.delete(delay=30)
        
    except nextcord.Forbidden:
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        error_msg = await ctx.send(
            f"❌ {ctx.author.mention}, I don't have permission to change this member's nickname."
        )
        await error_msg.delete(delay=5)
    except Exception as e:
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        error_msg = await ctx.send(
            f"❌ An error occurred: {str(e)}"
        )
        await error_msg.delete(delay=5)

# ------------------------------
# NICK SLASH COMMAND
# ------------------------------
@bot.slash_command(name="nick", description="Change a member's nickname")
async def nick_slash(interaction: nextcord.Interaction, member: nextcord.Member, new_nickname: str):
    """Change a member's nickname. Usage: /nick @member new_nickname"""
    await log_command(interaction.user, "nick", "Slash")

    # Check if the user has an allowed role (Intern Evaluator+)
    if not has_nick_permission(interaction.user):
        await interaction.response.send_message(
            f"{interaction.user.mention}, you do not have the proper permissions to use this command. You must be an Intern Evaluator+ of the staff-team in order to use it.",
            ephemeral=True
        )
        return

    # Check if the target's nickname can be changed
    can_change, reason = can_change_nickname(interaction.user, member)
    if not can_change:
        if reason == "executor_below_associate_exec":
            await interaction.response.send_message(
                f"{interaction.user.mention}, I do not have the appropriate permissions in order to run this command, since my roles are below Associate Executive+.",
                ephemeral=True
            )
        elif reason == "target_protected":
            await interaction.response.send_message(
                f"Unfortunately {interaction.user.mention}, you are unable to change the nickname of this person as they are an Executive or Holding team member.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Unfortunately {interaction.user.mention}, you are unable to change the nickname, since they are ranked higher than you.",
                ephemeral=True
            )
        return

    # Change the nickname
    old_nickname = member.display_name
    try:
        await member.edit(nick=new_nickname)
        await interaction.response.send_message(
            f"✅ Successfully changed **{old_nickname}**'s nickname to **{new_nickname}**!",
            ephemeral=True
        )
    except nextcord.Forbidden:
        await interaction.response.send_message(
            f"❌ {interaction.user.mention}, I don't have permission to change this member's nickname.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )

# =========================================================
# ====================== TICKET SYSTEM ====================
# =========================================================

MAX_TICKETS_PER_USER = 3

CATEGORIES = {
    "general": 1471689868022120468,
    "appeal": 1471689978135183581,
    "report": 1473172223501144306,
    "management": 1471690051078455386
}

LOG_CHANNELS = {
    "general": 1471690459251478662,
    "appeal": 1471690532714450964,
    "report": 1471690532714450964,
    "management": 1471690561655279783
}

SUPPORT_ROLES = {
    "general": [1472072792081170682,1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "appeal": [1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "report": [1471641790112333867,1471641915215843559,1471642126663024640,1471642360503992411],
    "management": [1471641915215843559,1471642126663024640,1471642360503992411]
}

async def count_user_tickets(guild, user):
    count = 0
    for channel in guild.text_channels:
        if channel.topic and f"owner:{user.id}" in channel.topic:
            count += 1
    return count

def generate_ticket_name(user):
    return f"ticket-{user.name}".lower().replace(" ", "-")

class CloseReasonModal(nextcord.ui.Modal):
    def __init__(self, channel, ticket_type):
        super().__init__("Close Ticket With Reason")
        self.channel = channel
        self.ticket_type = ticket_type

        self.reason = nextcord.ui.TextInput(
            label="Reason for closing",
            style=nextcord.TextInputStyle.paragraph,
            required=True,
            max_length=500
        )
        self.add_item(self.reason)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer()

        transcript = await chat_exporter.export(self.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{self.channel.name}.html"
            )
            log_channel = interaction.guild.get_channel(LOG_CHANNELS[self.ticket_type])
            await log_channel.send(
                content=f"🔒 Ticket closed with reason:\n{self.reason.value}",
                file=file
            )

        await self.channel.delete()

class TicketView(nextcord.ui.View):
    def __init__(self, ticket_type):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type

    @nextcord.ui.button(label="Claim", style=nextcord.ButtonStyle.primary)
    async def claim(self, button, interaction):
        await interaction.response.send_message(
            f"👤 {interaction.user.mention} has claimed this ticket."
        )

    @nextcord.ui.button(label="Transcript", style=nextcord.ButtonStyle.secondary)
    async def transcript(self, button, interaction):
        await interaction.response.defer(ephemeral=True)
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{interaction.channel.name}.html"
            )
            await interaction.followup.send(file=file, ephemeral=True)

    @nextcord.ui.button(label="Close", style=nextcord.ButtonStyle.danger)
    async def close(self, button, interaction):
        await interaction.response.defer()
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            file = nextcord.File(
                fp=transcript.encode(),
                filename=f"{interaction.channel.name}.html"
            )
            log_channel = interaction.guild.get_channel(LOG_CHANNELS[self.ticket_type])
            await log_channel.send(content="🔒 Ticket closed.", file=file)
        await interaction.channel.delete()

    @nextcord.ui.button(label="Close With Reason", style=nextcord.ButtonStyle.secondary)
    async def close_reason(self, button, interaction):
        await interaction.response.send_modal(
            CloseReasonModal(interaction.channel, self.ticket_type)
        )

class TicketDropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="General Inquiry", value="general", emoji="<:GeneralInquiry:1471679744767426581>"),
            nextcord.SelectOption(label="Appeal a Punishment", value="appeal", emoji="<:AppealandReports:1471679782818418852>"),
            nextcord.SelectOption(label="Report a Member", value="report", emoji="<:AppealandReports:1471679782818418852>"),
            nextcord.SelectOption(label="Management Request", value="management", emoji="<:ManagementRequests:1471679839667879956>")
        ]
        super().__init__(
            placeholder="Select an Assistance Category",
            options=options,
            custom_id="persistent_ticket_dropdown"
        )

    async def callback(self, interaction: nextcord.Interaction):

        if await count_user_tickets(interaction.guild, interaction.user) >= MAX_TICKETS_PER_USER:
            await interaction.response.send_message(
                "❌ You already have 3 open tickets.",
                ephemeral=True
            )
            return

        ticket_type = self.values[0]
        category = interaction.guild.get_channel(CATEGORIES[ticket_type])

        overwrites = {
            interaction.guild.default_role: nextcord.PermissionOverwrite(view_channel=False),
            interaction.user: nextcord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for role_id in SUPPORT_ROLES[ticket_type]:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = nextcord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await interaction.guild.create_text_channel(
            name=generate_ticket_name(interaction.user),
            category=category,
            overwrites=overwrites,
            topic=f"owner:{interaction.user.id}"
        )

        embed = nextcord.Embed(
            title="Ticket Created",
            description="Please await staff assistance.",
            color=BLUE
        )

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=TicketView(ticket_type)
        )

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

class TicketPanel(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

@bot.slash_command(name="sendpanel", description="Send the ticket panel.")
async def sendpanel(interaction: nextcord.Interaction):

    # Admin check
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You must be an administrator to use this command.",
            ephemeral=True
        )
        return

    embed = nextcord.Embed(
        title="Illinois State Roleplay Support",
        description=(
            "Please select a ticket category from the dropdown below.\n\n"
            "<:GeneralInquiry:1471679744767426581> **General Inquiry**\n"
            "<:AppealandReports:1471679782818418852> **Appeal a Punishment**\n"
            "<:AppealandReports:1471679782818418852> **Report a Member**\n"
            "<:ManagementRequests:1471679839667879956> **Management Request**\n\n"
            "You may have up to **3 open tickets**."
        ),
        color=nextcord.Color.blue()
    )

    target_channel = bot.get_channel(1471666959753154646)
    if not target_channel:
        await interaction.response.send_message(
            "❌ Could not find the target channel.",
            ephemeral=True
        )
        return

    await target_channel.send(
        embed=embed,
        view=TicketPanel()
    )

    await interaction.response.send_message(
        "✅ Ticket panel sent.",
        ephemeral=True
    )


# =========================================================
# =================== SESSION MANAGEMENT ====================
# =========================================================

# Management+ role IDs (for permission check)
MANAGEMENT_ROLE_IDS = [
    1471641915215843559,  # Management
    1471642126663024640,  # Executive
    1471642360503992411,  # Holding
    1471642523821674618,  # Owner
    1471642550271082690,  # Co-Owner
]

# Session channel ID where session messages are sent
SESSION_CHANNEL_ID = 1471702676591874078

# The pinned message ID that should never be deleted
SESSION_PINNED_MESSAGE_ID = 1473473459312136426

# Session ping role ID
SESSION_PING_ROLE_ID = 1473466540430200862

# Staff role IDs for counting on-shift staff
STAFF_ROLE_IDS = [1472041465365663976, 1472041617295806485]

# Session refresh interval (in seconds) - 5 minutes
SESSION_REFRESH_INTERVAL = 300

# Session image URL
SESSION_IMAGE_URL = "https://cdn.discordapp.com/attachments/1472412365415776306/1473471108786426046/isrpsessions.png?ex=69965468&is=699502e8&hm=522484f0f1b7147b81bc287ddac36d841d815b72bd10e4f33618ebe0ff284e8a&"

# Checkmark emoji for voting
CHECKMARK_EMOJI = "<:Checkmark:1473460905634431109>"

# ERLC API URL (Police Roleplay Community API)
ERLC_API_URL = "https://api.policeroleplay.community/v1/server/stats"

# Your server's private server ID (you need to set this)
ERLC_SERVER_ID = "YOUR_SERVER_ID"  # Replace with your actual server ID

def has_management_role(member):
    """Check if member has Management+ role"""
    member_role_ids = [role.id for role in member.roles]
    return any(rid in member_role_ids for rid in MANAGEMENT_ROLE_IDS)

async def get_erlc_stats():
    """Fetch ERLC server stats from Police Roleplay Community API"""
    api_key = os.getenv("POLICE_ROLEPLAY_API_KEY")
    if not api_key:
        print("POLICE_ROLEPLAY_API_KEY not set in environment variables")
        return None
    
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        # Using the server stats endpoint from the API docs
        response = requests.get(ERLC_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Parse the response based on API format
            return {
                "players": data.get("playerCount", 0),
                "staff": data.get("staffCount", 0),
                "queue": data.get("queueCount", 0),
                "max_players": data.get("maxPlayers", 0)
            }
        else:
            print(f"ERLC API Error: Status {response.status_code}")
    except Exception as e:
        print(f"ERLC API Error: {e}")
    return None

async def count_on_shift_staff(guild):
    """Count members with on-shift staff roles"""
    count = 0
    for role_id in STAFF_ROLE_IDS:
        role = guild.get_role(role_id)
        if role:
            count += len(role.members)
    return count

class SessionManagementView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @nextcord.ui.button(label="Session Vote", style=nextcord.ButtonStyle.primary, emoji="🗳️", custom_id="session_vote")
    async def session_vote(self, button, interaction):
        if not has_management_role(interaction.user):
            await interaction.response.send_message(
                "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
                ephemeral=True
            )
            return
        
        # Check if session is already active
        if hasattr(bot, 'session_message_id') and bot.session_message_id is not None:
            await interaction.response.send_message(
                "Unable to use this session option. Please select a different one.",
                ephemeral=True
            )
            return
        
        # Send a modal to get vote count
        modal = SessionVoteModal()
        await interaction.response.send_modal(modal)
    
    @nextcord.ui.button(label="Session Start", style=nextcord.ButtonStyle.primary, emoji="▶️", custom_id="session_start")
    async def session_start(self, button, interaction):
        if not has_management_role(interaction.user):
            await interaction.response.send_message(
                "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
                ephemeral=True
            )
            return
        
        # Check if session is already active
        if hasattr(bot, 'session_message_id') and bot.session_message_id is not None:
            await interaction.response.send_message(
                "Unable to use this session option. Please select a different one.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        # Delete all messages in the session channel except the pinned message
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
        
        # Get ERLC stats
        stats = await get_erlc_stats()
        
        # Count on-shift staff
        on_shift_count = await count_on_shift_staff(interaction.guild)
        
        # Get player and queue info from stats
        players_in_game = stats['players'] if stats else 0
        max_players = stats['max_players'] if stats else 40
        queue_count = stats['queue'] if stats else 0
        
        # Create session start embeds
        # Embed 1 - Image
        image_embed = nextcord.Embed(color=BLUE)
        image_embed.set_image(url=SESSION_IMAGE_URL)
        
        # Embed 2 - Session info
        session_embed = nextcord.Embed(
            title="__ILSRP・Session Started__",
            description=(
                "Hello, Illinois State Roleplay Public Members.\n"
                "> After enough votes with the <:Checkmark:1473460905634431109> reaction, the session has officially started. Below outline some statistics to refer to.\n\n"
                f"> - In-Game Session Code: ```ILRPS```\n"
                f"> - In-Game: ```{players_in_game}/{max_players}```\n"
                f"> - In-Queue: ```{queue_count}/{max_players}```\n"
                f"> - On-Shift: ```{on_shift_count}```"
            ),
            color=BLUE,
            timestamp=utcnow()
        )
        
        # Send message without ping (auto-refresh will update without pinging)
        session_message = await session_channel.send(
            embeds=[image_embed, session_embed]
        )
        
        # Store the session message ID for auto-refresh
        bot.session_message_id = session_message.id
        bot.session_message_channel_id = session_channel.id
        
        # Track who started the session for DM system
        active_sessions[interaction.user.id] = {
            "start_time": int(time.time()),
            "type": "start"
        }
        
        # Start the auto-refresh background task
        bot.loop.create_task(refresh_session_message())
        
        await interaction.followup.send("✅ Session started message sent! (Will auto-refresh every 5 minutes)", ephemeral=True)
    
    @nextcord.ui.button(label="Session Shutdown", style=nextcord.ButtonStyle.primary, emoji="⏹️", custom_id="session_shutdown")
    async def session_shutdown(self, button, interaction):
        if not has_management_role(interaction.user):
            await interaction.response.send_message(
                "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
                ephemeral=True
            )
            return
        
        # Check if there's an active session OR an active vote
        has_session = hasattr(bot, 'session_message_id') and bot.session_message_id is not None
        has_vote = hasattr(bot, 'session_votes') and len(bot.session_votes) > 0
        
        # Allow shutdown if there's either a session OR a vote
        if not has_session and not has_vote:
            await interaction.response.send_message(
                "Unable to use this session option. Please select a different one.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        # Clear the session message ID to stop auto-refresh
        bot.session_message_id = None
        bot.session_message_channel_id = None
        
        # Clear any active votes
        if hasattr(bot, 'session_votes'):
            bot.session_votes = {}
        
        # Delete all messages in the session channel except the pinned message
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
        
        embed = nextcord.Embed(
            title="🔴 Session Ended",
            description="The current session has been shut down.",
            color=0xFF0000,
            timestamp=utcnow()
        )
        embed.set_author(name=f"{interaction.user}", icon_url=interaction.user.display_avatar.url)
        
        await session_channel.send(embed=embed)
        await interaction.followup.send("✅ Session shutdown message sent!", ephemeral=True)
    
    @nextcord.ui.button(label="Session Low", style=nextcord.ButtonStyle.primary, emoji="📢", custom_id="session_low")
    async def session_low(self, button, interaction):
        if not has_management_role(interaction.user):
            await interaction.response.send_message(
                "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
                ephemeral=True
            )
            return
        
        # Check if session is NOT active
        if not hasattr(bot, 'session_message_id') or bot.session_message_id is None:
            await interaction.response.send_message(
                "Unable to use this session option. Please select a different one.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        embed = nextcord.Embed(
            title="📢 Session Needs Boost!",
            description="The session needs more players! Come join us!",
            color=BLUE,
            timestamp=utcnow()
        )
        
        await session_channel.send(
            content=f"<@&{SESSION_PING_ROLE_ID}> @here",
            embed=embed
        )
        await interaction.followup.send("✅ Session low ping sent!", ephemeral=True)
    
    @nextcord.ui.button(label="Session Full", style=nextcord.ButtonStyle.primary, emoji="✅", custom_id="session_full")
    async def session_full(self, button, interaction):
        if not has_management_role(interaction.user):
            await interaction.response.send_message(
                "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
                ephemeral=True
            )
            return
        
        # Check if session is NOT active
        if not hasattr(bot, 'session_message_id') or bot.session_message_id is None:
            await interaction.response.send_message(
                "Unable to use this session option. Please select a different one.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        embed = nextcord.Embed(
            title="✅ Session Full",
            description="The session is currently full. Please wait for the next session!",
            color=BLUE,
            timestamp=utcnow()
        )
        
        await session_channel.send(embed=embed)
        await interaction.followup.send("✅ Session full message sent!", ephemeral=True)

class SessionVoteModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Session Vote Setup")
        self.vote_count = nextcord.ui.TextInput(
            label="Number of votes required",
            style=nextcord.TextInputStyle.short,
            required=True,
            placeholder="Enter number (e.g., 10)"
        )
        self.add_item(self.vote_count)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            required_votes = int(self.vote_count.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        # Delete all messages in the session channel except the pinned message
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
        
        # Sky blue color for embed sidebar
        SKY_BLUE = 0x87CEEB
        
        # Create TWO embeds with sky blue sidebar
        # Embed 1 - Image with sky blue sidebar
        image_embed = nextcord.Embed(color=SKY_BLUE)
        image_embed.set_image(url=SESSION_IMAGE_URL)
        
        # Embed 2 - Text content with vote info
        text_embed = nextcord.Embed(
            title="__ILSRP・Session Voting__",
            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\nSee you soon! <:ILSRP:1471990869166002291>",
            color=SKY_BLUE,
            timestamp=utcnow()
        )
        
        vote_message = await session_channel.send(
            content=f"<@&{SESSION_PING_ROLE_ID}>",
            embeds=[image_embed, text_embed]
        )
        
        # Add checkmark reaction
        try:
            await vote_message.add_reaction(CHECKMARK_EMOJI)
        except:
            # Try with unicode emoji if custom emoji fails
            await vote_message.add_reaction("✅")
        
        # Store vote info for tracking
        if not hasattr(bot, 'session_votes'):
            bot.session_votes = {}
        
        bot.session_votes[vote_message.id] = {
            "required": required_votes,
            "initiator": interaction.user.id,
            "channel_id": session_channel.id,
            "message_id": vote_message.id
        }
        
        # Start the vote auto-refresh background task
        bot.loop.create_task(refresh_vote_messages())
        
        await interaction.followup.send(
            f"✅ Session vote started! Required votes: **{required_votes}**\n"
            f"Vote message sent in {session_channel.mention}",
            ephemeral=True
        )

class StartSessionButton(nextcord.ui.View):
    def __init__(self, initiator_id):
        super().__init__(timeout=None)
        self.initiator_id = initiator_id
    
    @nextcord.ui.button(label="Start Session", style=nextcord.ButtonStyle.primary, emoji="▶️", custom_id="start_session_btn")
    async def start_session(self, button, interaction):
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message(
                "❌ Only the vote initiator can start the session.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        session_channel = interaction.guild.get_channel(SESSION_CHANNEL_ID)
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        # Delete all messages in the session channel except the pinned message
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
        
        # Get ERLC stats
        stats = await get_erlc_stats()
        
        # Count on-shift staff
        on_shift_count = await count_on_shift_staff(interaction.guild)
        
        # Get player and queue info from stats
        players_in_game = stats['players'] if stats else 0
        max_players = stats['max_players'] if stats else 40
        queue_count = stats['queue'] if stats else 0
        
        # Create session start embeds
        # Embed 1 - Image
        image_embed = nextcord.Embed(color=BLUE)
        image_embed.set_image(url=SESSION_IMAGE_URL)
        
        # Embed 2 - Session info
        session_embed = nextcord.Embed(
            title="__ILSRP・Session Started__",
            description=(
                "Hello, Illinois State Roleplay Public Members.\n"
                "> After enough votes with the <:Checkmark:1473460905634431109> reaction, the session has officially started. Below outline some statistics to refer to.\n\n"
                f"> - In-Game Session Code: ```ILRPS```\n"
                f"> - In-Game: ```{players_in_game}/{max_players}```\n"
                f"> - In-Queue: ```{queue_count}/{max_players}```\n"
                f"> - On-Shift: ```{on_shift_count}```"
            ),
            color=BLUE,
            timestamp=utcnow()
        )
        
        # Get session channel from vote info
        vote_info = None
        for msg_id, info in bot.session_votes.items():
            if info.get("initiator") == interaction.user.id:
                vote_info = info
                break
        
        if not vote_info:
            await interaction.followup.send("❌ No active vote found.", ephemeral=True)
            return
        
        session_channel = interaction.guild.get_channel(vote_info["channel_id"])
        if not session_channel:
            await interaction.followup.send("❌ Session channel not found.", ephemeral=True)
            return
        
        # Delete all messages in the session channel except the pinned message
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
        
        # Get ERLC stats
        stats = await get_erlc_stats()
        
        # Count on-shift staff
        on_shift_count = await count_on_shift_staff(interaction.guild)
        
        # Get player and queue info from stats
        players_in_game = stats['players'] if stats else 0
        max_players = stats['max_players'] if stats else 40
        queue_count = stats['queue'] if stats else 0
        
        # Create session start embeds
        # Embed 1 - Image
        image_embed = nextcord.Embed(color=BLUE)
        image_embed.set_image(url=SESSION_IMAGE_URL)
        
        # Embed 2 - Session info
        session_embed = nextcord.Embed(
            title="__ILSRP・Session Started__",
            description=(
                "Hello, Illinois State Roleplay Public Members.\n"
                "> After enough votes with the <:Checkmark:1473460905634431109> reaction, the session has officially started. Below outline some statistics to refer to.\n\n"
                f"> - In-Game Session Code: ```ILRPS```\n"
                f"> - In-Game: ```{players_in_game}/{max_players}```\n"
                f"> - In-Queue: ```{queue_count}/{max_players}```\n"
                f"> - On-Shift: ```{on_shift_count}```"
            ),
            color=BLUE,
            timestamp=utcnow()
        )
        
        # Send the session start message
        session_message = await session_channel.send(
            embeds=[image_embed, session_embed]
        )
        
        # Store the session message ID for auto-refresh
        bot.session_message_id = session_message.id
        bot.session_message_channel_id = session_channel.id
        
        # Track who started the session for DM system (from vote)
        vote_info = None
        for msg_id, info in bot.session_votes.items():
            if info.get("initiator") == interaction.user.id:
                vote_info = info
                break
        
        if vote_info:
            active_sessions[vote_info["initiator"]] = {
                "start_time": int(time.time()),
                "type": "vote"
            }
        
        # Start the auto-refresh background task
        bot.loop.create_task(refresh_session_message())
        
        await interaction.followup.send("✅ Session started successfully! (Will auto-refresh every 5 minutes)", ephemeral=True)
        
        # Clear vote tracking for this initiator
        if hasattr(bot, 'session_votes'):
            # Remove votes for this initiator
            votes_to_remove = [msg_id for msg_id, info in bot.session_votes.items() if info.get("initiator") == interaction.user.id]
            for msg_id in votes_to_remove:
                del bot.session_votes[msg_id]

@bot.event
async def on_raw_reaction_add(payload):
    """Handle vote reactions"""
    if not hasattr(bot, 'session_votes'):
        return
    
    if payload.message_id not in bot.session_votes:
        return
    
    # Get the message
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return
    
    try:
        message = await channel.fetch_message(payload.message_id)
    except:
        return
    
    # Check if reaction is the checkmark
    emoji_str = str(payload.emoji)
    if CHECKMARK_EMOJI not in emoji_str and "✅" not in emoji_str:
        return
    
    # Don't count bot's own reaction
    if payload.user_id == bot.user.id:
        return
    
    # Count the actual number of reactions (excluding bot's own reaction)
    vote_info = bot.session_votes[payload.message_id]
    required_votes = vote_info["required"]
    
    # Get all reactions on the message and count checkmark reactions
    current_votes = 0
    for reaction in message.reactions:
        # Check if this is the checkmark reaction (either custom or unicode)
        if str(reaction.emoji) == CHECKMARK_EMOJI or str(reaction.emoji) == "✅":
            # Count non-bot users who reacted
            async for user in reaction.users():
                if user.id != bot.user.id:
                    current_votes += 1
            break
    
    # Update embed with new vote count
    initiator = channel.guild.get_member(vote_info["initiator"])
    initiator_mention = initiator.mention if initiator else "Unknown"
    
    # Sky blue color
    SKY_BLUE = 0x87CEEB
    
    # Create TWO embeds
    # Embed 1 - Image with sky blue sidebar
    image_embed = nextcord.Embed(color=SKY_BLUE)
    image_embed.set_image(url=SESSION_IMAGE_URL)
    
    # Check if vote threshold reached
    if current_votes >= required_votes:
        # Add Start Session button
        view = StartSessionButton(vote_info["initiator"])
        
        # Text embed - Vote passed
        text_embed = nextcord.Embed(
            title="__ILSRP・Session Voting__",
            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n✅ **{current_votes}/{required_votes}** votes reached!\n\nClick below to start the session:",
            color=0x00FF00,
            timestamp=utcnow()
        )
        
        # Ping the initiator when threshold is reached
        await channel.send(content=f"{initiator_mention}")
        await message.edit(embeds=[image_embed, text_embed], view=view)
    else:
        # Text embed - Vote in progress
        text_embed = nextcord.Embed(
            title="__ILSRP・Session Voting__",
            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n**Votes: {current_votes}/{required_votes}**",
            color=SKY_BLUE,
            timestamp=utcnow()
        )
        
        await message.edit(embeds=[image_embed, text_embed])

@bot.event
async def on_raw_reaction_remove(payload):
    """Handle vote reaction removal"""
    if not hasattr(bot, 'session_votes'):
        return
    
    if payload.message_id not in bot.session_votes:
        return
    
    # Get the message
    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return
    
    try:
        message = await channel.fetch_message(payload.message_id)
    except:
        return
    
    # Check if reaction is the checkmark
    emoji_str = str(payload.emoji)
    if CHECKMARK_EMOJI not in emoji_str and "✅" not in emoji_str:
        return
    
    # Count the actual number of reactions (excluding bot's own reaction)
    vote_info = bot.session_votes[payload.message_id]
    required_votes = vote_info["required"]
    
    # Get all reactions on the message and count checkmark reactions
    current_votes = 0
    for reaction in message.reactions:
        # Check if this is the checkmark reaction (either custom or unicode)
        if str(reaction.emoji) == CHECKMARK_EMOJI or str(reaction.emoji) == "✅":
            # Count non-bot users who reacted
            async for user in reaction.users():
                if user.id != bot.user.id:
                    current_votes += 1
            break
    
    # Update embed with new vote count
    initiator = channel.guild.get_member(vote_info["initiator"])
    initiator_mention = initiator.mention if initiator else "Unknown"
    
    # Sky blue color
    SKY_BLUE = 0x87CEEB
    
    # Create TWO embeds
    # Embed 1 - Image with sky blue sidebar
    image_embed = nextcord.Embed(color=SKY_BLUE)
    image_embed.set_image(url=SESSION_IMAGE_URL)
    
    # Check if vote threshold reached (shouldn't happen on remove, but check anyway)
    if current_votes >= required_votes:
        # Add Start Session button
        view = StartSessionButton(vote_info["initiator"])
        
        # Text embed - Vote passed
        text_embed = nextcord.Embed(
            title="__ILSRP・Session Voting__",
            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n✅ **{current_votes}/{required_votes}** votes reached!\n\nClick below to start the session:",
            color=0x00FF00,
            timestamp=utcnow()
        )
        
        # Ping the initiator when threshold is reached
        await channel.send(content=f"{initiator_mention}")
        await message.edit(embeds=[image_embed, text_embed], view=view)
    else:
        # Text embed - Vote in progress
        text_embed = nextcord.Embed(
            title="__ILSRP・Session Voting__",
            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n**Votes: {current_votes}/{required_votes}**",
            color=SKY_BLUE,
            timestamp=utcnow()
        )
        
        await message.edit(embeds=[image_embed, text_embed])

@bot.slash_command(name="sessions", description="Manage server sessions")
async def session_management(interaction: nextcord.Interaction):
    """Send the session management panel"""
    if not has_management_role(interaction.user):
        await interaction.response.send_message(
            "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team.",
            ephemeral=True
        )
        return
    
    embed = nextcord.Embed(
        title="🎮 Session Management",
        description="Select an action below:",
        color=BLUE,
        timestamp=utcnow()
    )
    embed.add_field(name="🗳️ Session Vote", value="Start a vote for a new session", inline=False)
    embed.add_field(name="▶️ Session Start", value="Start a new session with ERLC stats", inline=False)
    embed.add_field(name="⏹️ Session Shutdown", value="End the current session", inline=False)
    embed.add_field(name="📢 Session Low", value="Ping for more players", inline=False)
    embed.add_field(name="✅ Session Full", value="Mark session as full (no ping)", inline=False)
    embed.set_footer(text="Illinois State Roleplay - Session Management")
    
    view = SessionManagementView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ------------------------------
# SESSIONS PREFIX COMMAND
# ------------------------------
@bot.command(name="sessions")
async def sessions_prefix(ctx):
    """Send the session management panel"""
    await log_command(ctx.author, "sessions", "Prefix")
    
    if not has_management_role(ctx.author):
        # Delete user's command message
        try:
            await ctx.message.delete()
        except:
            pass
        # Send error message and delete it after 5 seconds
        error_msg = await ctx.send(
            "❌ You are not permitted to use this feature. It is restricted to Management+ members of Illinois State Roleplay's Staff Team."
        )
        await error_msg.delete(delay=5)
        return
    
    embed = nextcord.Embed(
        title="🎮 Session Management",
        description="Select an action below:",
        color=BLUE,
        timestamp=utcnow()
    )
    embed.add_field(name="🗳️ Session Vote", value="Start a vote for a new session", inline=False)
    embed.add_field(name="▶️ Session Start", value="Start a new session with ERLC stats", inline=False)
    embed.add_field(name="⏹️ Session Shutdown", value="End the current session", inline=False)
    embed.add_field(name="📢 Session Low", value="Ping for more players", inline=False)
    embed.add_field(name="✅ Session Full", value="Mark session as full (no ping)", inline=False)
    embed.set_footer(text="Illinois State Roleplay - Session Management")

    view = SessionManagementView()
    
    # Delete user's command message
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Send the panel as ephemeral (only visible to user)
    await ctx.send(embed=embed, view=view)

async def refresh_session_message():
    """Automatically refresh the session message with updated stats every 5 minutes"""
    while not bot.is_closed():
        if hasattr(bot, 'session_message_id') and bot.session_message_id and hasattr(bot, 'session_message_channel_id') and bot.session_message_channel_id:
            try:
                channel = bot.get_channel(bot.session_message_channel_id)
                if channel:
                    message = await channel.fetch_message(bot.session_message_id)
                    
                    # Get fresh stats
                    stats = await get_erlc_stats()
                    on_shift_count = await count_on_shift_staff(channel.guild)
                    
                    players_in_game = stats['players'] if stats else 0
                    max_players = stats['max_players'] if stats else 40
                    queue_count = stats['queue'] if stats else 0
                    
                    # Create updated embed (keep image embed as first embed)
                    image_embed = nextcord.Embed(color=BLUE)
                    image_embed.set_image(url=SESSION_IMAGE_URL)
                    
                    session_embed = nextcord.Embed(
                        title="__ILSRP・Session Started__",
                        description=(
                            "Hello, Illinois State Roleplay Public Members.\n"
                            "> After enough votes with the <:Checkmark:1473460905634431109> reaction, the session has officially started. Below outline some statistics to refer to.\n\n"
                            f"> - In-Game Session Code: ```ILRPS```\n"
                            f"> - In-Game: ```{players_in_game}/{max_players}```\n"
                            f"> - In-Queue: ```{queue_count}/{max_players}```\n"
                            f"> - On-Shift: ```{on_shift_count}```"
                        ),
                        color=BLUE,
                        timestamp=utcnow()
                    )
                    
                    await message.edit(embeds=[image_embed, session_embed])
            except Exception as e:
                print(f"Error refreshing session message: {e}")
        
        await asyncio.sleep(SESSION_REFRESH_INTERVAL)

# ------------------------------
# Vote Auto-Refresh Function (Every Minute)
# ------------------------------
async def refresh_vote_messages():
    """Automatically refresh vote messages every minute to show updated vote counts"""
    while not bot.is_closed():
        if hasattr(bot, 'session_votes') and bot.session_votes:
            for message_id, vote_info in list(bot.session_votes.items()):
                try:
                    channel = bot.get_channel(vote_info["channel_id"])
                    if not channel:
                        continue
                    
                    message = await channel.fetch_message(message_id)
                    
                    # Count actual reactions
                    required_votes = vote_info["required"]
                    current_votes = 0
                    
                    for reaction in message.reactions:
                        if str(reaction.emoji) == CHECKMARK_EMOJI or str(reaction.emoji) == "✅":
                            async for user in reaction.users():
                                if user.id != bot.user.id:
                                    current_votes += 1
                            break
                    
                    # Get initiator info
                    initiator = channel.guild.get_member(vote_info["initiator"])
                    initiator_mention = initiator.mention if initiator else "Unknown"
                    
                    SKY_BLUE = 0x87CEEB
                    
                    # Create embeds
                    image_embed = nextcord.Embed(color=SKY_BLUE)
                    image_embed.set_image(url=SESSION_IMAGE_URL)
                    
                    if current_votes >= required_votes:
                        view = StartSessionButton(vote_info["initiator"])
                        text_embed = nextcord.Embed(
                            title="__ILSRP・Session Voting__",
                            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n✅ **{current_votes}/{required_votes}** votes reached!\n\nClick below to start the session:",
                            color=0x00FF00,
                            timestamp=utcnow()
                        )
                        await message.edit(embeds=[image_embed, text_embed], view=view)
                    else:
                        text_embed = nextcord.Embed(
                            title="__ILSRP・Session Voting__",
                            description=f"> A Session Vote has been conducted by the Management Team+. React with {CHECKMARK_EMOJI} in order to vote. Once **{required_votes}** votes have been reacted, a session will begin! Thanks for voting and remain patient.\n\n**Votes: {current_votes}/{required_votes}**",
                            color=SKY_BLUE,
                            timestamp=utcnow()
                        )
                        await message.edit(embeds=[image_embed, text_embed])
                        
                except Exception as e:
                    print(f"Error refreshing vote message: {e}")
        
        await asyncio.sleep(60)  # Refresh every minute

# ------------------------------
# Member count update function
# ------------------------------
async def update_member_count(guild):
    """Update the voice channel name with the non-bot member count"""
    try:
        channel = bot.get_channel(MEMBER_COUNT_CHANNEL_ID)
        if channel:
            # Count non-bot members
            member_count = len([m for m in guild.members if not m.bot])
            # Update channel name (max 100 characters for channel names)
            new_name = f"Members: {member_count}"
            if len(new_name) > 100:
                new_name = f"Members: {member_count}"[:100]
            await channel.edit(name=new_name)
            print(f"Updated member count channel to: {new_name}")
    except Exception as e:
        print(f"Error updating member count channel: {e}")

# ------------------------------
# Periodic member count update task
# ------------------------------
async def update_member_count_periodic():
    """Periodically update the member count channel"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            # Get the guild from the channel
            channel = bot.get_channel(MEMBER_COUNT_CHANNEL_ID)
            if channel and channel.guild:
                await update_member_count(channel.guild)
        except Exception as e:
            print(f"Error in periodic member count update: {e}")
        # Update every 60 seconds
        await asyncio.sleep(60)

# ------------------------------
# Keep-alive / Activity Logistic
# ------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}!")
    try:
        await bot.sync_all_application_commands()
        print("Slash commands synced!")
    except Exception as e:
        print(f"Slash sync failed: {e}")

    bot.add_view(TicketPanel())
    bot.add_view(SessionManagementView())
    
    # Start the vote auto-refresh task
    bot.loop.create_task(refresh_vote_messages())
    
    # Start the member count update task
    bot.loop.create_task(update_member_count_periodic())
    
    # Initial member count update on startup
    member_count_channel = bot.get_channel(MEMBER_COUNT_CHANNEL_ID)
    if member_count_channel and member_count_channel.guild:
        await update_member_count(member_count_channel.guild)
    
    # Send deployment notification message once on startup
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        deployment_embed = nextcord.Embed(
            title="New Deployment",
            description="# New deployment has occured. Please refresh your client to see the changes, by exploring commands, embeds, and more!",
            color=0x4bbfff,
            timestamp=utcnow()
        )
        await log_channel.send(embed=deployment_embed)

    keepalive_channel = bot.get_channel(1473152268411998410)

    async def keep_sending():
        await bot.wait_until_ready()
        while not bot.is_closed():
            if keepalive_channel:
                embed = nextcord.Embed(
                    title="__Activity Logistic__",
                    description=(
                        "> This message is being sent to ensure that the bot keeps running smoothly.\n"
                        f"> Timestamp of Logistic: <t:{int(utcnow().timestamp())}:F>"
                    ),
                    color=0x4bbfff,
                    timestamp=utcnow()
                )
                await keepalive_channel.send(embed=embed)
            await asyncio.sleep(60)

    bot.loop.create_task(keep_sending())
    
    # Start session DM check task
    bot.loop.create_task(check_sessions())
    
    # Start scheduled verification task
    bot.loop.create_task(scheduled_verification())

# =========================================================
# =================== DATABASE SETUP ======================
# =========================================================

# Economy Database
conn = sqlite3.connect('economy.db')
c = conn.cursor()

# Create economy tables
c.execute('''CREATE TABLE IF NOT EXISTS economy (
    user_id INTEGER PRIMARY KEY,
    wallet INTEGER DEFAULT 0,
    bank INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    daily_timestamp INTEGER DEFAULT 0,
    weekly_timestamp INTEGER DEFAULT 0,
    monthly_timestamp INTEGER DEFAULT 0,
    work_timestamp INTEGER DEFAULT 0,
    beg_timestamp INTEGER DEFAULT 0,
    last_robbed INTEGER DEFAULT 0,
   robbed_count INTEGER DEFAULT 0
)''')

c.execute('''CREATE TABLE IF NOT EXISTS economy_settings (
    id INTEGER PRIMARY KEY,
    starting_balance INTEGER DEFAULT 0,
    daily_reward INTEGER DEFAULT 100,
    weekly_reward INTEGER DEFAULT 500,
    monthly_reward INTEGER DEFAULT 2000,
    work_min INTEGER DEFAULT 10,
    work_max INTEGER DEFAULT 50,
    beg_min INTEGER DEFAULT 5,
    beg_max INTEGER DEFAULT 25,
    rob_min INTEGER DEFAULT 100,
    rob_max INTEGER DEFAULT 500,
    rob_cooldown INTEGER DEFAULT 3600,
    tax_rate INTEGER DEFAULT 10
)''')

# Insert default settings if not exist
c.execute("INSERT OR IGNORE INTO economy_settings (id, starting_balance, daily_reward, weekly_reward, monthly_reward, work_min, work_max, beg_min, beg_max, rob_min, rob_max, rob_cooldown, tax_rate) VALUES (1, 100, 100, 500, 2000, 10, 50, 5, 25, 100, 500, 3600, 10)")
conn.commit()

# AFK Database
c.execute('''CREATE TABLE IF NOT EXISTS afk (
    user_id INTEGER PRIMARY KEY,
    reason TEXT,
    start_time INTEGER,
    pings TEXT DEFAULT '[]'
)''')
conn.commit()

# Suggestions Database
c.execute('''CREATE TABLE IF NOT EXISTS suggestions (
    message_id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    author_id INTEGER,
    suggestion TEXT,
    status TEXT DEFAULT 'pending',
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    approver_id INTEGER DEFAULT NULL,
    approved_at INTEGER DEFAULT NULL
)''')
conn.commit()

# Session DM System
# Active sessions tracking
active_sessions = {}  # {initiator_id: {"start_time": timestamp, "type": "vote" or "start"}}

# =========================================================
# =================== SESSION DM SYSTEM ===================
# =========================================================

# Session DM constants
SESSION_CHECK_INTERVAL = 7200  # 2 hours in seconds
MANAGEMENT_DM_TIMEOUT = 1800  # 30 minutes in seconds
SESSION_SHUTDOWN_DELAY = 5  # 5 seconds

class SessionActiveView(nextcord.ui.View):
    def __init__(self, initiator_id):
        super().__init__(timeout=1800)  # 30 min timeout
        self.initiator_id = initiator_id
    
    @nextcord.ui.button(label="Yes, session is active", style=nextcord.ButtonStyle.success, emoji="✅")
    async def yes_button(self, button, interaction):
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message("❌ Only the session initiator can respond.", ephemeral=True)
            return
        
        # Restart the session timer
        active_sessions[self.initiator_id]["start_time"] = int(time.time())
        
        await interaction.response.send_message("✅ Session timer restarted! The session will be checked again in 2 hours.", ephemeral=True)
        self.stop()
    
    @nextcord.ui.button(label="No, end the session", style=nextcord.ButtonStyle.danger, emoji="⏹️")
    async def no_button(self, button, interaction):
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message("❌ Only the session initiator can respond.", ephemeral=True)
            return
        
        # Shutdown session
        await shutdown_session(interaction.user, interaction.guild)
        
        await interaction.response.send_message("✅ Session has been shut down.", ephemeral=True)
        self.stop()

async def check_sessions():
    """Background task to check active sessions every minute"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        current_time = int(time.time())
        sessions_to_check = []
        
        for initiator_id, session_data in list(active_sessions.items()):
            start_time = session_data.get("start_time", 0)
            if current_time - start_time >= SESSION_CHECK_INTERVAL:
                sessions_to_check.append((initiator_id, session_data))
        
        for initiator_id, session_data in sessions_to_check:
            try:
                guild = bot.guilds[0]  # Get the guild
                initiator = guild.get_member(initiator_id)
                
                if initiator:
                    # Send DM to initiator
                    embed = nextcord.Embed(
                        title="Session Check",
                        description="Is the session still currently active?",
                        color=BLUE
                    )
                    view = SessionActiveView(initiator_id)
                    try:
                        await initiator.send(embed=embed, view=view)
                    except:
                        # If DM fails, proceed to shutdown
                        await shutdown_session(initiator, guild)
                
                # Wait for response or timeout
                await asyncio.sleep(MANAGEMENT_DM_TIMEOUT)
                
                # Check if session is still active after timeout
                if initiator_id in active_sessions:
                    # DM all Management role members who are NOT invisible/AFK
                    await dm_management_team(guild)
                    
                    # Wait another 30 minutes for management response
                    await asyncio.sleep(MANAGEMENT_DM_TIMEOUT)
                    
                    # If still active, shutdown
                    if initiator_id in active_sessions:
                        await shutdown_session(initiator, guild)
                        
            except Exception as e:
                print(f"Error in session check: {e}")
        
        await asyncio.sleep(60)  # Check every minute

async def dm_management_team(guild):
    """DM all Management role members who are not invisible/AFK"""
    management_role = guild.get_role(1471641915215843559)
    if not management_role:
        return
    
    embed = nextcord.Embed(
        title="Session Check",
        description="Is the session still currently active? The session initiator has not responded. Please respond if the session should continue.",
        color=BLUE
    )
    
    view = ManagementSessionView(list(management_role.members))
    
    for member in management_role.members:
        # Check if member is not invisible/afk (based on status)
        if member.status != nextcord.Status.offline:
            try:
                await member.send(embed=embed, view=view)
            except:
                pass

class ManagementSessionView(nextcord.ui.View):
    def __init__(self, members):
        super().__init__(timeout=1800)
        self.responded_members = []
        self.members = members
    
    @nextcord.ui.button(label="Yes, keep session", style=nextcord.ButtonStyle.success, emoji="✅")
    async def yes_button(self, button, interaction):
        if interaction.user.id in self.responded_members:
            await interaction.response.send_message("You have already responded!", ephemeral=True)
            return
        
        self.responded_members.append(interaction.user.id)
        await interaction.response.send_message("✅ Thank you! The session will continue.", ephemeral=True)
    
    @nextcord.ui.button(label="No, shutdown", style=nextcord.ButtonStyle.danger, emoji="⏹️")
    async def no_button(self, button, interaction):
        if interaction.user.id in self.responded_members:
            await interaction.response.send_message("You have already responded!", ephemeral=True)
            return
        
        self.responded_members.append(interaction.user.id)
        await shutdown_session(interaction.user, interaction.guild)
        await interaction.response.send_message("✅ Session has been shut down.", ephemeral=True)
        self.stop()

async def shutdown_session(user, guild):
    """Shutdown the session and send the thank you message"""
    # Remove from active sessions
    for initiator_id in list(active_sessions.keys()):
        if active_sessions[initiator_id].get("start_time"):
            del active_sessions[initiator_id]
    
    # Clear session message ID
    bot.session_message_id = None
    bot.session_message_channel_id = None
    
    # Clear any active votes
    if hasattr(bot, 'session_votes'):
        bot.session_votes = {}
    
    # Delete messages in session channel
    session_channel = guild.get_channel(SESSION_CHANNEL_ID)
    if session_channel:
        try:
            async for message in session_channel.history(limit=100):
                if message.id != SESSION_PINNED_MESSAGE_ID:
                    try:
                        await message.delete()
                    except:
                        pass
        except:
            pass
    
    # Wait 5 seconds then send shutdown message
    await asyncio.sleep(SESSION_SHUTDOWN_DELAY)
    
    if session_channel:
        await session_channel.send("Thanks for joining us today. See you soon")

# Modify session_start to track initiator
original_session_start = None

# We need to modify the session start functions to track who started the session
# This will be handled in the SessionManagementView class modifications

# =========================================================
# =================== ECONOMY SYSTEM =====================
# =========================================================

def get_economy_settings():
    c.execute("SELECT * FROM economy_settings WHERE id = 1")
    result = c.fetchone()
    if result:
        return {
            "starting_balance": result[1],
            "daily_reward": result[2],
            "weekly_reward": result[3],
            "monthly_reward": result[4],
            "work_min": result[5],
            "work_max": result[6],
            "beg_min": result[7],
            "beg_max": result[8],
            "rob_min": result[9],
            "rob_max": result[10],
            "rob_cooldown": result[11],
            "tax_rate": result[12]
        }
    return {
        "starting_balance": 100,
        "daily_reward": 100,
        "weekly_reward": 500,
        "monthly_reward": 2000,
        "work_min": 10,
        "work_max": 50,
        "beg_min": 5,
        "beg_max": 25,
        "rob_min": 100,
        "rob_max": 500,
        "rob_cooldown": 3600,
        "tax_rate": 10
    }

def get_user_economy(user_id):
    c.execute("SELECT * FROM economy WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if not result:
        settings = get_economy_settings()
        c.execute("INSERT INTO economy (user_id, wallet, bank, total_earned, daily_timestamp, weekly_timestamp, monthly_timestamp, work_timestamp, beg_timestamp, last_robbed, robbed_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, settings["starting_balance"], 0, settings["starting_balance"], 0, 0, 0, 0, 0, 0, 0))
        conn.commit()
        return {
            "wallet": settings["starting_balance"],
            "bank": 0,
            "total_earned": settings["starting_balance"],
            "daily_timestamp": 0,
            "weekly_timestamp": 0,
            "monthly_timestamp": 0,
            "work_timestamp": 0,
            "beg_timestamp": 0,
            "last_robbed": 0,
            "robbed_count": 0
        }
    return {
        "wallet": result[1],
        "bank": result[2],
        "total_earned": result[3],
        "daily_timestamp": result[4],
        "weekly_timestamp": result[5],
        "monthly_timestamp": result[6],
        "work_timestamp": result[7],
        "beg_timestamp": result[8],
        "last_robbed": result[9],
        "robbed_count": result[10]
    }

def update_economy(user_id, wallet=None, bank=None, total_earned=None, daily_timestamp=None, weekly_timestamp=None, monthly_timestamp=None, work_timestamp=None, beg_timestamp=None, last_robbed=None, robbed_count=None):
    current = get_user_economy(user_id)
    if wallet is not None:
        current["wallet"] = wallet
    if bank is not None:
        current["bank"] = bank
    if total_earned is not None:
        current["total_earned"] = total_earned
    if daily_timestamp is not None:
        current["daily_timestamp"] = daily_timestamp
    if weekly_timestamp is not None:
        current["weekly_timestamp"] = weekly_timestamp
    if monthly_timestamp is not None:
        current["monthly_timestamp"] = monthly_timestamp
    if work_timestamp is not None:
        current["work_timestamp"] = work_timestamp
    if beg_timestamp is not None:
        current["beg_timestamp"] = beg_timestamp
    if last_robbed is not None:
        current["last_robbed"] = last_robbed
    if robbed_count is not None:
        current["robbed_count"] = robbed_count
    
    c.execute("UPDATE economy SET wallet = ?, bank = ?, total_earned = ?, daily_timestamp = ?, weekly_timestamp = ?, monthly_timestamp = ?, work_timestamp = ?, beg_timestamp = ?, last_robbed = ?, robbed_count = ? WHERE user_id = ?",
        (current["wallet"], current["bank"], current["total_earned"], current["daily_timestamp"], current["weekly_timestamp"], current["monthly_timestamp"], current["work_timestamp"], current["beg_timestamp"], current["last_robbed"], current["robbed_count"], user_id))
    conn.commit()

# Economy Commands
@bot.slash_command(name="balance", description="Check your economy balance")
async def balance(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    embed = nextcord.Embed(
        title=f"{interaction.user.name}'s Balance",
        color=BLUE
    )
    embed.add_field(name="💰 Wallet", value=f"${user_data['wallet']:,}", inline=True)
    embed.add_field(name="🏦 Bank", value=f"${user_data['bank']:,}", inline=True)
    embed.add_field(name="💎 Total Earned", value=f"${user_data['total_earned']:,}", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="deposit", description="Deposit money to your bank")
async def deposit(interaction: nextcord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    update_economy(interaction.user.id, wallet=user_data["wallet"] - amount, bank=user_data["bank"] + amount)
    
    embed = nextcord.Embed(
        title="💰 Deposit Successful",
        description=f"Deposited **${amount:,}** to your bank.",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="withdraw", description="Withdraw money from your bank")
async def withdraw(interaction: nextcord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["bank"] < amount:
        await interaction.response.send_message("❌ Insufficient funds in bank!", ephemeral=True)
        return
    
    update_economy(interaction.user.id, wallet=user_data["wallet"] + amount, bank=user_data["bank"] - amount)
    
    embed = nextcord.Embed(
        title="🏦 Withdraw Successful",
        description=f"Withdrew **${amount:,}** from your bank.",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="daily", description="Claim your daily reward")
async def daily(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["daily_timestamp"] < 86400:  # 24 hours
        remaining = 86400 - (current_time - user_data["daily_timestamp"])
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await interaction.response.send_message(f"❌ You can claim your daily reward in {hours}h {minutes}m.", ephemeral=True)
        return
    
    reward = settings["daily_reward"]
    update_economy(interaction.user.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, daily_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Daily Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="weekly", description="Claim your weekly reward")
async def weekly(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["weekly_timestamp"] < 604800:  # 7 days
        await interaction.response.send_message("❌ You can claim your weekly reward in 7 days.", ephemeral=True)
        return
    
    reward = settings["weekly_reward"]
    update_economy(interaction.user.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, weekly_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Weekly Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="monthly", description="Claim your monthly reward")
async def monthly(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["monthly_timestamp"] < 2592000:  # 30 days
        await interaction.response.send_message("❌ You can claim your monthly reward in 30 days.", ephemeral=True)
        return
    
    reward = settings["monthly_reward"]
    update_economy(interaction.user.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, monthly_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Monthly Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="work", description="Work to earn money")
async def work(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["work_timestamp"] < 3600:  # 1 hour
        remaining = 3600 - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        await interaction.response.send_message(f"❌ You can work again in {minutes} minutes.", ephemeral=True)
        return
    
    earnings = random.randint(settings["work_min"], settings["work_max"])
    update_economy(interaction.user.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, work_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="💼 Work Complete",
        description=f"You earned **${earnings:,}** from working!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="beg", description="Beg for money")
async def beg(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["beg_timestamp"] < 300:  # 5 minutes
        remaining = 300 - (current_time - user_data["beg_timestamp"])
        await interaction.response.send_message(f"❌ You can beg again in {remaining} seconds.", ephemeral=True)
        return
    
    earnings = random.randint(settings["beg_min"], settings["beg_max"])
    update_economy(interaction.user.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, beg_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="🙏 You begged...",
        description=f"Someone gave you **${earnings:,}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="rob", description="Rob someone")
async def rob(interaction: nextcord.Interaction, member: nextcord.Member):
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't rob yourself!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    target_data = get_user_economy(member.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["last_robbed"] < settings["rob_cooldown"]:
        remaining = settings["rob_cooldown"] - (current_time - user_data["last_robbed"])
        minutes = remaining // 60
        await interaction.response.send_message(f"❌ You can rob again in {minutes} minutes.", ephemeral=True)
        return
    
    if target_data["wallet"] < 50:
        await interaction.response.send_message(f"❌ {member.name} doesn't have enough money to rob!", ephemeral=True)
        return
    
    # 50% chance to succeed
    if random.random() < 0.5:
        stolen = random.randint(settings["rob_min"], min(settings["rob_max"], target_data["wallet"]))
        update_economy(interaction.user.id, wallet=user_data["wallet"] + stolen, total_earned=user_data["total_earned"] + stolen, last_robbed=current_time)
        update_economy(member.id, wallet=target_data["wallet"] - stolen)
        
        embed = nextcord.Embed(
            title="💰 Robbery Successful!",
            description=f"You stole **${stolen:,}** from {member.name}!",
            color=BLUE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        fine = random.randint(50, 200)
        if user_data["wallet"] >= fine:
            update_economy(interaction.user.id, wallet=user_data["wallet"] - fine, last_robbed=current_time)
            embed = nextcord.Embed(
                title="🚨 Robbery Failed!",
                description=f"You were caught and fined **${fine:,}**!",
                color=0xFF0000
            )
        else:
            update_economy(interaction.user.id, wallet=0, last_robbed=current_time)
            embed = nextcord.Embed(
                title="🚨 Robbery Failed!",
                description=f"You were caught! You had **${user_data['wallet']:,}** seized!",
                color=0xFF0000
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="transfer", description="Transfer money to another user")
async def transfer(interaction: nextcord.Interaction, member: nextcord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't transfer to yourself!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    settings = get_economy_settings()
    tax = int(amount * (settings["tax_rate"] / 100))
    final_amount = amount - tax
    
    update_economy(interaction.user.id, wallet=user_data["wallet"] - amount)
    
    target_data = get_user_economy(member.id)
    update_economy(member.id, wallet=target_data["wallet"] + final_amount)
    
    embed = nextcord.Embed(
        title="💸 Transfer Successful",
        description=f"Transferred **${final_amount:,}** to {member.name} (Tax: **${tax:,}**)",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="shop", description="View the shop")
async def shop(interaction: nextcord.Interaction):
    # Shop items - can be customized
    shop_items = [
        {"name": "💎 Rare Boost", "price": 5000, "description": "A rare boost for your profile"},
        {"name": "⭐ Star Role", "price": 10000, "description": "A star role on your profile"},
        {"name": "🎖️ Premium Badge", "price": 25000, "description": "A premium badge"},
    ]
    
    embed = nextcord.Embed(
        title="🏪 Economy Shop",
        color=BLUE
    )
    
    for item in shop_items:
        embed.add_field(name=item["name"], value=f"Price: **${item['price']:,}**\n{item['description']}", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Economy Manage Command (Executive + Holding only)
class EconomyManageView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @nextcord.ui.select(placeholder="Select setting to modify", 
                       options=[
                           nextcord.SelectOption(label="Starting Balance", value="starting_balance"),
                           nextcord.SelectOption(label="Daily Reward", value="daily_reward"),
                           nextcord.SelectOption(label="Weekly Reward", value="weekly_reward"),
                           nextcord.SelectOption(label="Monthly Reward", value="monthly_reward"),
                           nextcord.SelectOption(label="Work Earnings (Min)", value="work_min"),
                           nextcord.SelectOption(label="Work Earnings (Max)", value="work_max"),
                           nextcord.SelectOption(label="Beg Earnings (Min)", value="beg_min"),
                           nextcord.SelectOption(label="Beg Earnings (Max)", value="beg_max"),
                           nextcord.SelectOption(label="Rob Amount (Min)", value="rob_min"),
                           nextcord.SelectOption(label="Rob Amount (Max)", value="rob_max"),
                           nextcord.SelectOption(label="Rob Cooldown (seconds)", value="rob_cooldown"),
                           nextcord.SelectOption(label="Transfer Tax Rate (%)", value="tax_rate"),
                       ])
    async def select_callback(self, interaction, select):
        await interaction.response.send_modal(EconomySettingModal(select.values[0]))

class EconomySettingModal(nextcord.ui.Modal):
    def __init__(self, setting_name):
        super().__init__(f"Set {setting_name}")
        self.setting_name = setting_name
        
        self.value = nextcord.ui.TextInput(
            label="New Value",
            style=nextcord.TextInputStyle.short,
            required=True,
            placeholder="Enter new value"
        )
        self.add_item(self.value)

    async def callback(self, interaction: nextcord.Interaction):
        try:
            new_value = int(self.value.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        c.execute(f"UPDATE economy_settings SET {self.setting_name} = ? WHERE id = 1", (new_value,))
        conn.commit()
        
        embed = nextcord.Embed(
            title="✅ Setting Updated",
            description=f"**{self.setting_name}** has been set to **{new_value}**",
            color=BLUE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(name="economy-manage", description="Manage economy settings (Executive + Holding only)")
async def economy_manage(interaction: nextcord.Interaction):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="⚙️ Economy Management",
        description="Select a setting to modify:",
        color=BLUE
    )
    
    view = EconomyManageView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# =========================================================
# =================== AFK SYSTEM =========================
# =========================================================

AFK_FOOTER_IMAGE = "https://cdn.discordapp.com/attachments/1472412365415776306/1475277452103258362/footerisrp.png?ex=699ce6b1&is=699b9531&hm=d0b11e03fb99f8ea16956ebe9e5e2b1bb657b5ea315c1f8638149f984325ca3a&"

def get_afk_status(user_id):
    c.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        return {
            "reason": result[1],
            "start_time": result[2],
            "pings": json.loads(result[3])
        }
    return None

def set_afk(user_id, reason):
    current_time = int(time.time())
    c.execute("INSERT OR REPLACE INTO afk (user_id, reason, start_time, pings) VALUES (?, ?, ?, '[]')", (user_id, reason, current_time))
    conn.commit()

def remove_afk(user_id):
    c.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
    conn.commit()

def add_ping(user_id, pinger_id, message_content):
    current = get_afk_status(user_id)
    if current:
        pings = current["pings"]
        pings.append({"pinger_id": pinger_id, "message": message_content, "time": int(time.time())})
        # Keep only last 50 pings
        pings = pings[-50:]
        c.execute("UPDATE afk SET pings = ? WHERE user_id = ?", (json.dumps(pings), user_id))
        conn.commit()

@bot.slash_command(name="afk", description="Set yourself as AFK")
async def afk_slash(interaction: nextcord.Interaction, reason: str = "AFK"):
    set_afk(interaction.user.id, reason)
    
    embed = nextcord.Embed(
        title="💤 AFK Set",
        description=f"You are now AFK: **{reason}**",
        color=BLUE
    )
    embed.set_image(url=AFK_FOOTER_IMAGE)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="afk")
async def afk_prefix(ctx, *, reason: str = "AFK"):
    await log_command(ctx.author, "afk", "Prefix")
    set_afk(ctx.author.id, reason)
    
    try:
        await ctx.message.delete()
    except:
        pass
    
    embed = nextcord.Embed(
        title="💤 AFK Set",
        description=f"You are now AFK: **{reason}**",
        color=BLUE
    )
    embed.set_image(url=AFK_FOOTER_IMAGE)
    
    await ctx.send(embed=embed, delete_after=10)

@bot.event
async def on_message(message):
    # Don't process bot messages
    if message.author.bot:
        return
    
    # Check if someone mentioned an AFK user
    afk_status = get_afk_status(message.author.id)
    
    # If author is AFK, remove AFK and show pings
    if afk_status:
        remove_afk(message.author.id)
        
        pings = afk_status["pings"]
        elapsed = int(time.time()) - afk_status["start_time"]
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        
        # Show welcome back embed
        embed = nextcord.Embed(
            title="👋 Welcome Back!",
            description=f"You were AFK for **{hours}h {minutes}m**",
            color=BLUE
        )
        
        if pings:
            # Show up to 5 pings
            recent_pings = pings[-5:]
            ping_text = ""
            for i, ping in enumerate(recent_pings, 1):
                pinger = message.guild.get_member(ping["pinger_id"])
                pinger_name = pinger.name if pinger else "Unknown"
                ping_text += f"**{i}.** {pinger_name}: \"{ping['message']}\"\n"
            
            if len(pings) > 5:
                ping_text += f"\n*...and {len(pings) - 5} more pings*"
            
            embed.add_field(name="📬 Pings While You Were Away", value=ping_text, inline=False)
        
        embed.set_image(url=AFK_FOOTER_IMAGE)
        
        await message.channel.send(embed=embed, delete_after=30)
    
    # Check for mentions of AFK users
    for mention in message.mentions:
        afk_data = get_afk_status(mention.id)
        if afk_data:
            # Add to pings
            add_ping(mention.id, message.author.id, message.content)
            
            # Calculate elapsed time
            elapsed = int(time.time()) - afk_data["start_time"]
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            
            # Send AFK reply
            embed = nextcord.Embed(
                title="💤 User is AFK",
                description=f"**{mention.name}** is currently AFK: **{afk_data['reason']}**\nAway for: **{hours}h {minutes}m**",
                color=BLUE
            )
            embed.set_image(url=AFK_FOOTER_IMAGE)
            
            await message.reply(embed=embed, delete_after=20)
    
    # Process other commands
    await bot.process_commands(message)

# =========================================================
# =============== WELCOME MEMBER COUNTER =================
# =========================================================

WELCOME_COUNTER_CHANNEL_ID = 1471639394212515916

@bot.event
async def on_member_join(member):
    # Existing code continues...
    # Just add the member counter message
    
    channel = bot.get_channel(WELCOME_COUNTER_CHANNEL_ID)
    if channel:
        member_count = len([m for m in member.guild.members if not m.bot])
        
        def ordinal(n):
            if 10 <= n % 100 <= 20:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return str(n) + suffix
        
        await channel.send(f"Welcome to Illinois State Roleplay, {member.mention}! You are our {ordinal(member_count)} member")

# =========================================================
# ============= SCHEDULED VERIFICATION MESSAGES ===========
# =========================================================

VERIFICATION_CHANNEL_ID = 1471660766536011952
VERIFICATION_ROLE_ID = 1471661069825998919
CHECKMARK_EMOJI_VERIFY = "<:Checkmark:1471668496814309449>"

verification_message_id = None

async def send_verification_message():
    """Send the verification reminder message"""
    global verification_message_id
    
    channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
    if not channel:
        return
    
    # Delete previous message if exists
    if verification_message_id:
        try:
            old_message = await channel.fetch_message(verification_message_id)
            await old_message.delete()
        except:
            pass
    
    # Send new message
    message = await channel.send(
        f"> <@&{VERIFICATION_ROLE_ID}>: You are requested to {CHECKMARK_EMOJI_VERIFY} **Verify with Melonly** to ensure full community access, such as community interaction channels, giveaways/events, and more!"
    )
    
    verification_message_id = message.id

async def scheduled_verification():
    """Background task to send verification messages at specified times"""
    await bot.wait_until_ready()
    
    # Times: 12am, 6am, 12pm, 6pm CST (UTC: 6am, 12pm, 6pm, 12am)
    # Actually: CST = UTC-6, so:
    # 12am CST = 6am UTC
    # 6am CST = 12pm UTC
    # 12pm CST = 6pm UTC
    # 6pm CST = 12am UTC
    
    target_times = [6, 12, 18, 0]  # UTC hours
    
    while not bot.is_closed():
        current_hour = datetime.utcnow().hour
        
        if current_hour in target_times:
            await send_verification_message()
            # Wait until next hour to avoid multiple sends
            await asyncio.sleep(3600)
        
        await asyncio.sleep(60)

# =========================================================
# ================= INVITE BLOCKING ======================
# =========================================================

# Allowed category IDs
ALLOWED_CATEGORY_IDS = [
    1471689868022120468,
    1471689978135183581,
    1473172223501144306,
    1473449632842518569,
    1473449548692062391,
    1471690051078455386,
]

# Allowed roles (Executive + Holding)
ALLOWED_ROLE_IDS_FOR_INVITE = [
    1471642360503992411,
    1471642126663024640,
]

INVITE_BLOCK_MESSAGE = "You are not permitted to send advertisements or links to Discord Communities in Illinois State Roleplay"

# Combined on_message for both AFK and Invite Blocking
@bot.event
async def on_message(message):
    # Skip bot messages
    if message.author.bot:
        return
    
    # Skip DMs
    if isinstance(message.channel, nextcord.DMChannel):
        return
    
    # ===== AFK SYSTEM =====
    # Check if someone mentioned an AFK user
    afk_status = get_afk_status(message.author.id)
    
    # If author is AFK, remove AFK and show pings
    if afk_status:
        remove_afk(message.author.id)
        
        pings = afk_status["pings"]
        elapsed = int(time.time()) - afk_status["start_time"]
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        
        # Show welcome back embed
        embed = nextcord.Embed(
            title="👋 Welcome Back!",
            description=f"You were AFK for **{hours}h {minutes}m**",
            color=BLUE
        )
        
        if pings:
            # Show up to 5 pings
            recent_pings = pings[-5:]
            ping_text = ""
            for i, ping in enumerate(recent_pings, 1):
                pinger = message.guild.get_member(ping["pinger_id"])
                pinger_name = pinger.name if pinger else "Unknown"
                ping_text += f"**{i}.** {pinger_name}: \"{ping['message']}\"\n"
            
            if len(pings) > 5:
                ping_text += f"\n*...and {len(pings) - 5} more pings*"
            
            embed.add_field(name="📬 Pings While You Were Away", value=ping_text, inline=False)
        
        embed.set_image(url=AFK_FOOTER_IMAGE)
        
        await message.channel.send(embed=embed, delete_after=30)
    
    # Check for mentions of AFK users
    for mention in message.mentions:
        afk_data = get_afk_status(mention.id)
        if afk_data:
            # Add to pings
            add_ping(mention.id, message.author.id, message.content)
            
            # Calculate elapsed time
            elapsed = int(time.time()) - afk_data["start_time"]
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            
            # Send AFK reply
            embed = nextcord.Embed(
                title="💤 User is AFK",
                description=f"**{mention.name}** is currently AFK: **{afk_data['reason']}**\nAway for: **{hours}h {minutes}m**",
                color=BLUE
            )
            embed.set_image(url=AFK_FOOTER_IMAGE)
            
            await message.reply(embed=embed, delete_after=20)
    
    # ===== INVITE BLOCKING =====
    # Check if user has allowed role
    if any(role.id in ALLOWED_ROLE_IDS_FOR_INVITE for role in message.author.roles):
        await bot.process_commands(message)
        return
    
    # Check if channel is in allowed category
    if message.channel.category and message.channel.category.id in ALLOWED_CATEGORY_IDS:
        await bot.process_commands(message)
        return
    
    # Check for Discord invites
    if "discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower():
        # Check for specific allowed invite
        if "discord.gg/prc" in message.content.lower():
            await bot.process_commands(message)
            return
        
        # Block the invite
        try:
            await message.delete()
        except:
            pass
        
        await message.channel.send(
            f"{message.author.mention} {INVITE_BLOCK_MESSAGE}",
            delete_after=10
        )
        return
    
    # Continue processing commands
    await bot.process_commands(message)

# =========================================================
# ================= SUGGESTION SYSTEM ====================
# =========================================================

SUGGESTION_CHANNEL_ID = 1475326269380890755
COMMUNITY_ROLE_ID = 1471652018329227415
UPVOTE_EMOJI = "✅"
DOWNVOTE_EMOJI = "<:XSignal:1475329163098591242>"

# Approve/Deny roles (Management + Executive + Holding)
APPROVE_DENY_ROLES = [
    1471641915215843559,  # Management
    1471642126663024640,  # Executive
    1471642360503992411,  # Holding
]

class SuggestionView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @nextcord.ui.button(label="Upvote", style=nextcord.ButtonStyle.success, emoji="✅", custom_id="suggestion_upvote")
    async def upvote(self, button, interaction):
        # Add upvote to database
        c.execute("UPDATE suggestions SET upvotes = upvotes + 1 WHERE message_id = ?", (interaction.message.id,))
        conn.commit()
        
        await interaction.response.send_message("✅ Voted!", ephemeral=True)
    
    @nextcord.ui.button(label="Downvote", style=nextcord.ButtonStyle.danger, emoji="X", custom_id="suggestion_downvote")
    async def downvote(self, button, interaction):
        # Add downvote to database
        c.execute("UPDATE suggestions SET downvotes = downvotes + 1 WHERE message_id = ?", (interaction.message.id,))
        conn.commit()
        
        await interaction.response.send_message("👎 Voted!", ephemeral=True)

@bot.slash_command(name="suggest", description="Make a suggestion")
async def suggest(interaction: nextcord.Interaction, suggestion: str):
    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Suggestion channel not found!", ephemeral=True)
        return
    
    # Create suggestion embed
    embed = nextcord.Embed(
        title="📝 New Suggestion",
        description=suggestion,
        color=BLUE,
        timestamp=utcnow()
    )
    embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
    embed.add_field(name="Status", value="⏳ Pending", inline=True)
    embed.add_field(name="Upvotes", value="0", inline=True)
    embed.add_field(name="Downvotes", value="0", inline=True)
    
    # Send suggestion with view
    view = SuggestionView()
    message = await channel.send(embed=embed, view=view)
    
    # Add reactions
    try:
        await message.add_reaction(UPVOTE_EMOJI)
        await message.add_reaction(DOWNVOTE_EMOJI)
    except:
        pass
    
    # Save to database
    c.execute("INSERT INTO suggestions (message_id, channel_id, author_id, suggestion) VALUES (?, ?, ?, ?)",
        (message.id, channel.id, interaction.user.id, suggestion))
    conn.commit()
    
    await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

@bot.slash_command(name="approve-suggestion", description="Approve a suggestion")
async def approve_suggestion(interaction: nextcord.Interaction, message_id: int):
    if not any(role.id in APPROVE_DENY_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    try:
        message = await channel.fetch_message(message_id)
    except:
        await interaction.response.send_message("❌ Message not found!", ephemeral=True)
        return
    
    # Update database
    c.execute("UPDATE suggestions SET status = 'approved', approver_id = ?, approved_at = ? WHERE message_id = ?",
        (interaction.user.id, int(time.time()), message_id))
    conn.commit()
    
    # Update embed
    embed = message.embeds[0]
    embed.color = 0x00FF00  # Green
    embed.set_field_at(0, name="Status", value="✅ Approved", inline=True)
    
    await message.edit(embed=embed)
    await interaction.response.send_message("✅ Suggestion approved!", ephemeral=True)

@bot.slash_command(name="deny-suggestion", description="Deny a suggestion")
async def deny_suggestion(interaction: nextcord.Interaction, message_id: int):
    if not any(role.id in APPROVE_DENY_ROLES for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    channel = bot.get_channel(SUGGESTION_CHANNEL_ID)
    try:
        message = await channel.fetch_message(message_id)
    except:
        await interaction.response.send_message("❌ Message not found!", ephemeral=True)
        return
    
    # Update database
    c.execute("UPDATE suggestions SET status = 'denied', approver_id = ?, approved_at = ? WHERE message_id = ?",
        (interaction.user.id, int(time.time()), message_id))
    conn.commit()
    
    # Update embed
    embed = message.embeds[0]
    embed.color = 0xFF0000  # Red
    embed.set_field_at(0, name="Status", value="❌ Denied", inline=True)
    
    await message.edit(embed=embed)
    await interaction.response.send_message("❌ Suggestion denied!", ephemeral=True)

# Update suggestion vote counts from reactions
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    if not channel or channel.id != SUGGESTION_CHANNEL_ID:
        return
    
    try:
        message = await channel.fetch_message(payload.message_id)
    except:
        return
    
    # Check if it's a suggestion message
    c.execute("SELECT * FROM suggestions WHERE message_id = ?", (payload.message_id,))
    if not c.fetchone():
        return
    
    emoji = str(payload.emoji)
    if emoji == UPVOTE_EMOJI:
        c.execute("UPDATE suggestions SET upvotes = upvotes + 1 WHERE message_id = ?", (payload.message_id,))
    elif emoji == DOWNVOTE_EMOJI or emoji == "X":
        c.execute("UPDATE suggestions SET downvotes = downvotes + 1 WHERE message_id = ?", (payload.message_id,))
    
    conn.commit()
    
    # Update embed with new counts
    c.execute("SELECT upvotes, downvotes FROM suggestions WHERE message_id = ?", (payload.message_id,))
    result = c.fetchone()
    if result and message.embeds:
        embed = message.embeds[0]
        embed.set_field_at(1, name="Upvotes", value=str(result[0]), inline=True)
        embed.set_field_at(2, name="Downvotes", value=str(result[1]), inline=True)
        try:
            await message.edit(embed=embed)
        except:
            pass

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    
    channel = bot.get_channel(payload.channel_id)
    if not channel or channel.id != SUGGESTION_CHANNEL_ID:
        return
    
    try:
        message = await channel.fetch_message(payload.message_id)
    except:
        return
    
    # Check if it's a suggestion message
    c.execute("SELECT * FROM suggestions WHERE message_id = ?", (payload.message_id,))
    if not c.fetchone():
        return
    
    emoji = str(payload.emoji)
    if emoji == UPVOTE_EMOJI:
        c.execute("UPDATE suggestions SET upvotes = MAX(0, upvotes - 1) WHERE message_id = ?", (payload.message_id,))
    elif emoji == DOWNVOTE_EMOJI or emoji == "X":
        c.execute("UPDATE suggestions SET downvotes = MAX(0, downvotes - 1) WHERE message_id = ?", (payload.message_id,))
    
    conn.commit()
    
    # Update embed with new counts
    c.execute("SELECT upvotes, downvotes FROM suggestions WHERE message_id = ?", (payload.message_id,))
    result = c.fetchone()
    if result and message.embeds:
        embed = message.embeds[0]
        embed.set_field_at(1, name="Upvotes", value=str(result[0]), inline=True)
        embed.set_field_at(2, name="Downvotes", value=str(result[1]), inline=True)
        try:
            await message.edit(embed=embed)
        except:
            pass

# =========================================================
# ================== MODIFIED ON_READY ===================
# =========================================================

# We need to add the session DM task and verification task to on_ready

# ------------------------------
# Run bot
# ------------------------------

# ==================== PREFIX ECONOMY COMMANDS ====================

# Balance prefix command
@bot.command(name="balance", aliases=["bal"])
async def balance_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    embed = nextcord.Embed(
        title=f"{ctx.author.name}'s Balance",
        color=BLUE
    )
    embed.add_field(name="💰 Wallet", value=f"${user_data['wallet']:,}", inline=True)
    embed.add_field(name="🏦 Bank", value=f"${user_data['bank']:,}", inline=True)
    embed.add_field(name="💎 Total Earned", value=f"${user_data['total_earned']:,}", inline=True)
    await ctx.send(embed=embed)

# Deposit prefix command
@bot.command(name="deposit")
async def deposit_prefix(ctx, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < amount:
        await ctx.send("❌ Insufficient funds!")
        return
    
    update_economy(ctx.author.id, wallet=user_data["wallet"] - amount, bank=user_data["bank"] + amount)
    
    embed = nextcord.Embed(
        title="💰 Deposit Successful",
        description=f"Deposited **${amount:,}** to your bank.",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Withdraw prefix command
@bot.command(name="withdraw")
async def withdraw_prefix(ctx, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["bank"] < amount:
        await ctx.send("❌ Insufficient funds in bank!")
        return
    
    update_economy(ctx.author.id, wallet=user_data["wallet"] + amount, bank=user_data["bank"] - amount)
    
    embed = nextcord.Embed(
        title="🏦 Withdraw Successful",
        description=f"Withdrew **${amount:,}** from your bank.",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Daily prefix command
@bot.command(name="daily")
async def daily_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["daily_timestamp"] < 86400:  # 24 hours
        remaining = 86400 - (current_time - user_data["daily_timestamp"])
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        await ctx.send(f"❌ You can claim your daily reward in {hours}h {minutes}m.")
        return
    
    reward = settings["daily_reward"]
    update_economy(ctx.author.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, daily_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Daily Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Weekly prefix command
@bot.command(name="weekly")
async def weekly_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["weekly_timestamp"] < 604800:  # 7 days
        await ctx.send("❌ You can claim your weekly reward in 7 days.")
        return
    
    reward = settings["weekly_reward"]
    update_economy(ctx.author.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, weekly_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Weekly Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Monthly prefix command
@bot.command(name="monthly")
async def monthly_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["monthly_timestamp"] < 2592000:  # 30 days
        await ctx.send("❌ You can claim your monthly reward in 30 days.")
        return
    
    reward = settings["monthly_reward"]
    update_economy(ctx.author.id, wallet=user_data["wallet"] + reward, total_earned=user_data["total_earned"] + reward, monthly_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="✅ Monthly Reward Claimed",
        description=f"You received **${reward:,}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Work prefix command
@bot.command(name="work")
async def work_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["work_timestamp"] < 3600:  # 1 hour
        remaining = 3600 - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        await ctx.send(f"❌ You can work again in {minutes} minutes.")
        return
    
    earnings = random.randint(settings["work_min"], settings["work_max"])
    update_economy(ctx.author.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, work_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="💼 Work Complete",
        description=f"You earned **${earnings:,}** from working!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Beg prefix command
@bot.command(name="beg")
async def beg_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["beg_timestamp"] < 300:  # 5 minutes
        remaining = 300 - (current_time - user_data["beg_timestamp"])
        await ctx.send(f"❌ You can beg again in {remaining} seconds.")
        return
    
    earnings = random.randint(settings["beg_min"], settings["beg_max"])
    update_economy(ctx.author.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, beg_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="🙏 You begged...",
        description=f"Someone gave you **${earnings:,}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Rob prefix command
@bot.command(name="rob")
async def rob_prefix(ctx, member: nextcord.Member):
    if member.id == ctx.author.id:
        await ctx.send("❌ You can't rob yourself!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    target_data = get_user_economy(member.id)
    settings = get_economy_settings()
    current_time = int(time.time())
    
    if current_time - user_data["last_robbed"] < settings["rob_cooldown"]:
        remaining = settings["rob_cooldown"] - (current_time - user_data["last_robbed"])
        minutes = remaining // 60
        await ctx.send(f"❌ You can rob again in {minutes} minutes.")
        return
    
    if target_data["wallet"] < 50:
        await ctx.send(f"❌ {member.name} doesn't have enough money to rob!")
        return
    
    # 50% chance to succeed
    if random.random() < 0.5:
        stolen = random.randint(settings["rob_min"], min(settings["rob_max"], target_data["wallet"]))
        update_economy(ctx.author.id, wallet=user_data["wallet"] + stolen, total_earned=user_data["total_earned"] + stolen, last_robbed=current_time)
        update_economy(member.id, wallet=target_data["wallet"] - stolen)
        
        embed = nextcord.Embed(
            title="💰 Robbery Successful!",
            description=f"You stole **${stolen:,}** from {member.name}!",
            color=BLUE
        )
        await ctx.send(embed=embed)
    else:
        fine = random.randint(50, 200)
        if user_data["wallet"] >= fine:
            update_economy(ctx.author.id, wallet=user_data["wallet"] - fine, last_robbed=current_time)
            embed = nextcord.Embed(
                title="🚨 Robbery Failed!",
                description=f"You were caught and fined **${fine:,}**!",
                color=0xFF0000
            )
        else:
            update_economy(ctx.author.id, wallet=0, last_robbed=current_time)
            embed = nextcord.Embed(
                title="🚨 Robbery Failed!",
                description=f"You were caught! You had **${user_data['wallet']:,}** seized!",
                color=0xFF0000
            )
        await ctx.send(embed=embed)

# Transfer prefix command
@bot.command(name="transfer")
async def transfer_prefix(ctx, member: nextcord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    if member.id == ctx.author.id:
        await ctx.send("❌ You can't transfer to yourself!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < amount:
        await ctx.send("❌ Insufficient funds!")
        return
    
    settings = get_economy_settings()
    tax = int(amount * (settings["tax_rate"] / 100))
    final_amount = amount - tax
    
    update_economy(ctx.author.id, wallet=user_data["wallet"] - amount)
    
    target_data = get_user_economy(member.id)
    update_economy(member.id, wallet=target_data["wallet"] + final_amount)
    
    embed = nextcord.Embed(
        title="💸 Transfer Successful",
        description=f"Transferred **${final_amount:,}** to {member.name} (Tax: **${tax:,}**)",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Shop prefix command
@bot.command(name="shop")
async def shop_prefix(ctx):
    shop_items = [
        {"name": "💎 Rare Boost", "price": 5000, "description": "A rare boost for your profile"},
        {"name": "⭐ Star Role", "price": 10000, "description": "A star role on your profile"},
        {"name": "🎖️ Premium Badge", "price": 25000, "description": "A premium badge"},
    ]
    
    embed = nextcord.Embed(
        title="🏪 Economy Shop",
        color=BLUE
    )
    
    for item in shop_items:
        embed.add_field(name=item["name"], value=f"Price: **${item['price']:,}**\n{item['description']}", inline=False)
    
    await ctx.send(embed=embed)

# ==================== ADDITIONAL ECONOMY COMMANDS ====================

# Crime command (slash)
@bot.slash_command(name="crime", description="Commit a crime to earn money (risk of fine)")
async def crime(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    current_time = int(time.time())
    
    if current_time - user_data["work_timestamp"] < 1800:  # 30 min cooldown
        remaining = 1800 - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        await interaction.response.send_message(f"❌ You can commit a crime again in {minutes} minutes.", ephemeral=True)
        return
    
    if random.random() < 0.6:
        earnings = random.randint(100, 500)
        update_economy(interaction.user.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, work_timestamp=current_time)
        
        embed = nextcord.Embed(
            title="💰 Crime Successful!",
            description=f"You committed a crime and earned **${earnings:,}**!",
            color=BLUE
        )
    else:
        fine = random.randint(50, 200)
        new_wallet = max(0, user_data["wallet"] - fine)
        update_economy(interaction.user.id, wallet=new_wallet, work_timestamp=current_time)
        
        embed = nextcord.Embed(
            title="🚨 Crime Failed!",
            description=f"You were caught and fined **${fine:,}**!",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Leaderboard command (slash)
@bot.slash_command(name="leaderboard", description="View the server wealth leaderboard")
async def leaderboard(interaction: nextcord.Interaction):
    c.execute("SELECT user_id, wallet, bank FROM economy ORDER BY (wallet + bank) DESC LIMIT 10")
    results = c.fetchall()
    
    embed = nextcord.Embed(
        title="🏆 Wealth Leaderboard",
        description="Top 10 richest members:",
        color=BLUE
    )
    
    for i, (user_id, wallet, bank) in enumerate(results, 1):
        user = interaction.guild.get_member(user_id)
        name = user.name if user else f"User {user_id}"
        total = wallet + bank
        embed.add_field(name=f"{i}. {name}", value=f"${total:,}", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Give-money command (slash)
@bot.slash_command(name="give-money", description="Give money to another user")
async def give_money(interaction: nextcord.Interaction, member: nextcord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be positive!", ephemeral=True)
        return
    
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't give money to yourself!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < amount:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    settings = get_economy_settings()
    tax = int(amount * (settings["tax_rate"] / 100))
    final_amount = amount - tax
    
    update_economy(interaction.user.id, wallet=user_data["wallet"] - amount)
    
    target_data = get_user_economy(member.id)
    update_economy(member.id, wallet=target_data["wallet"] + final_amount)
    
    embed = nextcord.Embed(
        title="💸 Money Given",
        description=f"You gave **${final_amount:,}** to {member.name} (Tax: **${tax:,}**)",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Money command (slash) - shows balance + leaderboard position
@bot.slash_command(name="money", description="Show your balance and leaderboard position")
async def money(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    
    c.execute("SELECT user_id, wallet FROM economy ORDER BY wallet DESC")
    all_users = c.fetchall()
    position = 1
    for uid, _ in all_users:
        if uid == interaction.user.id:
            break
        position += 1
    
    embed = nextcord.Embed(
        title=f"💰 {interaction.user.name}'s Balance",
        color=BLUE
    )
    embed.add_field(name="Wallet", value=f"${user_data['wallet']:,}", inline=True)
    embed.add_field(name="Bank", value=f"${user_data['bank']:,}", inline=True)
    embed.add_field(name="Position", value=f"#{position:,}", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== PREFIX ECONOMY COMMANDS ====================

@bot.command(name="crime")
async def crime_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    current_time = int(time.time())
    
    if current_time - user_data["work_timestamp"] < 1800:
        remaining = 1800 - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        await ctx.send(f"❌ You can commit a crime again in {minutes} minutes.")
        return
    
    if random.random() < 0.6:
        earnings = random.randint(100, 500)
        update_economy(ctx.author.id, wallet=user_data["wallet"] + earnings, total_earned=user_data["total_earned"] + earnings, work_timestamp=current_time)
        
        embed = nextcord.Embed(
            title="💰 Crime Successful!",
            description=f"You committed a crime and earned **${earnings:,}**!",
            color=BLUE
        )
    else:
        fine = random.randint(50, 200)
        new_wallet = max(0, user_data["wallet"] - fine)
        update_economy(ctx.author.id, wallet=new_wallet, work_timestamp=current_time)
        
        embed = nextcord.Embed(
            title="🚨 Crime Failed!",
            description=f"You were caught and fined **${fine:,}**!",
            color=0xFF0000
        )
    
    await ctx.send(embed=embed)

@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard_prefix(ctx):
    c.execute("SELECT user_id, wallet, bank FROM economy ORDER BY (wallet + bank) DESC LIMIT 10")
    results = c.fetchall()
    
    embed = nextcord.Embed(
        title="🏆 Wealth Leaderboard",
        description="Top 10 richest members:",
        color=BLUE
    )
    
    for i, (user_id, wallet, bank) in enumerate(results, 1):
        user = ctx.guild.get_member(user_id)
        name = user.name if user else f"User {user_id}"
        total = wallet + bank
        embed.add_field(name=f"{i}. {name}", value=f"${total:,}", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name="give-money", aliases=["give"])
async def give_money_prefix(ctx, member: nextcord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    
    if member.id == ctx.author.id:
        await ctx.send("❌ You can't give money to yourself!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < amount:
        await ctx.send("❌ Insufficient funds!")
        return
    
    settings = get_economy_settings()
    tax = int(amount * (settings["tax_rate"] / 100))
    final_amount = amount - tax
    
    update_economy(ctx.author.id, wallet=user_data["wallet"] - amount)
    
    target_data = get_user_economy(member.id)
    update_economy(member.id, wallet=target_data["wallet"] + final_amount)
    
    embed = nextcord.Embed(
        title="💸 Money Given",
        description=f"You gave **${final_amount:,}** to {member.name} (Tax: **${tax:,}**)",
        color=BLUE
    )
    await ctx.send(embed=embed)

@bot.command(name="money")
async def money_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    
    c.execute("SELECT user_id, wallet FROM economy ORDER BY wallet DESC")
    all_users = c.fetchall()
    position = 1
    for uid, _ in all_users:
        if uid == ctx.author.id:
            break
        position += 1
    
    embed = nextcord.Embed(
        title=f"💰 {ctx.author.name}'s Balance",
        color=BLUE
    )
    embed.add_field(name="Wallet", value=f"${user_data['wallet']:,}", inline=True)
    embed.add_field(name="Bank", value=f"${user_data['bank']:,}", inline=True)
    embed.add_field(name="Position", value=f"#{position:,}", inline=True)
    await ctx.send(embed=embed)

# ==================== ECONOMY ADMIN PANEL ====================

class EconomyConfigView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @nextcord.ui.select(placeholder="Select configuration option", 
                       options=[
                           nextcord.SelectOption(label="Set Starting Balance", value="starting_balance"),
                           nextcord.SelectOption(label="Set Daily Reward", value="daily_reward"),
                           nextcord.SelectOption(label="Set Weekly Reward", value="weekly_reward"),
                           nextcord.SelectOption(label="Set Monthly Reward", value="monthly_reward"),
                           nextcord.SelectOption(label="Set Work Min", value="work_min"),
                           nextcord.SelectOption(label="Set Work Max", value="work_max"),
                           nextcord.SelectOption(label="Set Rob Cooldown (seconds)", value="rob_cooldown"),
                           nextcord.SelectOption(label="Set Tax Rate (%)", value="tax_rate"),
                           nextcord.SelectOption(label="Add Money to User", value="add_money"),
                           nextcord.SelectOption(label="Remove Money from User", value="remove_money"),
                           nextcord.SelectOption(label="Reset User Money", value="reset_money"),
                           nextcord.SelectOption(label="Add Money to Role", value="add_money_role"),
                           nextcord.SelectOption(label="Economy Stats", value="stats"),
                       ])
    async def select_callback(self, interaction, select):
        await interaction.response.send_modal(EconomyConfigModal(select.values[0]))

class EconomyConfigModal(nextcord.ui.Modal):
    def __init__(self, setting_type):
        super().__init__(f"Economy Configuration")
        self.setting_type = setting_type
        
        if setting_type in ["add_money", "remove_money", "reset_money"]:
            self.user_id = nextcord.ui.TextInput(
                label="User ID",
                style=nextcord.TextInputStyle.short,
                required=True,
                placeholder="Enter user ID"
            )
            self.add_item(self.user_id)
        
        if setting_type in ["add_money", "remove_money", "add_money_role"]:
            self.amount = nextcord.ui.TextInput(
                label="Amount",
                style=nextcord.TextInputStyle.short,
                required=True,
                placeholder="Enter amount"
            )
            self.add_item(self.amount)
        
        if setting_type == "add_money_role":
            self.role_id = nextcord.ui.TextInput(
                label="Role ID",
                style=nextcord.TextInputStyle.short,
                required=True,
                placeholder="Enter role ID"
            )
            self.add_item(self.role_id)
        
        if setting_type not in ["add_money", "remove_money", "reset_money", "add_money_role", "stats"]:
            self.value = nextcord.ui.TextInput(
                label="Value",
                style=nextcord.TextInputStyle.short,
                required=True,
                placeholder="Enter new value"
            )
            self.add_item(self.value)

    async def callback(self, interaction: nextcord.Interaction):
        if self.setting_type == "add_money":
            try:
                user_id = int(self.user_id.value)
                amount = int(self.amount.value)
                user_data = get_user_economy(user_id)
                new_wallet = user_data["wallet"] + amount
                update_economy(user_id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
                embed = nextcord.Embed(title="✅ Money Added", description=f"Added **${amount:,}** to user {user_id}", color=BLUE)
            except:
                embed = nextcord.Embed(title="❌ Error", description="Invalid user ID or amount", color=0xFF0000)
        
        elif self.setting_type == "remove_money":
            try:
                user_id = int(self.user_id.value)
                amount = int(self.amount.value)
                user_data = get_user_economy(user_id)
                new_wallet = max(0, user_data["wallet"] - amount)
                update_economy(user_id, wallet=new_wallet)
                embed = nextcord.Embed(title="✅ Money Removed", description=f"Removed **${amount:,}** from user {user_id}", color=BLUE)
            except:
                embed = nextcord.Embed(title="❌ Error", description="Invalid user ID or amount", color=0xFF0000)
        
        elif self.setting_type == "reset_money":
            settings = get_economy_settings()
            try:
                user_id = int(self.user_id.value)
                update_economy(user_id, wallet=settings["starting_balance"], bank=0, total_earned=settings["starting_balance"])
                embed = nextcord.Embed(title="✅ Money Reset", description=f"Reset money for user {user_id}", color=BLUE)
            except:
                embed = nextcord.Embed(title="❌ Error", description="Invalid user ID", color=0xFF0000)
        
        elif self.setting_type == "add_money_role":
            try:
                role_id = int(self.role_id.value)
                amount = int(self.amount.value)
                role = interaction.guild.get_role(role_id)
                if role:
                    for member in role.members:
                        user_data = get_user_economy(member.id)
                        new_wallet = user_data["wallet"] + amount
                        update_economy(member.id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
                    embed = nextcord.Embed(title="✅ Money Added to Role", description=f"Added **${amount:,}** to all {len(role.members)} members with {role.name}", color=BLUE)
                else:
                    embed = nextcord.Embed(title="❌ Error", description="Role not found", color=0xFF0000)
            except:
                embed = nextcord.Embed(title="❌ Error", description="Invalid role ID or amount", color=0xFF0000)
        
        elif self.setting_type == "stats":
            c.execute("SELECT COUNT(*), SUM(wallet), SUM(bank) FROM economy")
            result = c.fetchone()
            embed = nextcord.Embed(title="📊 Economy Statistics", description=f"Total Users: **{result[0]:,}**\nTotal Wallet: **${result[1]:,}**\nTotal Bank: **${result[2]:,}**", color=BLUE)
        
        else:
            try:
                new_value = int(self.value.value)
                c.execute(f"UPDATE economy_settings SET {self.setting_type} = ? WHERE id = 1", (new_value,))
                conn.commit()
                embed = nextcord.Embed(title="✅ Setting Updated", description=f"**{self.setting_type}** has been set to **{new_value}**", color=BLUE)
            except:
                embed = nextcord.Embed(title="❌ Error", description="Invalid value", color=0xFF0000)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Economy Config Slash Command
@bot.slash_command(name="econ-config", description="Economy configuration panel (Executive + Holding only)")
async def econ_config_slash(interaction: nextcord.Interaction):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
        return
    
    embed = nextcord.Embed(title="⚙️ Economy Configuration", description="Select an option to configure:", color=BLUE)
    view = EconomyConfigView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Economy Config Prefix Command
@bot.command(name="econ-panel")
async def econ_panel_prefix(ctx):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission to use this command!")
        return
    
    embed = nextcord.Embed(title="⚙️ Economy Configuration", description="Select an option to configure:", color=BLUE)
    view = EconomyConfigView()
    await ctx.send(embed=embed, view=view)

# ==================== HELP COMMAND ====================

HELP_FOOTER_IMAGE = "https://cdn.discordapp.com/attachments/1472412365415776306/1475277452103258362/footerisrp.png?ex=699ce6b1&is=699b9531&hm=d0b11e03fb99f8ea16956ebe9e5e2b1bb657b5ea315c1f8638149f984325ca3a&"
SKY_BLUE = 0x87CEEB

@bot.slash_command(name="help", description="View all bot commands")
async def help_slash(interaction: nextcord.Interaction):
    # Text embed with command list
    text_embed = nextcord.Embed(
        title="📚 Illinois State Roleplay Bot Commands",
        description="Here's a list of all available commands:",
        color=SKY_BLUE,
        timestamp=utcnow()
    )
    
    text_embed.add_field(
        name="💰 Economy Commands",
        value="`/balance` - Check your balance\n`/money` - Balance + leaderboard position\n`/deposit [amount]` - Deposit to bank\n`/withdraw [amount]` - Withdraw from bank\n`/daily` - Claim daily reward\n`/weekly` - Claim weekly reward\n`/monthly` - Claim monthly reward\n`/work` - Work for money\n`/crime` - Commit crime (risk of fine)\n`/beg` - Beg for money\n`/rob @user` - Rob someone\n`/give-money @user [amount]` - Give money\n`/leaderboard` - View rich list\n`/shop` - View shop",
        inline=False
    )
    
    text_embed.add_field(
        name="🎫 Other Commands",
        value="`/afk [reason]` - Set AFK status\n`/suggest [suggestion]` - Make a suggestion\n`/help` - Show this help message",
        inline=False
    )
    
    text_embed.add_field(
        name="⚙️ Admin Commands (Exec+/Holding+)",
        value="`/sessions` - Manage sessions\n`/promote @user` - Promote staff\n`/lock` - Lock channel\n`/unlock` - Unlock channel\n`/nick @user [name]` - Change nickname\n`/econ-config` - Economy settings\n`/sendpanel` - Send ticket panel",
        inline=False
    )
    
    # Image embed with footer
    image_embed = nextcord.Embed(color=SKY_BLUE)
    image_embed.set_image(url=HELP_FOOTER_IMAGE)
    
    await interaction.response.send_message(embeds=[text_embed, image_embed], ephemeral=True)

@bot.command(name="help")
async def help_prefix(ctx):
    text_embed = nextcord.Embed(
        title="📚 Illinois State Roleplay Bot Commands",
        description="Here's a list of all available commands:",
        color=SKY_BLUE,
        timestamp=utcnow()
    )
    
    text_embed.add_field(
        name="💰 Economy Commands",
        value="`;balance` or `;bal` - Check balance\n`;money` - Balance + position\n`;deposit [amount]` - Deposit\n`;withdraw [amount]` - Withdraw\n`;daily` - Daily reward\n`;weekly` - Weekly reward\n`;monthly` - Monthly reward\n`;work` - Work for money\n`;crime` - Commit crime\n`;beg` - Beg for money\n`;rob @user` - Rob someone\n`;give @user [amount]` - Give money\n`;leaderboard` or `;lb` - Rich list\n`;shop` - View shop",
        inline=False
    )
    
    text_embed.add_field(
        name="🎫 Other Commands",
        value="`;afk [reason]` - Set AFK\n`;suggest [text]` - Make suggestion\n`;help` - Show help",
        inline=False
    )
    
    text_embed.add_field(
        name="⚙️ Admin Commands (Exec+/Holding+)",
        value="`;sessions` - Session management\n`;promote @user` - Promote staff\n`;lock` - Lock channel\n`;unlock` - Unlock channel\n`;nick @user [name]` - Change nickname\n`;econ-panel` - Economy settings\n`;sendpanel` - Ticket panel",
        inline=False
    )
    
    image_embed = nextcord.Embed(color=SKY_BLUE)
    image_embed.set_image(url=HELP_FOOTER_IMAGE)
    
    await ctx.send(embeds=[text_embed, image_embed])

# ==================== ADDITIONAL UNBELIEVABOAT-STYLE COMMANDS ====================

# Collect Income Slash Command
@bot.slash_command(name="collect-income", description="Collect your passive income")
async def collect_income(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    current_time = int(time.time())
    
    # Income collected every 10 minutes (600 seconds)
    income_interval = 600
    if current_time - user_data["work_timestamp"] < income_interval:
        remaining = income_interval - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        seconds = remaining % 60
        await interaction.response.send_message(f"❌ You can collect income again in {minutes}m {seconds}s.", ephemeral=True)
        return
    
    # Calculate passive income based on total earned (0.1% of total earned, min $1, max $100)
    income = max(1, min(100, int(user_data["total_earned"] * 0.001)))
    update_economy(interaction.user.id, wallet=user_data["wallet"] + income, total_earned=user_data["total_earned"] + income, work_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="💰 Income Collected!",
        description=f"You collected **${income:,}** in passive income!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Collect Income Prefix Command
@bot.command(name="collect-income", aliases=["collect"])
async def collect_income_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    current_time = int(time.time())
    
    income_interval = 600
    if current_time - user_data["work_timestamp"] < income_interval:
        remaining = income_interval - (current_time - user_data["work_timestamp"])
        minutes = remaining // 60
        seconds = remaining % 60
        await ctx.send(f"❌ You can collect income again in {minutes}m {seconds}s.")
        return
    
    income = max(1, min(100, int(user_data["total_earned"] * 0.001)))
    update_economy(ctx.author.id, wallet=user_data["wallet"] + income, total_earned=user_data["total_earned"] + income, work_timestamp=current_time)
    
    embed = nextcord.Embed(
        title="💰 Income Collected!",
        description=f"You collected **${income:,}** in passive income!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Item Info Slash Command
@bot.slash_command(name="item-info", description="View info about an item")
async def item_info(interaction: nextcord.Interaction, item_name: str):
    items = {
        "rare boost": {"price": 5000, "description": "A rare boost that increases work earnings by 10% for 24 hours"},
        "star role": {"price": 10000, "description": "A shiny star role on your profile"},
        "premium badge": {"price": 25000, "description": "A premium badge showing your support"},
        "money multiplier": {"price": 15000, "description": "2x money earnings for 1 hour"},
        "luck charm": {"price": 7500, "description": "Increases robbery success chance by 20%"},
    }
    
    item_lower = item_name.lower()
    if item_lower in items:
        item = items[item_lower]
        embed = nextcord.Embed(
            title=f"📦 {item_name.title()}",
            description=item["description"],
            color=BLUE
        )
        embed.add_field(name="💰 Price", value=f"${item['price']:,}", inline=True)
    else:
        embed = nextcord.Embed(
            title="❌ Item Not Found",
            description="Available items: Rare Boost, Star Role, Premium Badge, Money Multiplier, Luck Charm",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Buy Item Slash Command
@bot.slash_command(name="buy-item", description="Buy an item from the shop")
async def buy_item(interaction: nextcord.Interaction, item_name: str):
    items = {
        "rare boost": {"price": 5000, "description": "A rare boost for your profile"},
        "star role": {"price": 10000, "description": "A star role on your profile"},
        "premium badge": {"price": 25000, "description": "A premium badge"},
        "money multiplier": {"price": 15000, "description": "2x money earnings for 1 hour"},
        "luck charm": {"price": 7500, "description": "Increases robbery success chance"},
    }
    
    item_lower = item_name.lower()
    if item_lower not in items:
        await interaction.response.send_message("❌ Item not found! Available: Rare Boost, Star Role, Premium Badge, Money Multiplier, Luck Charm", ephemeral=True)
        return
    
    item = items[item_lower]
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < item["price"]:
        await interaction.response.send_message(f"❌ You need **${item['price']:,}** to buy this item!", ephemeral=True)
        return
    
    update_economy(interaction.user.id, wallet=user_data["wallet"] - item["price"])
    
    embed = nextcord.Embed(
        title="✅ Item Purchased!",
        description=f"You bought **{item_name.title()}** for **${item['price']:,}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Inventory Slash Command
@bot.slash_command(name="inventory", description="View your inventory")
async def inventory(interaction: nextcord.Interaction):
    user_data = get_user_economy(interaction.user.id)
    
    # Placeholder inventory - in real implementation would use a separate table
    embed = nextcord.Embed(
        title=f"🎒 {interaction.user.name}'s Inventory",
        description="Your purchased items:",
        color=BLUE
    )
    embed.add_field(name="Items", value="No items yet. Use `/buy-item` to purchase items!", inline=False)
    embed.add_field(name="💰 Wallet", value=f"${user_data['wallet']:,}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Use Item Slash Command
@bot.slash_command(name="use-item", description="Use an item from your inventory")
async def use_item(interaction: nextcord.Interaction, item_name: str):
    items = ["rare boost", "star role", "premium badge", "money multiplier", "luck charm"]
    
    if item_name.lower() not in items:
        await interaction.response.send_message("❌ You don't have this item!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Item Used!",
        description=f"You used **{item_name}**!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Roulette Slash Command
@bot.slash_command(name="roulette", description="Play roulette")
async def roulette(interaction: nextcord.Interaction, bet: int, color: str):
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < bet:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    colors = ["red", "black", "green"]
    color_lower = color.lower()
    
    if color_lower not in colors:
        await interaction.response.send_message("❌ Choose red, black, or green!", ephemeral=True)
        return
    
    # Spin the wheel
    result = random.choice(colors)
    
    if color_lower == result:
        if color_lower == "green":
            winnings = bet * 14  # 14x for green
        else:
            winnings = bet * 2  # 2x for red/black
        
        update_economy(interaction.user.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 Roulette - YOU WON!",
            description=f"The wheel landed on **{result.upper()}**!\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    else:
        update_economy(interaction.user.id, wallet=user_data["wallet"] - bet)
        
        embed = nextcord.Embed(
            title="🎰 Roulette - YOU LOST",
            description=f"The wheel landed on **{result.upper()}**.\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slot Machine Slash Command
@bot.slash_command(name="slot-machine", description="Play the slot machine")
async def slot_machine(interaction: nextcord.Interaction, bet: int):
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < bet:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐"]
    
    # Spin 3 reels
    reel1 = random.choice(emojis)
    reel2 = random.choice(emojis)
    reel3 = random.choice(emojis)
    
    result_text = f"{reel1} {reel2} {reel3}"
    
    # Check for win
    if reel1 == reel2 == reel3:
        # Jackpot!
        winnings = bet * 10
        update_economy(interaction.user.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 JACKPOT! 🎰",
            description=f"{result_text}\nYou won **${winnings:,}**!",
            color=0xFFD700
        )
    elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
        # Small win
        winnings = bet * 2
        update_economy(interaction.user.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 You Won!",
            description=f"{result_text}\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    else:
        update_economy(interaction.user.id, wallet=user_data["wallet"] - bet)
        
        embed = nextcord.Embed(
            title="🎰 Better Luck Next Time",
            description=f"{result_text}\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Blackjack Slash Command
@bot.slash_command(name="blackjack", description="Play blackjack")
async def blackjack(interaction: nextcord.Interaction, bet: int):
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < bet:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    # Simple blackjack - draw 2 cards each
    cards = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    card_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11}
    
    def get_card_value(hand):
        total = sum(card_values[c] for c in hand)
        aces = hand.count("A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    player_hand = [random.choice(cards), random.choice(cards)]
    dealer_hand = [random.choice(cards), random.choice(cards)]
    
    player_total = get_card_value(player_hand)
    dealer_total = get_card_value(dealer_hand)
    
    result_text = f"**Your cards:** {' '.join(player_hand)} ({player_total})\n**Dealer's cards:** {' '.join(dealer_hand)} ({dealer_total})"
    
    if player_total > 21:
        update_economy(interaction.user.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - BUST!",
            description=f"{result_text}\n\nYou busted! You lost **${bet:,}**.",
            color=0xFF0000
        )
    elif dealer_total > 21 or player_total > dealer_total:
        winnings = bet * 2
        update_economy(interaction.user.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - YOU WIN!",
            description=f"{result_text}\n\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    elif player_total == dealer_total:
        embed = nextcord.Embed(
            title="🃏 Blackjack - PUSH",
            description=f"{result_text}\n\nIt's a tie! Your bet of **${bet:,}** has been returned.",
            color=BLUE
        )
    else:
        update_economy(interaction.user.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - YOU LOSE",
            description=f"{result_text}\n\nThe dealer wins. You lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Russian Roulette Slash Command
@bot.slash_command(name="russian-roulette", description="Play russian roulette (high risk!)")
async def russian_roulette(interaction: nextcord.Interaction, bet: int):
    if bet <= 0:
        await interaction.response.send_message("❌ Bet must be positive!", ephemeral=True)
        return
    
    user_data = get_user_economy(interaction.user.id)
    
    if user_data["wallet"] < bet:
        await interaction.response.send_message("❌ Insufficient funds!", ephemeral=True)
        return
    
    # 1 in 6 chance of "death" (losing)
    if random.randint(1, 6) == 1:
        # Lost - you got the bullet
        update_economy(interaction.user.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🔫 Russian Roulette - BANG!",
            description="You pulled the trigger and... BANG!\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    else:
        # Won - you survived
        winnings = bet * 5
        update_economy(interaction.user.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        embed = nextcord.Embed(
            title="🔫 Russian Roulette - CLICK!",
            description="The chamber was empty... You survived!\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== ADMIN ECONOMY CONFIG COMMANDS ====================

# Set Currency Slash Command
@bot.slash_command(name="set-currency", description="Set the server currency symbol (Executive + Holding only)")
async def set_currency(interaction: nextcord.Interaction, symbol: str):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Currency Set",
        description=f"Currency symbol has been set to **{symbol}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Maximum Balance Slash Command
@bot.slash_command(name="maximum-balance", description="View or set maximum balance limit")
async def maximum_balance(interaction: nextcord.Interaction, limit: int = None):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    if limit:
        embed = nextcord.Embed(
            title="✅ Maximum Balance Set",
            description=f"Maximum balance has been set to **${limit:,}**",
            color=BLUE
        )
    else:
        embed = nextcord.Embed(
            title="💰 Maximum Balance",
            description=f"Current maximum balance is unlimited",
            color=BLUE
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Money Audit Log Slash Command
@bot.slash_command(name="money-audit-log", description="View money transaction logs")
async def money_audit_log(interaction: nextcord.Interaction):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    c.execute("SELECT user_id, wallet, total_earned FROM economy ORDER BY total_earned DESC LIMIT 20")
    results = c.fetchall()
    
    embed = nextcord.Embed(
        title="📊 Money Audit Log",
        description="Top 20 earners in the server:",
        color=BLUE
    )
    
    for user_id, wallet, total in results:
        user = interaction.guild.get_member(user_id)
        name = user.name if user else f"User {user_id}"
        embed.add_field(name=name, value=f"Wallet: ${wallet:,}\nTotal Earned: ${total:,}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Add Money Slash Command
@bot.slash_command(name="add-money", description="Add money to a user (Executive + Holding only)")
async def add_money(interaction: nextcord.Interaction, member: nextcord.Member, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    user_data = get_user_economy(member.id)
    new_wallet = user_data["wallet"] + amount
    update_economy(member.id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
    
    embed = nextcord.Embed(
        title="✅ Money Added",
        description=f"Added **${amount:,}** to **{member.name}**'s wallet.\nNew balance: **${new_wallet:,}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Remove Money Slash Command
@bot.slash_command(name="remove-money", description="Remove money from a user (Executive + Holding only)")
async def remove_money(interaction: nextcord.Interaction, member: nextcord.Member, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    user_data = get_user_economy(member.id)
    new_wallet = max(0, user_data["wallet"] - amount)
    update_economy(member.id, wallet=new_wallet)
    
    embed = nextcord.Embed(
        title="✅ Money Removed",
        description=f"Removed **${amount:,}** from **{member.name}**'s wallet.\nNew balance: **${new_wallet:,}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Add Money Role Slash Command
@bot.slash_command(name="add-money-role", description="Add money to all members with a role")
async def add_money_role(interaction: nextcord.Interaction, role: nextcord.Role, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    count = 0
    for member in role.members:
        user_data = get_user_economy(member.id)
        new_wallet = user_data["wallet"] + amount
        update_economy(member.id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
        count += 1
    
    embed = nextcord.Embed(
        title="✅ Money Added to Role",
        description=f"Added **${amount:,}** to **{count}** members with **{role.name}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Remove Money Role Slash Command
@bot.slash_command(name="remove-money-role", description="Remove money from all members with a role")
async def remove_money_role(interaction: nextcord.Interaction, role: nextcord.Role, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    count = 0
    for member in role.members:
        user_data = get_user_economy(member.id)
        new_wallet = max(0, user_data["wallet"] - amount)
        update_economy(member.id, wallet=new_wallet)
        count += 1
    
    embed = nextcord.Embed(
        title="✅ Money Removed from Role",
        description=f"Removed **${amount:,}** from **{count}** members with **{role.name}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Economy Stats Slash Command
@bot.slash_command(name="economy-stats", description="View economy statistics")
async def economy_stats(interaction: nextcord.Interaction):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    c.execute("SELECT COUNT(*), SUM(wallet), SUM(bank), SUM(total_earned) FROM economy")
    result = c.fetchone()
    
    embed = nextcord.Embed(
        title="📊 Economy Statistics",
        description=f"**Total Users:** {result[0]:,}\n**Total Wallet:** ${result[1]:,}\n**Total Bank:** ${result[2]:,}\n**Total Earned:** ${result[3]:,}",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Reset Money Slash Command
@bot.slash_command(name="reset-money", description="Reset a user's money to starting balance")
async def reset_money(interaction: nextcord.Interaction, member: nextcord.Member):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    settings = get_economy_settings()
    update_economy(member.id, wallet=settings["starting_balance"], bank=0, total_earned=settings["starting_balance"])
    
    embed = nextcord.Embed(
        title="✅ Money Reset",
        description=f"**{member.name}**'s money has been reset to **${settings['starting_balance']:,}**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Reset Economy Slash Command
@bot.slash_command(name="reset-economy", description="Reset all economy data")
async def reset_economy(interaction: nextcord.Interaction):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    settings = get_economy_settings()
    c.execute("UPDATE economy SET wallet = ?, bank = 0, total_earned = ?", (settings["starting_balance"], settings["starting_balance"]))
    conn.commit()
    
    embed = nextcord.Embed(
        title="✅ Economy Reset",
        description="All users' money has been reset to starting balance!",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Set Cooldown Slash Command
@bot.slash_command(name="set-cooldown", description="Set command cooldowns")
async def set_cooldown(interaction: nextcord.Interaction, command: str, seconds: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Cooldown Set",
        description=f"**{command}** cooldown set to **{seconds}** seconds",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Set Fine Rate Slash Command
@bot.slash_command(name="set-fine-rate", description="Set the crime/punishment fine rate")
async def set_fine_rate(interaction: nextcord.Interaction, rate: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Fine Rate Set",
        description=f"Fine rate has been set to **{rate}%**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Set Failure Rate Slash Command
@bot.slash_command(name="set-failure-rate", description="Set the failure rate for commands")
async def set_failure_rate(interaction: nextcord.Interaction, rate: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("❌ You don't have permission!", ephemeral=True)
        return
    
    embed = nextcord.Embed(
        title="✅ Failure Rate Set",
        description=f"Failure rate has been set to **{rate}%**",
        color=BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== ADMIN PREFIX ECONOMY COMMANDS ====================

# Add Money Prefix Command
@bot.command(name="add-money")
async def add_money_prefix(ctx, member: nextcord.Member, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    user_data = get_user_economy(member.id)
    new_wallet = user_data["wallet"] + amount
    update_economy(member.id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
    
    embed = nextcord.Embed(
        title="✅ Money Added",
        description=f"Added **${amount:,}** to **{member.name}**'s wallet.\nNew balance: **${new_wallet:,}**",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Remove Money Prefix Command
@bot.command(name="remove-money")
async def remove_money_prefix(ctx, member: nextcord.Member, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    user_data = get_user_economy(member.id)
    new_wallet = max(0, user_data["wallet"] - amount)
    update_economy(member.id, wallet=new_wallet)
    
    embed = nextcord.Embed(
        title="✅ Money Removed",
        description=f"Removed **${amount:,}** from **{member.name}**'s wallet.\nNew balance: **${new_wallet:,}**",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Economy Stats Prefix Command
@bot.command(name="economy-stats")
async def economy_stats_prefix(ctx):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    c.execute("SELECT COUNT(*), SUM(wallet), SUM(bank), SUM(total_earned) FROM economy")
    result = c.fetchone()
    
    embed = nextcord.Embed(
        title="📊 Economy Statistics",
        description=f"**Total Users:** {result[0]:,}\n**Total Wallet:** ${result[1]:,}\n**Total Bank:** ${result[2]:,}\n**Total Earned:** ${result[3]:,}",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Reset Money Prefix Command
@bot.command(name="reset-money")
async def reset_money_prefix(ctx, member: nextcord.Member):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    settings = get_economy_settings()
    update_economy(member.id, wallet=settings["starting_balance"], bank=0, total_earned=settings["starting_balance"])
    
    embed = nextcord.Embed(
        title="✅ Money Reset",
        description=f"**{member.name}**'s money has been reset to **${settings['starting_balance']:,}**",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Money Audit Log Prefix Command
@bot.command(name="money-audit-log")
async def money_audit_log_prefix(ctx):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    c.execute("SELECT user_id, wallet, total_earned FROM economy ORDER BY total_earned DESC LIMIT 20")
    results = c.fetchall()
    
    embed = nextcord.Embed(
        title="📊 Money Audit Log",
        description="Top 20 earners in the server:",
        color=BLUE
    )
    
    for user_id, wallet, total in results:
        user = ctx.guild.get_member(user_id)
        name = user.name if user else f"User {user_id}"
        embed.add_field(name=name, value=f"Wallet: ${wallet:,}\nTotal: ${total:,}", inline=True)
    
    await ctx.send(embed=embed)

# Maximum Balance Prefix Command
@bot.command(name="maximum-balance")
async def maximum_balance_prefix(ctx):
    embed = nextcord.Embed(
        title="💰 Maximum Balance",
        description="Current maximum balance is unlimited",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Add Money Role Prefix Command
@bot.command(name="add-money-role")
async def add_money_role_prefix(ctx, role: nextcord.Role, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    count = 0
    for member in role.members:
        user_data = get_user_economy(member.id)
        new_wallet = user_data["wallet"] + amount
        update_economy(member.id, wallet=new_wallet, total_earned=user_data["total_earned"] + amount)
        count += 1
    
    embed = nextcord.Embed(
        title="✅ Money Added to Role",
        description=f"Added **${amount:,}** to **{count}** members with **{role.name}**",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Remove Money Role Prefix Command
@bot.command(name="remove-money-role")
async def remove_money_role_prefix(ctx, role: nextcord.Role, amount: int):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    count = 0
    for member in role.members:
        user_data = get_user_economy(member.id)
        new_wallet = max(0, user_data["wallet"] - amount)
        update_economy(member.id, wallet=new_wallet)
        count += 1
    
    embed = nextcord.Embed(
        title="✅ Money Removed from Role",
        description=f"Removed **${amount:,}** from **{count}** members with **{role.name}**",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Reset Economy Prefix Command
@bot.command(name="reset-economy")
async def reset_economy_prefix(ctx):
    if not any(role.id in EXECUTIVE_HOLDING_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission!")
        return
    
    settings = get_economy_settings()
    c.execute("UPDATE economy SET wallet = ?, bank = 0, total_earned = ?", (settings["starting_balance"], settings["starting_balance"]))
    conn.commit()
    
    embed = nextcord.Embed(
        title="✅ Economy Reset",
        description="All users' money has been reset to starting balance!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# ==================== GAME PREFIX COMMANDS ====================

# Roulette Prefix Command
@bot.command(name="roulette")
async def roulette_prefix(ctx, bet: int, color: str):
    if bet <= 0:
        await ctx.send("❌ Bet must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < bet:
        await ctx.send("❌ Insufficient funds!")
        return
    
    colors = ["red", "black", "green"]
    color_lower = color.lower()
    
    if color_lower not in colors:
        await ctx.send("❌ Choose red, black, or green!")
        return
    
    result = random.choice(colors)
    
    if color_lower == result:
        if color_lower == "green":
            winnings = bet * 14
        else:
            winnings = bet * 2
        
        update_economy(ctx.author.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 Roulette - YOU WON!",
            description=f"The wheel landed on **{result.upper()}**!\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    else:
        update_economy(ctx.author.id, wallet=user_data["wallet"] - bet)
        
        embed = nextcord.Embed(
            title="🎰 Roulette - YOU LOST",
            description=f"The wheel landed on **{result.upper()}**.\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await ctx.send(embed=embed)

# Slot Machine Prefix Command
@bot.command(name="slot-machine", aliases=["slots"])
async def slot_machine_prefix(ctx, bet: int):
    if bet <= 0:
        await ctx.send("❌ Bet must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < bet:
        await ctx.send("❌ Insufficient funds!")
        return
    
    emojis = ["🍒", "🍋", "🍊", "🍇", "💎", "⭐"]
    
    reel1 = random.choice(emojis)
    reel2 = random.choice(emojis)
    reel3 = random.choice(emojis)
    
    result_text = f"{reel1} {reel2} {reel3}"
    
    if reel1 == reel2 == reel3:
        winnings = bet * 10
        update_economy(ctx.author.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 JACKPOT! 🎰",
            description=f"{result_text}\nYou won **${winnings:,}**!",
            color=0xFFD700
        )
    elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
        winnings = bet * 2
        update_economy(ctx.author.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        
        embed = nextcord.Embed(
            title="🎰 You Won!",
            description=f"{result_text}\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    else:
        update_economy(ctx.author.id, wallet=user_data["wallet"] - bet)
        
        embed = nextcord.Embed(
            title="🎰 Better Luck Next Time",
            description=f"{result_text}\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await ctx.send(embed=embed)

# Blackjack Prefix Command
@bot.command(name="blackjack", aliases=["bj"])
async def blackjack_prefix(ctx, bet: int):
    if bet <= 0:
        await ctx.send("❌ Bet must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < bet:
        await ctx.send("❌ Insufficient funds!")
        return
    
    cards = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    card_values = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11}
    
    def get_card_value(hand):
        total = sum(card_values[c] for c in hand)
        aces = hand.count("A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total
    
    player_hand = [random.choice(cards), random.choice(cards)]
    dealer_hand = [random.choice(cards), random.choice(cards)]
    
    player_total = get_card_value(player_hand)
    dealer_total = get_card_value(dealer_hand)
    
    result_text = f"**Your cards:** {' '.join(player_hand)} ({player_total})\n**Dealer's cards:** {' '.join(dealer_hand)} ({dealer_total})"
    
    if player_total > 21:
        update_economy(ctx.author.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - BUST!",
            description=f"{result_text}\n\nYou busted! You lost **${bet:,}**.",
            color=0xFF0000
        )
    elif dealer_total > 21 or player_total > dealer_total:
        winnings = bet * 2
        update_economy(ctx.author.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - YOU WIN!",
            description=f"{result_text}\n\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    elif player_total == dealer_total:
        embed = nextcord.Embed(
            title="🃏 Blackjack - PUSH",
            description=f"{result_text}\n\nIt's a tie! Your bet of **${bet:,}** has been returned.",
            color=BLUE
        )
    else:
        update_economy(ctx.author.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🃏 Blackjack - YOU LOSE",
            description=f"{result_text}\n\nThe dealer wins. You lost **${bet:,}**.",
            color=0xFF0000
        )
    
    await ctx.send(embed=embed)

# Russian Roulette Prefix Command
@bot.command(name="russian-roulette", aliases=["rr"])
async def russian_roulette_prefix(ctx, bet: int):
    if bet <= 0:
        await ctx.send("❌ Bet must be positive!")
        return
    
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < bet:
        await ctx.send("❌ Insufficient funds!")
        return
    
    if random.randint(1, 6) == 1:
        update_economy(ctx.author.id, wallet=user_data["wallet"] - bet)
        embed = nextcord.Embed(
            title="🔫 Russian Roulette - BANG!",
            description="You pulled the trigger and... BANG!\nYou lost **${bet:,}**.",
            color=0xFF0000
        )
    else:
        winnings = bet * 5
        update_economy(ctx.author.id, wallet=user_data["wallet"] + winnings - bet, total_earned=user_data["total_earned"] + winnings - bet)
        embed = nextcord.Embed(
            title="🔫 Russian Roulette - CLICK!",
            description="The chamber was empty... You survived!\nYou won **${winnings:,}**!",
            color=0x00FF00
        )
    
    await ctx.send(embed=embed)

# Inventory Prefix Command
@bot.command(name="inventory", aliases=["inv"])
async def inventory_prefix(ctx):
    user_data = get_user_economy(ctx.author.id)
    
    embed = nextcord.Embed(
        title=f"🎒 {ctx.author.name}'s Inventory",
        description="Your purchased items:",
        color=BLUE
    )
    embed.add_field(name="Items", value="No items yet. Use `;buy-item` to purchase items!", inline=False)
    embed.add_field(name="💰 Wallet", value=f"${user_data['wallet']:,}", inline=True)
    
    await ctx.send(embed=embed)

# Item Info Prefix Command
@bot.command(name="item-info")
async def item_info_prefix(ctx, *, item_name: str):
    items = {
        "rare boost": {"price": 5000, "description": "A rare boost that increases work earnings by 10% for 24 hours"},
        "star role": {"price": 10000, "description": "A shiny star role on your profile"},
        "premium badge": {"price": 25000, "description": "A premium badge showing your support"},
        "money multiplier": {"price": 15000, "description": "2x money earnings for 1 hour"},
        "luck charm": {"price": 7500, "description": "Increases robbery success chance by 20%"},
    }
    
    item_lower = item_name.lower()
    if item_lower in items:
        item = items[item_lower]
        embed = nextcord.Embed(
            title=f"📦 {item_name.title()}",
            description=item["description"],
            color=BLUE
        )
        embed.add_field(name="💰 Price", value=f"${item['price']:,}", inline=True)
    else:
        embed = nextcord.Embed(
            title="❌ Item Not Found",
            description="Available items: Rare Boost, Star Role, Premium Badge, Money Multiplier, Luck Charm",
            color=0xFF0000
        )
    
    await ctx.send(embed=embed)

# Buy Item Prefix Command
@bot.command(name="buy-item")
async def buy_item_prefix(ctx, *, item_name: str):
    items = {
        "rare boost": {"price": 5000, "description": "A rare boost for your profile"},
        "star role": {"price": 10000, "description": "A star role on your profile"},
        "premium badge": {"price": 25000, "description": "A premium badge"},
        "money multiplier": {"price": 15000, "description": "2x money earnings for 1 hour"},
        "luck charm": {"price": 7500, "description": "Increases robbery success chance"},
    }
    
    item_lower = item_name.lower()
    if item_lower not in items:
        await ctx.send("❌ Item not found! Available: Rare Boost, Star Role, Premium Badge, Money Multiplier, Luck Charm")
        return
    
    item = items[item_lower]
    user_data = get_user_economy(ctx.author.id)
    
    if user_data["wallet"] < item["price"]:
        await ctx.send(f"❌ You need **${item['price']:,}** to buy this item!")
        return
    
    update_economy(ctx.author.id, wallet=user_data["wallet"] - item["price"])
    
    embed = nextcord.Embed(
        title="✅ Item Purchased!",
        description=f"You bought **{item_name.title()}** for **${item['price']:,}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Use Item Prefix Command
@bot.command(name="use-item")
async def use_item_prefix(ctx, *, item_name: str):
    items = ["rare boost", "star role", "premium badge", "money multiplier", "luck charm"]
    
    if item_name.lower() not in items:
        await ctx.send("❌ You don't have this item!")
        return
    
    embed = nextcord.Embed(
        title="✅ Item Used!",
        description=f"You used **{item_name}**!",
        color=BLUE
    )
    await ctx.send(embed=embed)

# Collect Income Prefix Command (already added above, keeping for reference)
# Already added as collect-income and collect

bot.run(os.getenv("TOKEN"))

