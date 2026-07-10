import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1524855039909298326

ROLE_CITOYEN = int(os.getenv("ROLE_CITOYEN"))
ROLE_TOURISTE = int(os.getenv("ROLE_TOURISTE"))