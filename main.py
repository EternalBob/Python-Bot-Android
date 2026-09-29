import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import variables.config as config
from keep_alive import keep_alive

TOKEN = getattr(config, 'TOKEN', None) or \
        getattr(config, 'DISCORD_TOKEN', None) or \
        getattr(config, 'BOT_TOKEN', None) or \
        getattr(config, 'token', None) or \
        os.getenv("DISCORD_TOKEN") or \
        os.getenv("TOKEN")

GUILD_ID = 1516263846149357660

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name="Monitoring Moderation Logs")
    )

    guild = discord.Object(id=GUILD_ID)

    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"✅ Active and synced {len(synced)} command(s) to server {GUILD_ID}.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(f"❌ Error executing /{interaction.command.name if interaction.command else 'unknown'}: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def load_extensions():
    for ext in ["commands.dyno_logger", "commands.purge"]:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"Failed to load {ext}: {e}")

async def main():
    async with bot:
        await load_extensions()
        keep_alive()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())