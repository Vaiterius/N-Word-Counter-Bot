import io
import aiohttp
import discord
from PIL import Image


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


async def generate_color(image_url: str):
    """Generate a similar color to the album cover of the song.
    :param image_url: The url of the album cover.
    :return discord.Color: A discord color.
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                return discord.Color.blurple()
            f = io.BytesIO(await resp.read())
    image = Image.open(f)
    # Get average color of the image
    colors = image.getcolors(image.size[0] * image.size[1])
    # Sort the colors by the amount of pixels and get the most common color
    colors.sort(key=lambda x: x[0], reverse=True)
    # Get the color of the most common color
    color = colors[0][1]
    try:
        if len(color) < 3:
            return discord.Color.blurple()
    except TypeError:
        return discord.Color.blurple()
    # Convert the color to a discord color
    return discord.Color.from_rgb(color[0], color[1], color[2])


async def generate_message_embed(text: str,
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
        color = await generate_color(ctx.author.avatar.url)
    elif type is None and color is not None:
        color = convert_color(color)
    else:
        raise ValueError("Invalid type")
    embed = discord.Embed(description=text, color=color, title=title)
    if ctx is not None:
        embed.set_footer(text=f"Command ran by {ctx.author.display_name} | {ctx.bot.user.name}",
                         icon_url=ctx.author.avatar.url)
    return embed
