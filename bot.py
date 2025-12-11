import discord
from discord.ext import commands, tasks
import json
import os
import pytz
import re
import random
from datetime import datetime, timedelta, timezone, time
import asyncio
from pathlib import Path

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.help_command = None

#config
ROLE_NAME = "CLAN_ROLE_NAME"
MOD_ROLE_NAME = "CLAN_MOD_ROLE"
BOT_ROLES = ["BOT_ROLE_1", "BOT_ROLE_2"]
CATEGORY_NAME = "PRIVATE_CATEGORY_NAME"
STORAGE_FILE = "channel_owners.json"
ACTIVE_ROLE_NAME = "ACTIVE_ROLE_NAME"
INACTIVE_ROLE_NAME = "INACTIVE_ROLE_NAME"
EXCUSED_ROLE_NAME = "EXCUSED_ROLE_NAME"
IGNORED_USER_IDS = [
    000000000000000000,
    000000000000000000
]
TREASURY_ID = 000000000000000000
LEAVE_CHANNEL_ID = 000000000000000000
TRACKER_CHANNEL_NAME = "TRACKER_CHANNEL_NAME"
TRACKER_CATEGORY_NAME = "CLAN_CATEGORY_NAME"
GOAL_TEXT = "has reached the Clan goal Weekly Catch Req of 300!"
TIMEZONE = pytz.timezone('US/Eastern')
RESET_TIME = 0
active_breaks = {}
DATA_FILE = Path("users.json")

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            for uid, info in data.items():
                if "break_end" in info:
                    info["break_end"] = datetime.fromisoformat(info["break_end"])
            return data
    return {}

def save_data(data):
    # Convert datetime to string
    to_save = {}
    for uid, info in data.items():
        new_info = info.copy()
        if "break_end" in new_info:
            new_info["break_end"] = new_info["break_end"].isoformat()
        to_save[uid] = new_info
    with open(DATA_FILE, "w") as f:
        json.dump(to_save, f, indent=4)

# Load channel ownership from file
def load_channel_owners():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception as e:
            print(f"Error loading ownership data: {e}")
    return {}

# Save channel ownership to file
def save_channel_owners():
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(channel_owners, f, indent=4)
    except Exception as e:
        print(f"Error saving ownership data: {e}")

# Initialize ownership tracking
channel_owners = load_channel_owners()

# --- Channel Creation ---
@bot.event
async def on_member_update(before, after):
    if len(before.roles) < len(after.roles):
        new_role = next((role for role in after.roles if role not in before.roles), None)
        if new_role and new_role.name == ROLE_NAME:
            await create_member_channel(after)

async def create_member_channel(member):
    guild = member.guild
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        category = await guild.create_category(CATEGORY_NAME)
    
    default_emojis = ["🌹"]
    emoji_choice = random.choice(default_emojis)
    channel_name = f"{emoji_choice}│{member.display_name}"
    channel_topic = f"{member.name}'s personal channel"
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    
    mod_role = discord.utils.get(guild.roles, name=MOD_ROLE_NAME)
    if mod_role:
        overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True)
        print(f"✅ Added {mod_role.name} to channel permissions")
    
    for role_name in BOT_ROLES:
        bot_role = discord.utils.get(guild.roles, name=role_name)
        if bot_role:
            overwrites[bot_role] = discord.PermissionOverwrite(read_messages=True)


    try:
        channel = await category.create_text_channel(
            name=channel_name,
            topic=channel_topic,
            overwrites=overwrites,
            reason=f"Auto-created for {member.name}"
        )
        
        channel_owners[channel.id] = member.id
        save_channel_owners()
        
        await channel.send(
            f"Welcome {member.mention}!\n"
            f"• Use `!rename emoji name` to personalize this channel (example: `!rename 🎮 Gaming Den`)\n"
            f"• Use `!public`/`!private` to control visibility (default set to private)\n"
            f"• Use `!guide` to show this message again\n"
            f"• Use `!welcome` to show the welcome message again"
        )
        
        clan_embed = discord.Embed(
            description=(
                "> Our clan is *insert* rank so you can purchase bronze and silver perks (with your own money) if you have enough clan catches.\n"
                "> Type `;clan info perks` for more information on clan perks.\n\n"
                "**Here's a rundown of channels and guides you should check out to get the most out of your clan experience.**\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n\n"
                "**Helpful channels if you are in need of assistance:**\n"
                "<#000000000000000000>\n"
                "<#000000000000000000> - check pins\n\n"
                "Check out any games, lottos, or giveaways we have going on!!\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n\n"
                "Finally, make sure to get some <#000000000000000000> <#000000000000000000> and tell us more about yourself in <#000000000000000000>. We'd love to hear more about you!!"
            ),
            color=discord.Color.green()
        )
        await channel.send(embed=clan_embed)
    except Exception as e:
        print(f"Error creating channel: {e}")
        
@bot.command(name='guide')
async def show_guide(ctx):
    if ctx.channel.category and ctx.channel.category.name == CATEGORY_NAME:
        await ctx.send(
            f"• Use `!rename emoji name` to personalize this channel, example: `!rename 🎮 Gaming Den` (be mindful to not use improper speech)\n"
            f"• Use `!public`/`!private` to control visibility (default set to private)\n"
            f"• Use `!guide` to show this message again\n"
            f"• Use `!welcome` to show the welcome message again"
        )



