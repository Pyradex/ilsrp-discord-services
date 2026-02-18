import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio
import chat_exporter
import requests
import json

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

# ------------------------------
# Bot setup
# ------------------------------
bot = commands.Bot(command_prefix=";", intents=intents)

LOG_CHANNEL_ID = 1473167409505374220  # Logging channel
BLUE = 0x4bbfff

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
            "current": 0,
            "initiator": interaction.user.id,
            "channel_id": session_channel.id,
            "message_id": vote_message.id
        }
        
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
    
    # Get user
    user = channel.guild.get_member(payload.user_id)
    if not user:
        return
    
    # Get vote info
    vote_info = bot.session_votes[payload.message_id]
    vote_info["current"] += 1
    current_votes = vote_info["current"]
    required_votes = vote_info["required"]
    
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
# Session Auto-Refresh Function
# ------------------------------
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

# ------------------------------
# Run bot
# ------------------------------
bot.run(os.getenv("TOKEN"))

