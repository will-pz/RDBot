import asyncio
import json
import logging

import aiohttp
import discord
from discord.ext import commands

from config import NG_API_KEY, NG_BASE_URL, PAYS_NG, SERVEUR_NG

logger = logging.getLogger("RDBot")

COLOR_NOTATION = discord.Color(0x002D62)

# Clés candidates pour deviner où se trouve la liste de résultats dans le JSON,
# et pour choisir un intitulé de champ plus parlant que "Résultat N".
CLES_LISTE_CANDIDATES = ("data", "results", "notations", "items")
CLES_NOM_CANDIDATES = ("name", "nom", "pseudo", "player", "ville", "town", "city")

# L'API publique NationsGlory peut être lente : on lui laisse un peu de marge
# avant d'abandonner, en plus du ctx.defer() qui protège l'interaction Discord.
NG_TIMEOUT = aiohttp.ClientTimeout(total=10)


def _extraire_liste(payload):
    """Tente de retrouver la liste de résultats dans une réponse JSON de forme inconnue."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for cle in CLES_LISTE_CANDIDATES:
            valeur = payload.get(cle)
            if isinstance(valeur, list):
                return valeur
    return None


def _formatter_resultat(resultat) -> str:
    """Formate un élément de la liste en texte lisible, en tronquant si besoin."""
    if not isinstance(resultat, dict):
        texte = str(resultat)
    else:
        texte = "\n".join(f"**{cle}** : {valeur}" for cle, valeur in resultat.items())

    if len(texte) > 1000:
        texte = texte[:1000] + "…"
    return texte or "—"


def _nom_resultat(resultat, index: int) -> str:
    """Choisit un nom de champ plus parlant si une clé usuelle est présente."""
    if isinstance(resultat, dict):
        for cle in CLES_NOM_CANDIDATES:
            valeur = resultat.get(cle)
            if valeur:
                return str(valeur)[:256]
    return f"Résultat {index}"


class Notations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _build_embed(self, payload, country: str, server: str, week: int) -> discord.Embed:
        embed = discord.Embed(title="📊 Notations NationsGlory", color=COLOR_NOTATION)

        criteres = []
        if country:
            criteres.append(f"Pays : **{country}**")
        if server:
            criteres.append(f"Serveur : **{server}**")
        if week is not None:
            criteres.append(f"Semaine : **{week}**")

        resultats = _extraire_liste(payload)

        if resultats is not None:
            embed.description = " · ".join(criteres) if criteres else None

            if not resultats:
                embed.add_field(name="Résultat", value="Aucune notation trouvée pour ces critères.", inline=False)
            else:
                affiches = resultats[:10]
                for index, resultat in enumerate(affiches, start=1):
                    embed.add_field(
                        name=_nom_resultat(resultat, index),
                        value=_formatter_resultat(resultat),
                        inline=False,
                    )
                if len(resultats) > len(affiches):
                    embed.set_footer(text=f"{len(affiches)} résultat(s) affiché(s) sur {len(resultats)}.")
        else:
            # Structure inattendue : on retombe sur un affichage brut du JSON, tronqué
            # pour rester dans la limite de 4096 caractères d'une description d'embed.
            entete = (" · ".join(criteres) + "\n\n") if criteres else ""
            brut = json.dumps(payload, indent=2, ensure_ascii=False)
            place_dispo = 4000 - len(entete) - len("```json\n\n```")
            if len(brut) > place_dispo:
                brut = brut[:place_dispo] + "\n… (tronqué)"
            embed.description = f"{entete}```json\n{brut}\n```"

        embed.timestamp = discord.utils.utcnow()
        return embed

    @commands.slash_command(description="Affiche les notations NationsGlory d'un pays/serveur")
    async def notation(self, ctx, country: str = None, server: str = None, week: int = None):
        if not NG_API_KEY:
            await ctx.respond(
                "Clé API NationsGlory manquante (NATIONSGLORY_API_KEY). Contacte un administrateur.",
                ephemeral=True,
            )
            return

        # L'appel à l'API externe peut dépasser les 3 secondes accordées par
        # Discord pour répondre à une interaction : on defer immédiatement.
        await ctx.defer()

        country = country or PAYS_NG
        server = server or SERVEUR_NG

        params = {}
        if country:
            params["country"] = country
        if server:
            params["server"] = server
        if week is not None:
            params["week"] = week

        headers = {"Authorization": NG_API_KEY}

        try:
            async with aiohttp.ClientSession(timeout=NG_TIMEOUT) as session:
                async with session.get(f"{NG_BASE_URL}/notations", headers=headers, params=params) as response:
                    if response.status != 200:
                        logger.warning("Appel /notations en échec (statut %s)", response.status)
                        await ctx.respond(
                            f"L'API NationsGlory a répondu avec une erreur (statut {response.status}). "
                            "Réessaie plus tard.",
                            ephemeral=True,
                        )
                        return

                    try:
                        data = await response.json()
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        logger.warning("Réponse /notations non-JSON reçue")
                        await ctx.respond(
                            "La réponse de l'API NationsGlory n'a pas pu être interprétée.", ephemeral=True
                        )
                        return
        except asyncio.TimeoutError:
            logger.warning("Timeout lors de l'appel à l'API NationsGlory (/notations)")
            await ctx.respond(
                "L'API NationsGlory met trop de temps à répondre. Réessaie plus tard.", ephemeral=True
            )
            return
        except aiohttp.ClientError as erreur:
            logger.warning("Erreur réseau lors de l'appel à l'API NationsGlory : %s", erreur)
            await ctx.respond("Impossible de contacter l'API NationsGlory pour le moment.", ephemeral=True)
            return

        embed = self._build_embed(data, country, server, week)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Notations(bot))
