import discord


def convert_color(color: tuple | str | discord.Color) -> discord.Color:
    """Converts a RGB tuple or hex to a discord.Color"""
    if isinstance(color, discord.Color):
        return color
    if isinstance(color, tuple):
        return discord.Color.from_rgb(*color)
    if isinstance(color, str) and color.startswith("#"):
        color = color.lstrip("#")
        return discord.Color.from_rgb(int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
    raise TypeError("Invalid color type, must be tuple or hex string starting with #")


def generate_message_embed(text: str,
                           type: str = None,
                           title: str = None,
                           ctx: discord.ApplicationContext = None,
                           color: discord.Color = None) -> discord.Embed:
    if type == "error":
        color = color or discord.Color.red()
        title = ":red_circle: Error"
    elif type == "success":
        color = color or discord.Color.green()
    elif type == "info":
        color = color or discord.Color.blue()
    elif type == "warning":
        color = color or discord.Color.orange()
        title = ":orange_circle: Warning"
    elif type is None and color is None:
        color = discord.Color.blurple()
    elif type is None and color is not None:
        color = convert_color(color)
    else:
        raise ValueError("Invalid type")
    embed = discord.Embed(description=text, color=color, title=title)
    if ctx is not None:
        embed.set_footer(text=f"Command ran by {ctx.author.display_name} | {ctx.bot.user.name}",
                         icon_url=ctx.author.avatar.url)
    return embed
