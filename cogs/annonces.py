import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import json
import logging
import pathlib
import re

from logs import log

logger = logging.getLogger("RDBot")

FOOTER_TEXT = "République Dominicaine - Nations Glory Blue"

COLOR_ANNONCE = discord.Color(0xD21E26)
COLOR_GUERRE = discord.Color(0x8B0000)
COLOR_PAIX = discord.Color(0x1E7A3F)
COLOR_VOTE = discord.Color(0x002D62)

EMOJI_OUI = "✅"
EMOJI_NON = "❌"

DUREE_RE = re.compile(r"^(\d+)([mhd])$", re.IGNORECASE)
DUREE_UNITES = {"m": "minutes", "h": "hours", "d": "days"}

VOTES_FILE = pathlib.Path(__file__).resolve().parent.parent / "data" / "votes.json"


class Annonces(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.votes = self._load_votes()
        self.sync_votes.start()

    def cog_unload(self):
        self.sync_votes.cancel()

    def _icon_url(self, ctx):
        return ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None

    def _footer(self, embed, ctx):
        embed.set_footer(text=FOOTER_TEXT, icon_url=self._icon_url(ctx))
        embed.timestamp = discord.utils.utcnow()

    @commands.slash_command(description="Envoie une annonce générale")
    @commands.has_permissions(manage_messages=True)
    async def annonce(self, ctx, titre: str, message: str):
        embed = discord.Embed(title=titre, description=message, color=COLOR_ANNONCE)
        embed.set_author(name="République Dominicaine · Annonce", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Publié par", value=ctx.author.mention, inline=False)
        self._footer(embed, ctx)
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Déclare la guerre à un pays")
    @commands.has_permissions(manage_guild=True)
    async def guerre(self, ctx, pays_ennemi: str, raison: str, message: str):
        embed = discord.Embed(
            title=f"⚔️ Déclaration de guerre — {pays_ennemi}",
            description=message,
            color=COLOR_GUERRE,
        )
        embed.set_author(name="République Dominicaine · Ministère de la Défense", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Pays adverse", value=pays_ennemi, inline=True)
        embed.add_field(name="Casus belli", value=raison, inline=True)
        embed.add_field(name="Date d'effet", value=datetime.now().strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Ordonné par", value=ctx.author.mention, inline=True)
        self._footer(embed, ctx)
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Déclare la paix avec un pays")
    @commands.has_permissions(manage_guild=True)
    async def paix(self, ctx, pays_ennemi: str, message: str):
        embed = discord.Embed(
            title=f"🕊️ Traité de paix — {pays_ennemi}",
            description=message,
            color=COLOR_PAIX,
        )
        embed.set_author(name="République Dominicaine · Ministère de la Défense", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Pays concerné", value=pays_ennemi, inline=True)
        embed.add_field(name="Date d'effet", value=datetime.now().strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Ordonné par", value=ctx.author.mention, inline=True)
        self._footer(embed, ctx)
        await ctx.respond(embed=embed)

    # ---------------------------------------------------------------- votes

    def _load_votes(self) -> dict:
        if not VOTES_FILE.exists():
            return {}
        try:
            raw = json.loads(VOTES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return {int(vote_id): data for vote_id, data in raw.items()}

    def _save_votes(self):
        VOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {str(vote_id): data for vote_id, data in self.votes.items()}
        VOTES_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _find_vote_by_message(self, message_id: int):
        for vote in self.votes.values():
            if vote["message_id"] == message_id:
                return vote
        return None

    def _parse_duree(self, duree: str) -> timedelta:
        match = DUREE_RE.fullmatch(duree.strip())
        if not match:
            raise ValueError(f"Format de durée invalide : {duree}")
        valeur, unite = match.groups()
        return timedelta(**{DUREE_UNITES[unite.lower()]: int(valeur)})

    def _build_vote_embed(self, vote: dict, oui: int, non: int) -> discord.Embed:
        embed = discord.Embed(title=f"🗳️ {vote['titre']}", color=COLOR_VOTE)
        if vote.get("description"):
            embed.description = vote["description"]

        embed.set_author(name="République Dominicaine · Vote", icon_url=vote.get("author_avatar_url"))
        embed.add_field(name=f"{EMOJI_OUI} Oui", value=f"{oui} vote", inline=True)
        embed.add_field(name=f"{EMOJI_NON} Non", value=f"{non} vote", inline=True)

        auteur_mention = f"<@{vote['author_id']}>"
        if vote["closed"]:
            closed_at = datetime.fromtimestamp(vote["closed_at"], tz=timezone.utc)
            info = (
                f"Le vote s'est clôturé le {closed_at.strftime('%d/%m/%Y')} "
                f"à {closed_at.strftime('%Hh%M')} · Lancé par {auteur_mention}"
            )
        else:
            end_time = datetime.fromtimestamp(vote["end_time"], tz=timezone.utc)
            info = f"Le vote se clôture {discord.utils.format_dt(end_time, 'R')} · Lancé par {auteur_mention}"
        info += f"\nID de vote : `{vote['id']}`"
        embed.add_field(name="Informations", value=info, inline=False)

        embed.set_footer(text=FOOTER_TEXT, icon_url=vote.get("guild_icon_url"))
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def _refresh_vote_message(self, vote: dict):
        channel = self.bot.get_channel(vote["channel_id"])
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(vote["channel_id"])
            except discord.HTTPException:
                return

        try:
            message = await channel.fetch_message(vote["message_id"])
        except discord.HTTPException:
            # message supprimé ou inaccessible : on considère le vote clos
            vote["closed"] = True
            vote["closed_at"] = vote.get("closed_at") or datetime.now(timezone.utc).timestamp()
            self._save_votes()
            return

        oui = non = 0
        for reaction in message.reactions:
            if str(reaction.emoji) == EMOJI_OUI:
                oui = max(reaction.count - 1, 0)
            elif str(reaction.emoji) == EMOJI_NON:
                non = max(reaction.count - 1, 0)

        embed = self._build_vote_embed(vote, oui, non)
        await message.edit(embed=embed)

    async def _close_vote(self, vote: dict):
        vote["closed"] = True
        vote["closed_at"] = datetime.now(timezone.utc).timestamp()
        self._save_votes()
        await self._refresh_vote_message(vote)

    @commands.slash_command(description="Lance un vote")
    @commands.has_permissions(manage_messages=True)
    async def vote(self, ctx, duree: str, titre: str, message: str = None):
        try:
            delta = self._parse_duree(duree)
        except ValueError:
            await ctx.respond(
                "Durée invalide. Utilise le format Xm, Xh ou Xd (ex : 30m, 2h, 1d).", ephemeral=True
            )
            return

        if delta.total_seconds() <= 0:
            await ctx.respond("La durée doit être supérieure à 0.", ephemeral=True)
            return

        end_time = datetime.now(timezone.utc) + delta
        vote_id = ctx.interaction.id

        vote_data = {
            "id": vote_id,
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "message_id": None,
            "author_id": ctx.author.id,
            "author_avatar_url": ctx.author.display_avatar.url,
            "guild_icon_url": self._icon_url(ctx),
            "titre": titre,
            "description": message,
            "end_time": end_time.timestamp(),
            "closed": False,
            "closed_at": None,
        }

        embed = self._build_vote_embed(vote_data, 0, 0)
        await ctx.respond(embed=embed)
        message_envoye = await ctx.interaction.original_response()

        vote_data["message_id"] = message_envoye.id
        self.votes[vote_id] = vote_data
        self._save_votes()

        await message_envoye.add_reaction(EMOJI_OUI)
        await message_envoye.add_reaction(EMOJI_NON)

        await log(self.bot, "/vote", ctx.author, f"{titre} (ID {vote_id})")

    @commands.slash_command(description="Clôture prématurément un vote en cours")
    @commands.has_permissions(manage_messages=True)
    async def closevote(self, ctx, id: str):
        try:
            vote_id = int(id)
        except ValueError:
            await ctx.respond("ID de vote invalide.", ephemeral=True)
            return

        vote_data = self.votes.get(vote_id)
        if vote_data is None:
            await ctx.respond("Aucun vote trouvé avec cet ID.", ephemeral=True)
            return
        if vote_data["closed"]:
            await ctx.respond("Ce vote est déjà clôturé.", ephemeral=True)
            return

        await self._close_vote(vote_data)
        await ctx.respond(f"Le vote `{vote_id}` a été clôturé.", ephemeral=True)
        await log(self.bot, "/closevote", ctx.author, f"{vote_data['titre']} (ID {vote_id})")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        vote_data = self._reaction_vote(payload)
        if vote_data is None:
            return

        await self._enforce_single_choice(payload)
        await self._safe_refresh(vote_data)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        vote_data = self._reaction_vote(payload)
        if vote_data is None:
            return

        await self._safe_refresh(vote_data)

    def _reaction_vote(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return None
        if str(payload.emoji) not in (EMOJI_OUI, EMOJI_NON):
            return None

        vote_data = self._find_vote_by_message(payload.message_id)
        if vote_data is None or vote_data["closed"]:
            return None
        return vote_data

    async def _enforce_single_choice(self, payload: discord.RawReactionActionEvent):
        # Empêche de voter Oui et Non en même temps : la nouvelle réaction chasse l'autre.
        if payload.member is None:
            return

        autre_emoji = EMOJI_NON if str(payload.emoji) == EMOJI_OUI else EMOJI_OUI

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(payload.channel_id)
            except discord.HTTPException:
                return

        try:
            await channel.get_partial_message(payload.message_id).remove_reaction(autre_emoji, payload.member)
        except discord.HTTPException:
            pass

    async def _safe_refresh(self, vote_data: dict):
        try:
            await self._refresh_vote_message(vote_data)
        except discord.HTTPException:
            logger.warning("Impossible de mettre à jour le vote %s après une réaction", vote_data["id"])

    @tasks.loop(seconds=30)
    async def sync_votes(self):
        now = datetime.now(timezone.utc).timestamp()
        for vote_data in list(self.votes.values()):
            if vote_data["closed"]:
                continue
            try:
                if vote_data["end_time"] <= now:
                    await self._close_vote(vote_data)
                else:
                    await self._refresh_vote_message(vote_data)
            except discord.HTTPException:
                logger.warning("Erreur lors de la synchronisation du vote %s", vote_data["id"])

    @sync_votes.before_loop
    async def before_sync_votes(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Annonces(bot))
