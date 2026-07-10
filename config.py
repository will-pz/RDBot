import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1524855039909298326

ROLE_CITOYEN = int(os.getenv("1525072469038203011"))
ROLE_TOURISTE = int(os.getenv("1525072477892509767"))