import discord
from discord import app_commands
from discord.ext import commands

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        # General command open to everyone
        await interaction.response.send_message(f"🏓 Pong! Latency is `{round(self.bot.latency * 1000)}ms`")

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))