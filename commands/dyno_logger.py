import re
import discord
from discord import app_commands
from discord.ext import commands
from variables.config import ALLOWED_ROLE_IDS

TARGET_CHANNEL_ID = 1516263846149357660
ALLOWED_ACTIONS = {"/warn", "/mute", "/kick", "/ban"}

class DynoLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages sent by this bot itself
        if message.author.id == self.bot.user.id:
            return

        # Restrict strictly to the target channel
        if message.channel.id != TARGET_CHANNEL_ID:
            return

        moderator = None
        target_user_id = None
        target_user_str = None
        action = None
        reason = None

        # 1. Parse Dyno Embed Format
        if message.embeds:
            embed = message.embeds[0]

            if embed.author and embed.author.name:
                moderator = embed.author.name

            desc = embed.description or ""

            # Extract command string: e.g. /warn user: 123456789 reason: text
            cmd_match = re.search(r'(/[\w]+)\s+user:\s*(\d+|\S+)(?:\s+reason:\s*(.+))?', desc, re.IGNORECASE)
            if cmd_match:
                extracted_cmd = cmd_match.group(1).lower()
                if extracted_cmd in ALLOWED_ACTIONS:
                    action = extracted_cmd
                    user_raw = cmd_match.group(2)
                    reason = cmd_match.group(3).strip() if cmd_match.group(3) else None

                    if user_raw.isdigit():
                        target_user_id = int(user_raw)
                        target_user_str = f"<@{user_raw}>"
                    else:
                        target_user_str = user_raw

            # Check title for action if not found in description
            if not action and embed.title:
                title_lower = embed.title.lower()
                for allowed in ALLOWED_ACTIONS:
                    if allowed.strip('/') in title_lower:
                        action = allowed
                        break

            # Process fields
            for field in embed.fields:
                name_lower = field.name.lower()
                val = field.value.strip()

                if "moderator" in name_lower or "mod" in name_lower:
                    moderator = val
                elif "user" in name_lower or "member" in name_lower or "target" in name_lower:
                    target_user_str = val
                    id_m = re.search(r'(\d{17,20})', val)
                    if id_m:
                        target_user_id = int(id_m.group(1))
                elif "action" in name_lower or "type" in name_lower:
                    fmt_action = f"/{val.lower().replace('action:', '').strip()}"
                    if fmt_action in ALLOWED_ACTIONS:
                        action = fmt_action
                elif "reason" in name_lower:
                    reason = val

        # 2. Parse Plain Text Messages
        elif message.content:
            content = message.content
            mod_m = re.search(r'(?:Moderator|Mod):\s*(<@!?\d+>|\S+)', content, re.IGNORECASE)
            user_m = re.search(r'(?:User|Target|Member|user:):\s*(<@!?\d+>|\d+|\S+)', content, re.IGNORECASE)
            act_m = re.search(r'(?:Action|Command):\s*([^\n|]+)', content, re.IGNORECASE)
            rea_m = re.search(r'(?:Reason|reason:):\s*([^\n|]+)', content, re.IGNORECASE)

            if act_m:
                fmt_action = f"/{act_m.group(1).strip().lower().replace('/', '')}"
                if fmt_action in ALLOWED_ACTIONS:
                    action = fmt_action

            if mod_m: 
                moderator = mod_m.group(1)
            if user_m: 
                user_raw = user_m.group(1)
                if user_raw.isdigit():
                    target_user_id = int(user_raw)
                    target_user_str = f"<@{user_raw}>"
                else:
                    target_user_str = user_raw
            if rea_m: 
                reason = rea_m.group(1).strip()

        # Stop execution if the action is not one of /warn, /mute, /kick, or /ban
        if not action or action not in ALLOWED_ACTIONS:
            return

        mod_text = moderator if moderator else "Staff member"
        user_text = target_user_str if target_user_str else "User"
        reason_text = reason if reason else "No reason specified."

        # --- Send Channel Log ---
        log_embed = discord.Embed(
            description=(
                f"{mod_text} Used **{action}** on {user_text}\n\n"
                f"**Punishment:** {action}\n"
                f"**Reason:** {reason_text}\n\n"
                f"**Support Server:**\nhttps://discord.gg/fsFH85WGr7"
            ),
            color=discord.Color.dark_theme()
        )
        await message.channel.send(embed=log_embed)

        # --- Direct Message Target User ---
        if target_user_id:
            try:
                target_user = await self.bot.fetch_user(target_user_id)
                if target_user:
                    dm_embed = discord.Embed(
                        description=(
                            f"Staff member Used **{action}** on {target_user.name}\n\n"
                            f"**Punishment:** {action}\n"
                            f"**Reason:** {reason_text}\n\n"
                            f"**Support Server:**\nhttps://discord.gg/fsFH85WGr7"
                        ),
                        color=discord.Color.dark_theme()
                    )
                    await target_user.send(embed=dm_embed)
            except (discord.Forbidden, discord.HTTPException):
                pass

    @app_commands.command(name="logcheck", description="Manually verify channel logging permissions.")
    async def logcheck(self, interaction: discord.Interaction):
        has_role = any(role.id in ALLOWED_ROLE_IDS for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Dyno log listener active in <#{TARGET_CHANNEL_ID}>.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DynoLogger(bot))
