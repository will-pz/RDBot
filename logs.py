import discord
import logging

from config import LOG_CHANNEL_ID

logger = logging.getLogger("RDBot")

COLOR_LOG = discord.Color(0xD21E26)


async def log(bot: discord.Bot, source: str, auteur: discord.abc.User, cible: str):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        except discord.HTTPException:
            logger.warning("Salon de logs introuvable (LOG_CHANNEL_ID=%s)", LOG_CHANNEL_ID)
            return

    embed = discord.Embed(
        description=f"**{auteur.mention}** a effectuée la commande **{source}** : **{cible}**",
        color=COLOR_LOG,
    )
    icon_url = channel.guild.icon.url if channel.guild and channel.guild.icon else None
    embed.set_author(name="République Dominicaine · Logs", icon_url=icon_url)

    await channel.send(embed=embed)
