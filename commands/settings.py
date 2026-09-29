import os
import json
import discord
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "variables/command_settings.json"

# Load or initialize command states (Default all ON: True)
def load_command_states():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"purge": True, "dyno_logger": True, "settings": True}

def save_command_states(states):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(states, f, indent=4)

COMMAND_STATES = load_command_states()

def is_command_enabled(command_name: str) -> bool:
    return COMMAND_STATES.get(command_name, True)


def create_main_settings_embed():
    embed = discord.Embed(
        title="⚙️ Bot Settings",
        description="Select an option below to manage log channels or enable/disable bot commands.",
        color=discord.Color.blurple()
    )
    return embed


def create_toggle_embed(states):
    embed = discord.Embed(
        title="⚙️ Enable / Disable Commands",
        description="Click any command button to toggle its status, then click **Save** at the bottom.",
        color=discord.Color.blue()
    )
    for cmd, enabled in states.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        embed.add_field(name=f"/{cmd}", value=status, inline=True)
    return embed


class CommandToggleView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.temp_states = COMMAND_STATES.copy()
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        
        # Command Toggle Buttons
        for cmd_name, enabled in self.temp_states.items():
            if cmd_name == "settings": 
                continue  # Keep settings always accessible
            
            symbol = "✅" if enabled else "❌"
            style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.danger
            
            button = discord.ui.Button(
                label=f"/{cmd_name} {symbol}",
                style=style
            )
            button.callback = self._make_toggle_callback(cmd_name)
            self.add_item(button)

        # Save Button
        save_btn = discord.ui.Button(
            label="💾 Save",
            style=discord.ButtonStyle.primary,
            row=4
        )
        save_btn.callback = self.save_callback
        self.add_item(save_btn)

        # Back Button
        back_btn = discord.ui.Button(
            label="⬅️ Back",
            style=discord.ButtonStyle.secondary,
            row=4
        )
        back_btn.callback = self.back_callback
        self.add_item(back_btn)

    def _make_toggle_callback(self, cmd_name):
        async def callback(interaction: discord.Interaction):
            self.temp_states[cmd_name] = not self.temp_states[cmd_name]
            self._build_buttons()
            embed = create_toggle_embed(self.temp_states)
            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    async def save_callback(self, interaction: discord.Interaction):
        global COMMAND_STATES
        COMMAND_STATES.update(self.temp_states)
        save_command_states(COMMAND_STATES)
        
        embed = discord.Embed(
            title="✅ Settings Saved",
            description="Command availability rules have been updated successfully.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def back_callback(self, interaction: discord.Interaction):
        view = SettingsMainView(self.author_id)
        embed = create_main_settings_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can edit settings.", ephemeral=True)
            return False
        return True


class SettingsMainView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=180)
        self.author_id = author_id

    @discord.ui.button(label="📋 Log Channels", style=discord.ButtonStyle.primary, emoji="📋")
    async def logs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        from variables import config
        
        search_log = getattr(config, 'SEARCH_LOG_CHANNEL_ID', 'Not Configured')
        output_log = getattr(config, 'LOG_CHANNEL_ID', 'Not Configured')

        search_val = f"<#{search_log}>" if isinstance(search_log, int) else str(search_log)
        output_val = f"<#{output_log}>" if isinstance(output_log, int) else str(output_log)

        embed = discord.Embed(
            title="📋 Log Channels Overview",
            color=discord.Color.gold()
        )
        embed.add_field(name="🔍 Searching Log Channel", value=search_val, inline=False)
        embed.add_field(name="📥 Target Output Log Channel", value=output_val, inline=False)

        back_view = discord.ui.View()
        back_btn = discord.ui.Button(label="⬅️ Back", style=discord.ButtonStyle.secondary)
        
        async def back_cb(inter: discord.Interaction):
            await inter.response.edit_message(embed=create_main_settings_embed(), view=SettingsMainView(self.author_id))
            
        back_btn.callback = back_cb
        back_view.add_item(back_btn)

        await interaction.response.edit_message(embed=embed, view=back_view)

    @discord.ui.button(label="⚙️ Enable / Disable Commands", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        toggle_view = CommandToggleView(self.author_id)
        embed = create_toggle_embed(toggle_view.temp_states)
        await interaction.response.edit_message(embed=embed, view=toggle_view)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command user can edit settings.", ephemeral=True)
            return False
        return True


class SettingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="settings", description="Manage bot log channels and command availability.")
    async def settings(self, interaction: discord.Interaction):
        view = SettingsMainView(interaction.user.id)
        embed = create_main_settings_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
