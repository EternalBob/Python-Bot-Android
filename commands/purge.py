import discord
from discord import app_commands
from discord.ext import commands
from variables.config import PURGE_ALLOWED_ROLES

class TimeGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="time", description="Time and management utilities")

    @app_commands.command(name="purge", description="Purge a specified number of messages from the channel.")
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, interaction: discord.Interaction, amount: int):
        has_role = any(role.id in PURGE_ALLOWED_ROLES for role in interaction.user.roles)
        if not has_role:
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ Please specify a number greater than 0.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Successfully purged {len(deleted)} message(s).", ephemeral=True)

async def setup(bot):
    bot.tree.add_command(TimeGroup())
