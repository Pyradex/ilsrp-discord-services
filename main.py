import os
import nextcord
from nextcord.ext import commands
from nextcord.utils import utcnow

# ------------------------------
# Intents
# ------------------------------
intents = nextcord.Intents.default()
intents.members = True  # Required to detect member joins
intents.message_content = True  # Required for prefix commands

# ------------------------------
# Bot setup
# ------------------------------
bot = commands.Bot(command_prefix=";", intents=intents)

# ------------------------------
# Member join event
# ------------------------------
@bot.event
async def on_member_join(member):
    # Replace with your welcome channel ID
    channel = bot.get_channel(1471660664022896902)

    if channel:
        # ---- EMBED 1: Banner ----
        banner_embed = nextcord.Embed(color=0x4bbfff)
        banner_embed.set_image(
            url="https://cdn.discordapp.com/attachments/1472412365415776306/1473135761078358270/welcomeilsrp.png"
        )

        # ---- EMBED 2: Welcome Message ----
        welcome_embed = nextcord.Embed(
            title="Welcome to the Server!",
            description=(
                f"Hey {member.mention} 👋\n\n"
                "We're glad to have you here.\n"
                "Make sure to read the rules and grab your roles!"
            ),
            color=0x4bbfff
        )

        welcome_embed.set_thumbnail(url=member.avatar.url)
        welcome_embed.set_footer(text=f"Member #{member.guild.member_count}")
        welcome_embed.timestamp = utcnow()  # adds timestamp

        # Send greeting text + embeds
        await channel.send(
            content=f"Greetings {member.mention} 🎉",
            embeds=[banner_embed, welcome_embed]
        )

# ------------------------------
# ;say command for two roles
# ------------------------------
ALLOWED_ROLE_IDS = [1471642126663024640, 1471642360503992411]  # executive & holding

@bot.command()
async def say(ctx, *, message: str):
    """Repeats message and deletes original; only for specific roles."""
    
    if any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        try:
            await ctx.message.delete()
        except nextcord.Forbidden:
            pass
        await ctx.send(message)
    else:
        await ctx.send(f"❌ {ctx.author.mention}, you don't have permission to use this command.")

# ------------------------------
# ;requesttraining command
# ------------------------------
@bot.command()
async def requesttraining(ctx):
    # Only allow usage in the specific channel
    if ctx.channel.id != 1473150653374271491:
        await ctx.send(f"❌ {ctx.author.mention}, you can't use this command here.")
        return

    # Only allow users with the specific role
    allowed_role_id = 1472037174630285538
    if allowed_role_id not in [role.id for role in ctx.author.roles]:
        await ctx.send(f"❌ {ctx.author.mention}, you do not have permission to use this command.")
        return

    # Target channel to send the message
    target_channel = bot.get_channel(1473150653374271491)
    if not target_channel:
        await ctx.send("❌ Could not find the target channel.")
        return

    # Embed message
    embed = nextcord.Embed(
        title="Greetings, Staff Trainers",
        description=(
            f"{ctx.author.mention} is requesting that a training session will be hosted at this time.\n\n"
            "You are requested to organize one and provide further instructions in <#1472056023358640282>."
        ),
        color=0x4bbfff
    )

    # Send role ping outside of embed
    await target_channel.send(
        content="<@&1473151069264678932>",
        embed=embed
    )

    # Delete command message and optionally confirm
    try:
        await ctx.message.delete()
    except nextcord.Forbidden:
        pass
    await ctx.send(f"✅ {ctx.author.mention}, your training request has been sent!", delete_after=5)

# ------------------------------
# Run bot using Render environment variable
# ------------------------------
bot.run(os.getenv("TOKEN"))
