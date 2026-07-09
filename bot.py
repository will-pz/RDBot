import discord
from discord.ext import commands
import os
import logging

from config import TOKEN

# Logging propre dès le départ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RDBot")

# Intents : active seulement ce dont tu as besoin
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    logger.info(f"Connecté en tant que {bot.user} (ID: {bot.user.id})")


def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
            logger.info(f"Cog chargé : {filename}")


if __name__ == "__main__":
    load_cogs()
    bot.run(TOKEN)