@bot.command(name='welcome')
async def show_welcome(ctx):
    if ctx.channel.category and ctx.channel.category.name == CATEGORY_NAME:
        clan_embed = discord.Embed(
            description=(
                "> Our clan is *INSERT* rank so you can purchase bronze and silver perks (with your own money) if you have enough clan catches.\n"
                "> Type `;clan info perks` for more information on clan perks.\n\n"
                "**Here's a rundown of channels and guides you should check out to get the most out of your clan experience.**\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n\n"
                "**Helpful channels if you are in need of assistance:**\n"
                "<#000000000000000000>\n"
                "<#000000000000000000> - check pins\n\n"
                "Check out any games, lottos, or giveaways we have going on!!\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n"
                "<#000000000000000000>\n\n"
                "Finally, make sure to get some <#000000000000000000> <#000000000000000000> and tell us more about yourself in <#000000000000000000>. We'd love to hear more about you!!"
            ),
            color=discord.Color.green()
        )
        await ctx.send(embed=clan_embed)

# Handle channel deletions
@bot.event
async def on_guild_channel_delete(channel):
    if channel.id in channel_owners:
        del channel_owners[channel.id]
        save_channel_owners()

# Cleanup on startup
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    valid_channels = set()
    for guild in bot.guilds:
        valid_channels.update(ch.id for ch in guild.channels)
    
    global channel_owners
    original_keys = list(channel_owners.keys())
    changed = False
    
    for channel_id in original_keys:
        if channel_id not in valid_channels:
            del channel_owners[channel_id]
            changed = True
    
    if changed:
        save_channel_owners()
    
    # Start the weekly reset task
    if not weekly_reset.is_running():
        weekly_reset.start()
    check_breaks.start()
    thursday_fee_reminder.start()

# --- Channel Management Commands ---
@bot.command(name='rename')
async def rename_channel(ctx, emoji_part: str, *, text_part: str):
    if channel_owners.get(ctx.channel.id) != ctx.author.id:
        return await ctx.send("❌ This isn't your channel!")
    
    new_name = f"{emoji_part}│{text_part}"
    
    if len(new_name) > 32:
        return await ctx.send(f"❌ Name too long ({len(new_name)}/32 characters)")
    
    try:
        await ctx.channel.edit(name=new_name)
        await ctx.send(f"✅ Renamed to: {new_name}")
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to rename: {str(e)}")

@bot.command(name='public')
async def make_public(ctx):
    if channel_owners.get(ctx.channel.id) != ctx.author.id:
        return await ctx.send("❌ This isn't your channel!")
    
    clan_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
    mod_role = discord.utils.get(ctx.guild.roles, name=MOD_ROLE_NAME)
    
    if not clan_role:
        return await ctx.send(f"❌ {ROLE_NAME} role not found!")
    
    try:
        await ctx.channel.set_permissions(clan_role, read_messages=True)
        
        if mod_role:
            await ctx.channel.set_permissions(mod_role, read_messages=True)
        
        await ctx.send(f"🔓 Visible to all {ROLE_NAME}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify channel permissions!")



@bot.command(name='private')
async def make_private(ctx):
    if channel_owners.get(ctx.channel.id) != ctx.author.id:
        return await ctx.send("❌ This isn't your channel!")
    
    clan_role = discord.utils.get(ctx.guild.roles, name=ROLE_NAME)
    mod_role = discord.utils.get(ctx.guild.roles, name=MOD_ROLE_NAME)
    
    if not clan_role:
        return await ctx.send(f"❌ {ROLE_NAME} role not found!")
    
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await ctx.channel.set_permissions(clan_role, read_messages=False)
        
        if mod_role:
            await ctx.channel.set_permissions(mod_role, read_messages=True)
        
        await ctx.channel.set_permissions(ctx.author, read_messages=True)
        
        await ctx.send(f"🔒 Now private (only you can see)")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to modify channel permissions!")

# --- Clan Goal Tracking ---
def get_role(guild, role_name):
    """Get role with case-insensitive matching"""
    # First try exact match
    role = discord.utils.get(guild.roles, name=role_name)
    if role:
        return role
    
    # Try case-insensitive match
    for r in guild.roles:
        if r.name.lower() == role_name.lower():
            return r
    
    return None

async def find_tracker_channel(guild):
    """Find the tracker channel with flexible matching"""
    # First try exact match in the category
    category = discord.utils.get(guild.categories, name=TRACKER_CATEGORY_NAME)
    if category:
        channel = discord.utils.get(category.channels, name=TRACKER_CHANNEL_NAME)
        if channel:
            return channel
    
    # Try case-insensitive search
    for category in guild.categories:
        # Flexible category matching
        if TRACKER_CATEGORY_NAME.lower() in category.name.lower():
            for channel in category.channels:
                # Flexible channel matching
                if TRACKER_CHANNEL_NAME.lower() in channel.name.lower():
                    return channel
    
    # Search all channels if still not found
    for channel in guild.text_channels:
        if TRACKER_CHANNEL_NAME.lower() in channel.name.lower():
            return channel
    
    return None

