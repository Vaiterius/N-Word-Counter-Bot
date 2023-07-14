import discord
from discord.ext import commands
from utils.database import Database
from utils.discord import generate_message_embed

DEFAULT_SETTINGS = [
    {
        "name": "Send Message",
        "int_name": "send_message",
        "description": "Whether or not the bot should send messages in response to nwords",
        "type": "bool",
        "default": True,
        "value": True
    }
]


class SettingModal(discord.ui.Modal):
    def __init__(self, settingName: str = None, settingValue: str = "", *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db = Database()
        self.custom_id = str(settingValue)
        self.add_item(discord.ui.InputText(label=settingName, value=settingValue))

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.edit_original_response(view=None)
        new_setting = interaction.to_dict()["data"]["components"][0]["components"][0]["value"].upper().strip()
        old_setting = interaction.to_dict()["data"]["custom_id"].upper().strip()
        setting_name = interaction.to_dict()["message"]["components"][0]["components"][0]["custom_id"]
        settings = await self.db.get_internal_guild_settings(interaction.guild.id)
        if not settings:
            settings = DEFAULT_SETTINGS
        for setting in settings:
            if setting["int_name"] == setting_name:
                if setting["type"] == "bool":
                    if new_setting == "TRUE" or new_setting == "FALSE":
                        setting["value"] = new_setting == "TRUE"
                    else:
                        await interaction.edit_original_response(embed=await generate_message_embed(
                            title="Invalid Setting",
                            text=f"Setting `{setting_name}` must be either `TRUE` or `FALSE` not `{new_setting}`",
                            type="error"
                        ), view=None, content=None, delete_after=5)
                        return False
        await self.db.update_guild_settings(interaction.guild.id, settings)
        embed = await generate_message_embed(
            title="Setting Changed",
            text=f"Setting `{setting_name}` changed from `{old_setting}` to `{new_setting}`",
            type="success"
        )
        await interaction.edit_original_response(embed=embed, view=None, content=None, delete_after=5)


class GuildSettings(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot
        self.db = Database()

    def generate_settings_options(self, settings):
        return [discord.SelectOption(label=setting["name"], description=setting["description"],
                                     value=setting["int_name"]) for setting in settings]

    # Oh my god this is so ugly - i'm so sorry
    @commands.slash_command(name="settings", description="Change settings for this guild")
    async def settings(self, ctx: discord.ApplicationContext):
        async def settings_callback(ctx: discord.Interaction):
            async def button_callback(ctx: discord.Interaction):
                settings = await self.db.get_internal_guild_settings(ctx.guild.id)
                settingName = ctx.to_dict()["message"]["components"][0]["components"][0]["custom_id"]
                settingTitle = settingName.replace("_", " ").title()
                if not settings:
                    settings = DEFAULT_SETTINGS
                for setting in settings:
                    if setting["int_name"] == settingName:
                        value = setting["value"]
                await ctx.response.send_modal(SettingModal(settingName=settingTitle, settingValue=value,
                                                           title=f"Change Setting (currently: {value})"))

            await ctx.response.defer()
            settings = await self.db.get_internal_guild_settings(ctx.guild.id)
            if not settings:
                settings = DEFAULT_SETTINGS
            for setting in settings:
                if setting["int_name"] in ctx.data["values"]:
                    embed = discord.Embed(title=setting["name"], description=setting["description"],
                                          color=discord.Color.blurple())
                    embed.add_field(name="Current Value", value=str(setting["value"]))
                    if setting["type"] == "bool":
                        embed.add_field(name="Possible Values", value="True, False")
                    elif setting["type"] == "int":
                        embed.add_field(name="Possible Values", value="Any integer")
                    elif setting["type"] == "str":
                        embed.add_field(name="Possible Values", value="Any string")
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Change Value", style=discord.ButtonStyle.blurple, custom_id=setting["int_name"]))
                    view.children[0].callback = button_callback
                    await ctx.edit_original_response(content=None, embed=embed, view=view)

        await ctx.defer()
        settings = await self.db.get_internal_guild_settings(ctx.guild.id)
        if not settings:
            settings = DEFAULT_SETTINGS
        embed = discord.Embed(title="Settings", description="Change settings for this guild",
                              color=discord.Color.blurple())
        for setting in settings:
            embed.add_field(name=setting["name"], value=f"Currently: {setting['value']}\n\n{setting['description']}", inline=False)
        view = discord.ui.View()
        view.add_item(discord.ui.Select(placeholder="Choose a Setting to change!",
                                        min_values=1,
                                        max_values=1,
                                        options=self.generate_settings_options(settings)))
        view.children[0].callback = settings_callback
        await ctx.respond(embed=embed, ephemeral=True, view=view)


def setup(bot):
    bot.add_cog(GuildSettings(bot))
