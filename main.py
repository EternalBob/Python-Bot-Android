import os
import sys
import discord
from discord.ext import commands
from keep_alive import keep_alive

# Load Token from config module or environment variable
try:
    from variables import config
    TOKEN = getattr(config, 'TOKEN', None) or os.getenv("TOKEN")
except ImportError:
    TOKEN = os.getenv("TOKEN")

# Initialize Bot Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Initialize Bot Instance
bot = commands.Bot(command_prefix="!", intents=intents)


# Global Interaction Check to enforce command enabling/disabling
@bot.tree.interaction_check
async def global_command_check(interaction: discord.Interaction) -> bool:
    if interaction.command:
        cmd_name = interaction.command.name
        # Allow /settings to always remain accessible
        if cmd_name != "settings":
            try:
                from commands.settings import is_command_enabled
                if not is_command_enabled(cmd_name):
                    await interaction.response.send_message(
                        f"❌ The `/{cmd_name}` command is currently disabled in `/settings`.",
                        ephemeral=True
                    )
                    return False
            except ImportError:
                pass  # Fallback if settings cog hasn't been loaded
    return True


# Setup Hook: Loads cogs and syncs slash commands on startup
@bot.event
async def setup_hook():
    initial_extensions = [
        "commands.dyno_logger",
        "commands.purge",
        "commands.settings"
    ]

    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded extension: {extension}")
        except Exception as e:
            print(f"Failed to load extension {extension}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")


# Event: Bot Ready Confirmation
@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready and running!")
    print("----------------------------------------")


# Application Entry Point
def main():
    # Start Flask Web Server
    keep_alive()

    if not TOKEN:
        print("CRITICAL ERROR: Discord Bot Token is missing!")
        print("Please configure TOKEN in variables/config.py or export TOKEN in your environment.")
        sys.exit(1)

    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("CRITICAL ERROR: Invalid Discord Bot Token supplied.")
    except Exception as e:
        print(f"An unexpected error occurred while running the bot: {e}")


if __name__ == "__main__":
    main()
