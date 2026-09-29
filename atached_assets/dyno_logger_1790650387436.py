import re
import discord
from discord import app_commands
from discord.ext import commands
from variables.config import ALLOWED_ROLE_IDS

# Targeted channel ID
TARGET_CHANNEL_ID = 1516263846149357660

class DynoLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_log_message_id = None  # Stores the ID of the latest bot log message

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages sent by this bot itself
        if message.author.id == self.bot.user.id:
            return

        # Ensure message is strictly in the specified target channel
        if message.channel.id != TARGET_CHANNEL_ID:
            return

        # Initialize parsed fields
        moderator = None
        affected_user = None
        action = None
        reason = None

        # Case A: Dyno Embed Log Parsing
        if message.embeds:
            embed = message.embeds[0]
            
            for field in embed.fields:
                name_lower = field.name.lower()
                if "moderator" in name_lower:
                    moderator = field.value
                elif "user" in name_lower or "member" in name_lower:
                    affected_user = field.value
                elif "action" in name_lower or "type" in name_lower:
                    action = field.value
                elif "reason" in name_lower:
                    reason = field.value

            if not moderator and embed.author:
                moderator = embed.author.name

        # Case B: Standard Dyno Plain Text Log Parsing
        elif message.content:
            content = message.content
            mod_match = re.search(r'(?:Moderator|Mod):\s*(<@!?\d+>|\w+#\d+|\S+)', content, re.IGNORECASE)
            user_match = re.search(r'(?:User|Target|Member):\s*(<@!?\d+>|\w+#\d+|\S+)', content, re.IGNORECASE)
            action_match = re.search(r'(?:Action):\s*([^\n|]+)', content, re.IGNORECASE)
            reason_match = re.search(r'(?:Reason):\s*([^\n|]+)', content, re.IGNORECASE)

            if mod_match:
                moderator = mod_match.group(1)
            if user_match:
                affected_user = user_match.group(1)
            if action_match:
                action = action_match.group(1).strip()
            if reason_match:
                reason = reason_match.group(1).strip()

        # If a valid moderation log was detected
        if moderator or affected_user:
            mod_text = moderator if moderator else f"<@{message.author.id}>"
            user_text = affected_user if affected_user else "Unknown User"
            action_text = action if action else "Warning / Punishment"
            reason_text = reason if reason else "No reason provided."

            # Construct formatted embed
            formatted_embed = discord.Embed(
                description=f"{mod_text} Used **/punish** to {user_text}",
                color=discord.Color.dark_theme()
            )

            formatted_embed.add_field(
                name="Message Sent:",
                value=f"**Punishment:** {action_text}\n**Reason:** {reason_text}",
                inline=False
            )

            formatted_embed.add_field(
                name="Support Server:",
                value="https://discord.gg/fsFH85WGr7",
                inline=False
            )

            # 1. Delete the previous log message sent by this bot
            if self.last_log_message_id:
                try:
                    old_msg = await message.channel.fetch_message(self.last_log_message_id)
                    await old_msg.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

            # 2. Delete the trigger/incoming Dyno message to clear space
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException):
                pass

            # 3. Send the new embed and store its message ID
            new_msg = await message.channel.send(embed=formatted_embed)
            self.last_log_message_id = new_msg.id

    @app_commands.command(name="logcheck", description="Manually verify channel logging permissions.")
    async def logcheck(self, interaction: discord.Interaction):
        """Slash command check restricted to the 9 allowed role IDs."""
        has_role = any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Dyno log listener active in <#{TARGET_CHANNEL_ID}>.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DynoLogger(bot))