import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio
import chat_exporter

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
        
        await interaction.followup.send(
            f"✅ **{self.target_member}** has been promoted to **{new_position}**!\n\n"
            f"**COPY TEXT:**\n```\n{copy_text}\n```",
            ephemeral=False
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

    await interaction.channel.send(
        embed=embed,
        view=TicketPanel()
    )

    await interaction.response.send_message(
        "✅ Ticket panel sent.",
        ephemeral=True
    )


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

