import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow
import asyncio
import chat_exporter

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

        await channel.send(welcome_message)

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
BLUE = 0x4bbfff

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

# ------------------------------
# SEND PANEL COMMAND
# ------------------------------
@bot.slash_command(name="sendpanel", description="Send the ticket panel")
async def sendpanel(interaction: nextcord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ No permission.", ephemeral=True)
        return

    await interaction.channel.send(view=TicketPanel())
    await interaction.response.send_message("✅ Ticket panel sent.", ephemeral=True)

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