async def verify_permissions(guild):
    """Verify the bot has required permissions"""
    # Check manage roles permission
    if not guild.me.guild_permissions.manage_roles:
        print(f"❌ Bot lacks 'Manage Roles' permission in {guild.name}")
        return False
    
    # Check if bot's top role is high enough
    active_role = get_role(guild, ACTIVE_ROLE_NAME)
    inactive_role = get_role(guild, INACTIVE_ROLE_NAME)
    
    if active_role and guild.me.top_role.position <= active_role.position:
        print(f"❌ Bot's role is not higher than '{ACTIVE_ROLE_NAME}' role")
        return False
        
    if inactive_role and guild.me.top_role.position <= inactive_role.position:
        print(f"❌ Bot's role is not higher than '{INACTIVE_ROLE_NAME}' role")
        return False
        
    return True

async def process_weekly_goal():
    print("Starting weekly clan goal processing...")
    for guild in bot.guilds:
        try:
            # Check permissions first
            if not await verify_permissions(guild):
                print(f"Skipping {guild.name} due to permission issues")
                continue
                
            # Get required roles
            clan_role = get_role(guild, ROLE_NAME)
            if not clan_role:
                print(f"❌ Clan role '{ROLE_NAME}' not found in {guild.name}")
                continue
                
            active_role = get_role(guild, ACTIVE_ROLE_NAME) or await guild.create_role(name=ACTIVE_ROLE_NAME)
            inactive_role = get_role(guild, INACTIVE_ROLE_NAME) or await guild.create_role(name=INACTIVE_ROLE_NAME)
            excused_role = get_role(guild, EXCUSED_ROLE_NAME)
            
            # Find tracker channel
            tracker_channel = await find_tracker_channel(guild)
            if not tracker_channel:
                print(f"❌ Could not find tracker channel in {guild.name}")
                continue
                
            print(f"✅ Found tracker channel: #{tracker_channel.name} in {tracker_channel.category}")
                
            # Calculate time range (current week)
            now = datetime.now(TIMEZONE)
            # Get the most recent Sunday at 00:00
            reset_time = now - timedelta(days=now.weekday() + 1)
            reset_time = reset_time.replace(hour=RESET_TIME, minute=0, second=0, microsecond=0)
            # If today is Sunday but before reset time, go back one week
            if now.weekday() == 6 and now.hour < RESET_TIME:
                reset_time = reset_time - timedelta(weeks=1)
                
            # Start time is the reset time (Sunday 00:00)
            start_time = reset_time
            # End time is now (current time on Sunday)
            end_time = now
            
            print(f"⏰ Processing messages from {start_time} to {end_time}")
            
            # Collect active members
            active_members = set()
            async for message in tracker_channel.history(limit=None, after=start_time, before=end_time):
                # Match TRACKER_HELPER_BOT messages with the goal text
                if message.author.name == "TRACKER_HELPER_BOT" and GOAL_TEXT in message.content:
                    # Extract username - first word in the message
                    username = message.content.split()[0]
                    active_members.add(username.lower())
            
            print(f"📊 Found {len(active_members)} active catchers}")
            
            # Process clan members
            clan_members = [member for member in clan_role.members if member.id not in IGNORED_USER_IDS]
            print(f"👥 Processing {len(clan_members)} clan members")
            
            excused_count = 0
            active_count = 0
            inactive_count = 0
            
            for member in clan_members:
                try:
                    if member.id in IGNORED_USER_IDS:
                        ignored_count += 1
                        continue
                    # Skip processing if member has EXCUSED_ROLE_NAME role
                    if excused_role and excused_role in member.roles:
                        excused_count += 1
                        # Remove inactive role if present
                        if inactive_role in member.roles:
                            await member.remove_roles(inactive_role)
                        continue
                    
                    # Normalize for comparison
                    username_match = member.name.lower() in active_members
                    display_match = member.display_name.lower() in active_members
                    
                    if username_match or display_match:
                        # Add active role
                        if active_role not in member.roles:
                            await member.add_roles(active_role)
                        # Remove inactive role
                        if inactive_role in member.roles:
                            await member.remove_roles(inactive_role)
                        active_count += 1
                    else:
                        # Add inactive role
                        if inactive_role not in member.roles:
                            await member.add_roles(inactive_role)
                        # Remove active role
                        if active_role in member.roles:
                            await member.remove_roles(active_role)
                        inactive_count += 1
                except Exception as e:
                    print(f"❌ Error updating roles for {member.display_name}: {e}")
            
            print(f"✅ Weekly clan goal processing completed! "
                  f"Active: {active_count}, Inactive: {inactive_count}, EXCUSED_ROLE_NAME: {excused_count}")
            
            # Send notification to the tracker channel
            await tracker_channel.send(
                f"🏆 Weekly clan goal processing complete!\n"
                f"• ACTIVE_ROLE_NAMEs: {active_count}\n"
                f"• INACTIVE_ROLE_NAMEs: {inactive_count}\n"
                f"• EXCUSED_ROLE_NAME Members: {excused_count}\n"
                f"• Total Clan Members: {len(clan_members)}"
            )
            
            # Find WEEKLY_CATCHES_CHANNEL_NAME channel and send notification
            weekly_catches_channel = discord.utils.get(guild.text_channels, name="WEEKLY_CATCHES_CHANNEL_NAME")
            if not weekly_catches_channel:
                # Try case-insensitive search
                for channel in guild.text_channels:
                    if "WEEKLY_CATCHES_CHANNEL_NAME" in channel.name.lower():
                        weekly_catches_channel = channel
                        break
            
            if weekly_catches_channel:
                # Get current week for the message
                week_start = start_time.strftime("%B %d")
                
                # Format the message
                message = (
                    f"<@&{inactive_role.id}>\n\n"
                    f"**Week of {week_start}**\n\n"
                    "Those with the role please do one of the following:\n\n"
                    f"• ;give <@{TREASURY_ID}> 100K\n\n"
                    "Or @ CLAN_STAFF_USER in your personal channel if you need to be excused"
                )
                await weekly_catches_channel.send(message)
            else:
                print(f"⚠️ Could not find WEEKLY_CATCHES_CHANNEL_NAME channel in {guild.name}")
            
        except Exception as e:
            print(f"❌ Error processing weekly goal for {guild.name}: {e}")

