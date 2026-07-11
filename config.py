import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1524855039909298326

NG_API_KEY = os.getenv("NATIONSGLORY_API_KEY")
NG_BASE_URL = "https://publicapi.nationsglory.fr"

PAYS_NG = os.getenv("PAYS_NG")
SERVEUR_NG = os.getenv("SERVEUR_NG")

ROLE_CITOYEN = int(os.getenv("ROLE_CITOYEN"))
ROLE_TOURISTE = int(os.getenv("ROLE_TOURISTE"))

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))