reset_clock = time(hour=0, tzinfo=TIMEZONE)
now = datetime.now(TIMEZONE)
@tasks.loop(time=reset_clock)
async def weekly_reset():
    now = datetime.now(TIMEZONE)
    if now.weekday() == 6:  # Sunday
        await process_weekly_goal()

# Manual reset command for testing
@bot.command(name='forcereset')
@commands.has_role(MOD_ROLE_NAME)
async def force_reset(ctx):
    await process_weekly_goal()
    await ctx.send("✅ Manual clan goal processing completed!")

@bot.command(name='activecatchers')
async def show_active_catchers(ctx):
    """Show current members with ACTIVE_ROLE_NAME role"""
    try:
        # Get the active role
        active_role = discord.utils.get(ctx.guild.roles, name=ACTIVE_ROLE_NAME)
        if not active_role:
            return await ctx.send(f"❌ '{ACTIVE_ROLE_NAME}' role not found")
        
        # Get members with the role
        active_members = [member for member in active_role.members]
        
        if not active_members:
            return await ctx.send("No active catchers found this week")
        
        # Sort alphabetically by display name
        active_members.sort(key=lambda m: m.display_name.lower())
        
        # Create paginated list
        members_per_page = 20
        pages = []
        current_page = []
        
        for i, member in enumerate(active_members, 1):
            current_page.append(f"{i}. {member.display_name}")
            if i % members_per_page == 0:
                pages.append("\n".join(current_page))
                current_page = []
        
        if current_page:
            pages.append("\n".join(current_page))
        
        # Create and send embeds
        for page_num, page_content in enumerate(pages, 1):
            embed = discord.Embed(
                title=f"ACTIVE_ROLE_NAMEs (Page {page_num}/{len(pages)})",
                description=page_content,
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Total ACTIVE_ROLE_NAMEs: {len(active_members)}")
            await ctx.send(embed=embed)
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

class HelpView(discord.ui.View):
    def __init__(self, ctx, is_mod=False):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.is_mod = is_mod
        self.current_page = "main"
        
        # Set emojis directly using the guild's emojis
        guild = ctx.guild
        
        # Try to find custom emojis, fallback to defaults
        general_emoji = discord.utils.get(guild.emojis, name="EMOJI_GENERAL") or "ℹ️"
        channel_emoji = discord.utils.get(guild.emojis, name="EMOJI_CHANNEL") or "💬"
        pto_emoji = discord.utils.get(guild.emojis, name="EMOJI_PTO") or "🏖️"
        mod_emoji = discord.utils.get(guild.emojis, name="EMOJI_MOD") or "🛡️"
        back_emoji = discord.utils.get(guild.emojis, name="EMOJI_BACK") or "⬅️"

        # Update button emojis
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.label == "General":
                    child.emoji = general_emoji
                elif child.label == "Channel":
                    child.emoji = channel_emoji
                elif child.label == "PTO/Breaks":
                    child.emoji = pto_emoji
                elif child.label == "Mod Only":
                    child.emoji = mod_emoji
                    child.disabled = not is_mod
                elif child.label == "Back":
                    child.emoji = back_emoji

    
    async def on_timeout(self):
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass
    
    @discord.ui.button(label="General", style=discord.ButtonStyle.primary)
    async def general_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="General Commands",
            description="Basic commands available to everyone:",
            color=discord.Color.blue()
        )
        
        commands_list = [
            ("!shelp", "Show this interactive help menu"),
            ("!guide", "Show channel management guide"),
            ("!welcome", "Show clan welcome message"),
            ("!activecatchers", "List current active catchers"),
            ("!mystatus", "Show your break status and PTO balance"),
            ("!pto [reason]", "Request PTO (if you reached catch requirement)"),
            ("!break Xd [reason]", "Request a break using PTO"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="Use the buttons below to navigate between categories")
        self.current_page = "general"
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Channel", style=discord.ButtonStyle.secondary)
    async def channel_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Channel Management Commands",
            description="Commands for managing your personal channel:",
            color=discord.Color.green()
        )
        
        commands_list = [
            ("!rename [emoji] [name]", "Personalize your channel (e.g., `!rename 🎮 Gaming Den`)"),
            ("!public", "Make your channel visible to all clan members"),
            ("!private", "Make your channel private (only you and mods)"),
            ("!guide", "Show channel management guide again"),
            ("!welcome", "Show welcome message again"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="Note: These commands only work in your personal channel")
        self.current_page = "channel"
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="PTO/Breaks", style=discord.ButtonStyle.success)
    async def pto_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="PTO & Break System",
            description="Manage your time off and breaks:",
            color=discord.Color.orange()
        )
        
        commands_list = [
            ("!pto [reason]", "Request Paid Time Off (requires meeting catch goals)"),
            ("!break Xd [reason]", "Take a break (uses PTO, must be multiples of 7 days)"),
            ("!mystatus", "Check your current break status and PTO balance"),
            ("PTO Rules", "Earn 1 PTO per week you meet catch requirements"),
            ("Break Rules", "1 PTO = 1 week of break time"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="All requests require moderator approval")
        self.current_page = "pto"
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Mod Only", style=discord.ButtonStyle.danger)
    async def mod_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_mod:
            await interaction.response.send_message("❌ This section is for moderators only!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Moderator Commands",
            description="Commands available only to CLAN_MOD_ROLEs:",
            color=discord.Color.red()
        )
        
        commands_list = [
            ("!forcereset", "Manually process weekly clan goals"),
            ("!ptos", "Show all members' PTO balances"),
            ("!breaks", "Show all active breaks"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        self.current_page = "mod"
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.gray)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Return to main help menu
        await self.show_main_menu(interaction)
    
    async def show_main_menu(self, interaction=None):
        embed = discord.Embed(
            title="CLAN_BOT_HELP_TITLE",
            description="Welcome to the interactive help system! Select a category below to learn more about available commands.",
            color=discord.Color.blue()
        )
        
        # Get current emojis from buttons for display
        general_emoji = "ℹ️"
        channel_emoji = "💬"
        pto_emoji = "🏖️"
        mod_emoji = "🛡️"
        
        for child in self.children:
            if child.label == "General" and child.emoji:
                general_emoji = child.emoji
            elif child.label == "Channel" and child.emoji:
                channel_emoji = child.emoji
            elif child.label == "PTO/Breaks" and child.emoji:
                pto_emoji = child.emoji
            elif child.label == "Mod Only" and child.emoji:
                mod_emoji = child.emoji
        
        categories = [
            (f"{general_emoji} General", "Basic commands for everyone", False),
            (f"{channel_emoji} Channel", "Manage your personal channel", False),
            (f"{pto_emoji} PTO/Breaks", "Time off and break system", False),
            (f"{mod_emoji} Mod Only", "Moderator commands", not self.is_mod),
        ]
        
        for category_name, desc, disabled in categories:
            status = "🔒 (Mod Only)" if disabled else "✅"
            embed.add_field(
                name=f"{category_name} {status}",
                value=desc,
                inline=False
            )
        
        embed.set_footer(text="This menu will timeout after 60 seconds of inactivity")
        self.current_page = "main"
        
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            return embed

@bot.command(name='shelp')
async def custom_help(ctx):
    """Show interactive help menu with buttons"""
    # Check if user is mod
    mod_role = discord.utils.get(ctx.guild.roles, name=MOD_ROLE_NAME)
    is_mod = mod_role and mod_role in ctx.author.roles
    
    view = HelpView(ctx, is_mod=is_mod)
    embed = await view.show_main_menu()
    
    view.message = await ctx.send(embed=embed, view=view)

def load_pto():
    if PTO_FILE.exists():
        with open(PTO_FILE, "r") as f:
            return json.load(f)
    return {}

def save_pto(data):
    with open(PTO_FILE, "w") as f:
        json.dump(data, f, indent=4)

def deduct_pto(user_id: int):
    pto_data = load_pto()
    uid = str(user_id)
    if uid not in pto_data:
        pto_data[uid] = 0
    if pto_data[uid] > 0:
        pto_data[uid] -= 1
    save_pto(pto_data)


def load_breaks():
    if BREAKS_FILE.exists():
        with open(BREAKS_FILE, "r") as f:
            data = json.load(f)
            # Convert end_time strings back to datetime
            for uid, info in data.items():
                info["end_time"] = datetime.fromisoformat(info["end_time"])
            return data
    return {}

def save_breaks(data):
    # Convert datetime to ISO string
    to_save = {uid: {**info, "end_time": info["end_time"].isoformat()} for uid, info in data.items()}
    with open(BREAKS_FILE, "w") as f:
        json.dump(to_save, f, indent=4)

class ApprovalView(discord.ui.View):
    def __init__(self, requester: discord.Member, duration: timedelta, reason: str, is_break=True):
        super().__init__(timeout=None)
        self.requester = requester
        self.duration = duration
        self.reason = reason
        self.is_break = is_break

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=EXCUSED_ROLE_NAME)
        data = load_data()
        uid = str(self.requester.id)
        now = datetime.now(timezone.utc)

        if self.is_break:
            if role:
                await self.requester.add_roles(role)

            if uid in data and "break_end" in data[uid] and data[uid]["break_end"] > now:
                base_time = data[uid]["break_end"]
                new_end = base_time + self.duration
                data[uid]["break_end"] = new_end
                data[uid]["break_reason"] += f" + {self.reason}"
            else:
                data.setdefault(uid, {})["break_end"] = now + self.duration
                data[uid]["break_reason"] = self.reason

            # PTO deduction based on weeks
            if uid not in data:
                data[uid] = {}
            if "pto" not in data[uid]:
                data[uid]["pto"] = 0

            weeks = self.duration.days // 7
            if weeks > 0:
                data[uid]["pto"] = max(0, data[uid]["pto"] - weeks)
        # Handle PTO requests
        else:
            if uid not in data:
                data[uid] = {}
            if "pto" not in data[uid]:
                data[uid]["pto"] = 0
            data[uid]["pto"] += 1
            data[uid]["last_pto_reason"] = self.reason

        data[uid]["last_approved_by"] = interaction.user.id
        save_data(data)

        # Update embed
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        status_text = "Approved"
        if self.is_break:
            status_text += f"\nEnds: {format_remaining(data[uid]['break_end'])}"
        embed.add_field(name="Status", value=f"✅ {status_text} by {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

        # Send to personal channel
        personal_channel_id = None
        for ch_id, owner_id in channel_owners.items():
            if owner_id == self.requester.id:
                personal_channel_id = int(ch_id)
                break

        personal_channel_id = None
        for ch_id, owner_id in channel_owners.items():
            if owner_id == self.requester.id:
                personal_channel_id = int(ch_id)
                break

        if personal_channel_id:
            personal_channel = bot.get_channel(personal_channel_id)  # <-- use bot, not interaction.guild
            if personal_channel:
                await personal_channel.send(
                    f"{self.requester.mention}\n✅ Your request has been approved!\n"
                    + (f"Duration: {format_remaining(data[uid]['break_end'])}" if self.is_break else "")
                )


    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="Status", value=f"❌ Rejected by {interaction.user.mention}", inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

        # Find personal channel
        personal_channel_id = None
        for ch_id, owner_id in channel_owners.items():
            if owner_id == self.requester.id:
                personal_channel_id = int(ch_id)
                break

        if personal_channel_id:
            personal_channel = bot.get_channel(personal_channel_id)
            if personal_channel:
                await personal_channel.send(
                    f"{self.requester.mention}\n❌ Your request has been rejected!\n"
                )



@bot.command(name="break")
async def leave_request(ctx, duration: str = None, *, reason: str = None):
    if not duration or not reason:
        await ctx.send("❌ Usage: `!break <duration> <reason>`\nExample: `!break 7d Vacation`")
        return

    # Only allow multiples of 7 days
    if duration[-1].lower() != "d":
        await ctx.send("⚠️ Only durations in days are allowed (e.g., 7d, 14d).")
        return
    days = int(duration[:-1])
    if days % 7 != 0:
        await ctx.send("⚠️ Break duration must be a multiple of 7 days (7, 14, etc).")
        return

    duration_td = timedelta(days=days)
    leave_channel = bot.get_channel(LEAVE_CHANNEL_ID)

    embed = discord.Embed(
        title="📅 Leave/Break Request",
        description=f"**User:** {ctx.author.mention}\n**Reason:** {reason}\n**Duration:** {days} days",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"User ID: {ctx.author.id}")

    await leave_channel.send(embed=embed, view=ApprovalView(ctx.author, duration_td, reason, is_break=True))
    await ctx.send("✅ Your break request has been submitted.")

def format_remaining(end_time: datetime) -> str:
    remaining = end_time - datetime.now(timezone.utc)
    if remaining.total_seconds() <= 0:
        return "Expired"
    days = remaining.days
    hours, remainder = divmod(remaining.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"

@bot.command(name="mystatus")
async def my_status(ctx):
    data = load_data()
    uid = str(ctx.author.id)
    if uid not in data:
        await ctx.send("❌ You have no active breaks or PTO.")
        return

    msg = ""
    if "break_end" in data[uid]:
        msg += f"📅 Break reason: {data[uid].get('break_reason','')}\n"
        msg += f"⏳ Time left: {format_remaining(data[uid]['break_end'])}\n"
    msg += f"📝 PTO remaining: {data[uid].get('pto',0)}"

    await ctx.send(msg)


@bot.command(name="breaks")
@commands.has_role("CLAN_MOD_ROLE")
async def all_breaks(ctx):
    data = load_data()
    msg = "📋 **Current Breaks:**\n"
    now = datetime.now(timezone.utc)
    for uid, info in data.items():
        if "break_end" in info and info["break_end"] > now:
            member = ctx.guild.get_member(int(uid))
            approver = ctx.guild.get_member(info.get("last_approved_by",0))
            msg += f"- {member.mention if member else uid}: {info.get('break_reason','')} | ⏳ {format_remaining(info['break_end'])} | Approved by {approver.mention if approver else 'Unknown'}\n"
    await ctx.send(msg or "✅ No active breaks.")


@bot.command(name="pto")
async def pto_request(ctx, *, reason: str = None):
    if not reason:
        await ctx.send("❌ Usage: `!pto <reason>`")
        return

    leave_channel = bot.get_channel(LEAVE_CHANNEL_ID)
    embed = discord.Embed(
        title="📝 PTO Request",
        description=f"**User:** {ctx.author.mention}\n**Reason:** {reason}",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"User ID: {ctx.author.id}")

    await leave_channel.send(embed=embed, view=ApprovalView(ctx.author, timedelta(0), reason, is_break=False))
    await ctx.send("✅ Your PTO request has been submitted.")


@tasks.loop(minutes=60)
async def check_breaks():
    data = load_data()
    now = datetime.now(timezone.utc)

    for uid, user_data in list(data.items()):
        if "break_end" in user_data:
            end_time = user_data["break_end"]
            if now >= end_time:
                # Break is over
                guild = bot.get_guild(000000000000000000)  # replace with your guild/server ID
                member = guild.get_member(int(uid))
                if member:
                    role = discord.utils.get(guild.roles, name=EXCUSED_ROLE_NAME)
                    if role in member.roles:
                        await member.remove_roles(role, reason="Break ended automatically")

                # Clean up user_data
                del user_data["break_end"]
                del user_data["break_reason"]
                save_data(data)


@bot.command(name="ptos")
@commands.has_role("CLAN_MOD_ROLE")
async def all_ptos(ctx):
    data = load_data()
    msg = "📋 **PTO Counts:**\n"
    for uid, info in data.items():
        member = ctx.guild.get_member(int(uid))
        msg += f"- {member.mention if member else uid}: {info.get('pto',0)} PTOs\n"
    await ctx.send(msg)

# Donation monitoring system - Trusted bots only
TRUSTED_BOT_ROLES = ["BOT_ROLE_2", "BOT_ROLE_3"]

@bot.event
async def on_message(message):
    # Process commands first
    await bot.process_commands(message)
    
    # Check for donation messages from trusted bots only
    await check_donation_message(message)

async def check_donation_message(message):
    """Check if message from trusted bot contains a successful donation to TREASURY_USER"""
    
    # Only process messages from trusted bots
    if not await is_trusted_bot(message):
        return
    
    content = message.content
    
    treasury_pattern = r"(.+?) gave .*?TREASURY_USER.*?(\\d+[,]?\\d*)[kK]?\\s*PokeCoins"
    
    match = re.search(treasury_pattern, content, re.IGNORECASE)
    if not match:
        return
    
    donor_text = match.group(1).strip()
    amount_str = match.group(2).replace(',', '')
    
    # Convert amount to integer
    try:
        amount = int(amount_str)
    except ValueError:
        return
    
    # Check if amount meets threshold
    if amount < 100000:
        return
    
    # Extract donor name
    donor_name = extract_donor_name(donor_text)
    if not donor_name:
        print(f"⚠️ Could not extract donor name from: {donor_text}")
        return
    
    # Find the member
    donor = await find_member_by_name(message.guild, donor_name)
    if not donor:
        print(f"⚠️ Could not find member with name: {donor_name}")
        return
    
    # Handle the successful donation
    await handle_successful_donation(donor, amount, message.channel)

TRUSTED_BOT_ROLES = ["BOT_ROLE_2", "BOT_ROLE_3"]

async def is_trusted_bot(message):
    """Check if message is from a trusted bot (BOT_ROLE_2 or BOT_ROLE_3)"""
    
    # Check if the author is a bot
    if not message.author.bot:
        return False
    
    # Check if author is a Member (has roles attribute) - NOT a User object
    if not isinstance(message.author, discord.Member):
        return False
    
    # Check if author has one of the trusted roles
    for role_name in TRUSTED_BOT_ROLES:
        role = discord.utils.get(message.guild.roles, name=role_name)
        if role and role in message.author.roles:
            return True
    
    return False


def extract_donor_name(donor_text):
    """Extract the donor name from the text, removing bold markers and extra spaces"""
    # Remove **bold** markers if present
    clean_text = re.sub(r'\*\*', '', donor_text)
    
    # Remove any remaining emoji or special characters at the start/end
    clean_text = clean_text.strip()
    
    # If there are multiple words, take the last one (usually the username)
    words = clean_text.split()
    if words:
        return words[-1]
    
    return clean_text

async def find_member_by_name(guild, name):
    """Find a member by display name or username with flexible matching"""
    clean_name = name.strip()
    
    # Try exact matches first
    member = discord.utils.get(guild.members, display_name=clean_name)
    if member:
        return member
    
    member = discord.utils.get(guild.members, name=clean_name)
    if member:
        return member
    
    # Try case-insensitive matches
    for member in guild.members:
        if member.display_name.lower() == clean_name.lower():
            return member
    
    for member in guild.members:
        if member.name.lower() == clean_name.lower():
            return member
    
    # Try partial matches
    for member in guild.members:
        if clean_name.lower() in member.display_name.lower():
            return member
    
    for member in guild.members:
        if clean_name.lower() in member.name.lower():
            return member
    
    return None

async def handle_successful_donation(member, amount, channel):
    """Handle successful donation by removing inactive role if present"""
    try:
        inactive_role = discord.utils.get(member.guild.roles, name=INACTIVE_ROLE_NAME)
        active_role = discord.utils.get(member.guild.roles, name=ACTIVE_ROLE_NAME)
        
        if not inactive_role:
            return
        
        # Check if member has inactive role
        if inactive_role in member.roles:
            # Remove inactive role
            await member.remove_roles(inactive_role)
            
            # Add active role if it exists
            if active_role and active_role not in member.roles:
                await member.add_roles(active_role)
            
            # Send notification
            notification = await channel.send(
                f"🎉 {member.mention} thank you for your donation of {amount:,} PokéCoins! "
                f"Your **{INACTIVE_ROLE_NAME}** role has been removed."
            )
            
            
            print(f"✅ Removed inactive role from {member.display_name} after donation of {amount:,}")
        
    except Exception as e:
        print(f"❌ Error handling donation for {member.display_name}: {e}")

@bot.command(name='testdonation')
@commands.has_role(MOD_ROLE_NAME)
async def test_donation(ctx, amount: int = 100000, member: discord.Member = None):
    """Test the donation detection system (Mods only)"""
    if member is None:
        member = ctx.author
    
    # Find a trusted bot to simulate the message from
    trusted_bot = None
    for role_name in TRUSTED_BOT_ROLES:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            # Get the first bot that has this role
            for guild_member in ctx.guild.members:
                if guild_member.bot and role in guild_member.roles:
                    trusted_bot = guild_member
                    break
            if trusted_bot:
                break
    
    if not trusted_bot:
        await ctx.send("❌ No trusted bot found with the specified roles. Using current user for test.")
        trusted_bot = ctx.author
    
    # Test message that matches the real BOT_ROLE_2 format
    test_messages = [
        f"**{member.display_name}** gave **TREASURY_USER** {amount:,} PokeCoins!",
        f":moneybag: **{member.display_name}** gave :smiley: **TREASURY_USER** {amount:,} PokeCoins!",
        f"**{member.display_name}** gave **TREASURY_USER** {amount}k PokeCoins!",
    ]
    
    for i, test_msg in enumerate(test_messages, 1):
        # Create a mock message object that appears to be from the trusted bot
        class MockMessage:
            def __init__(self, content, author, channel, guild):
                self.content = content
                self.author = author
                self.channel = channel
                self.guild = guild
        
        mock_msg = MockMessage(
            content=test_msg,
            author=trusted_bot,
            channel=ctx.channel,
            guild=ctx.guild
        )
        
        await ctx.send(f"🧪 Test {i}:\n`{test_msg}`")
        
        # Check if our system would trust this bot
        is_trusted = await is_trusted_bot(mock_msg)
        if is_trusted:
            await check_donation_message(mock_msg)
        else:
            await ctx.send("❌ This message would NOT be trusted (bot doesn't have required roles)")
        
        await asyncio.sleep(2)  # Small delay between tests
    
    await ctx.send("✅ Donation tests completed! Check if inactive role was removed.")


@tasks.loop(hours=168)
async def thursday_fee_reminder():
    """Send polite reminders to inactive catchers about weekly fees"""
    print("Starting Thursday fee reminder process...")
    
    for guild in bot.guilds:
        try:
            inactive_role = get_role(guild, INACTIVE_ROLE_NAME)
            if not inactive_role:
                continue
            
            # Get all inactive members
            inactive_members = [m for m in inactive_role.members if m.id not in IGNORED_USER_IDS]
            
            for member in inactive_members:
                # Find their personal channel
                personal_channel_id = None
                for channel_id, owner_id in channel_owners.items():
                    if owner_id == member.id:
                        personal_channel_id = int(channel_id)
                        break
                
                if personal_channel_id:
                    personal_channel = bot.get_channel(personal_channel_id)
                    if personal_channel:
                        # Send polite reminder with @TREASURY_USER display
                        reminder_embed = discord.Embed(
                            title="💜 Friendly Weekly Reminder",
                            description=f"Hello! 👋\n\n"
                                      f"Just a reminder that you haven't completed this week's catch goal yet. "
                                      f"When you have a moment, please consider:\n\n"
                                      f"• Sending **100K** to @TREASURY_USER, or\n"
                                      f"• Tagging any moderator/requesting a break through a command here if you need to be excused\n\n"
                                      f"Thanks!",
                            color=discord.Color.purple()
                        )
                        
                        await personal_channel.send(embed=reminder_embed)
                        print(f"Sent reminder to {member.display_name}")
                        
                        await asyncio.sleep(1)
            
            print(f"Thursday reminders sent to {len(inactive_members)} members in {guild.name}")
                    
        except Exception as e:
            print(f"Error sending Thursday reminders in {guild.name}: {e}")  # Changed from printf

@thursday_fee_reminder.before_loop
async def before_thursday_reminder():
    """Wait until next Thursday at 10:00 AM EST before starting the loop"""
    await bot.wait_until_ready()
    
    now = datetime.now(TIMEZONE)
    
    # Calculate days until next Thursday (weekday 3 = Thursday, 0 = Monday)
    days_until_thursday = (3 - now.weekday()) % 7
    
    # Set target time to 10:00 AM EST on Thursday
    next_thursday = now + timedelta(days=days_until_thursday)
    next_thursday = next_thursday.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # If we're already past Thursday 10 AM this week, schedule for next Thursday
    if next_thursday <= now:
        next_thursday += timedelta(days=7)
    
    # Calculate seconds until that time
    seconds_until_thursday = (next_thursday - now).total_seconds()
    
    print(f"Thursday reminder scheduled for {next_thursday.strftime('%Y-%m-%d %H:%M:%S %Z')}. Waiting {seconds_until_thursday/3600:.1f} hours...")
    
    # Wait until Thursday
    await asyncio.sleep(seconds_until_thursday)

# Run the bot
bot.run('token')
