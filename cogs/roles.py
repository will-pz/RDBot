import discord
from discord.ext import commands, tasks
import logging

from config import ROLE_CITOYEN, ROLE_TOURISTE
from logs import log

logger = logging.getLogger("RDBot")


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_touristes.start()

    def cog_unload(self):
        self.check_touristes.cancel()

    @commands.slash_command(description="Accueille un utilisateur en tant que citoyen")
    @commands.has_permissions(manage_roles=True)
    async def joinrecrue(self, ctx, membre: discord.Member):
        role_citoyen = ctx.guild.get_role(ROLE_CITOYEN)
        role_touriste = ctx.guild.get_role(ROLE_TOURISTE)

        if role_citoyen is None or role_touriste is None:
            await ctx.respond("Rôle ROLE_CITOYEN ou ROLE_TOURISTE introuvable sur ce serveur.", ephemeral=True)
            return

        await membre.add_roles(role_citoyen, reason=f"/joinrecrue par {ctx.author}")
        await membre.remove_roles(role_touriste, reason=f"/joinrecrue par {ctx.author}")

        await ctx.respond(f"{membre.mention} est maintenant citoyen.")
        await log(self.bot, "/joinrecrue", ctx.author, membre.mention)

    @commands.slash_command(description="Retire tous les rôles d'un utilisateur sauf ROLE_TOURISTE")
    @commands.has_permissions(manage_roles=True)
    async def kick(self, ctx, membre: discord.Member):
        role_touriste = ctx.guild.get_role(ROLE_TOURISTE)

        if role_touriste is None:
            await ctx.respond("Rôle ROLE_TOURISTE introuvable sur ce serveur.", ephemeral=True)
            return

        roles_a_retirer = [r for r in membre.roles if r != ctx.guild.default_role and r != role_touriste]

        if roles_a_retirer:
            await membre.remove_roles(*roles_a_retirer, reason=f"/kick par {ctx.author}")

        if role_touriste not in membre.roles:
            await membre.add_roles(role_touriste, reason=f"/kick par {ctx.author}")

        await ctx.respond(f"Tous les rôles de {membre.mention} ont été retirés (sauf ROLE_TOURISTE).")
        await log(self.bot, "/kick", ctx.author, membre.mention)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        role_touriste = member.guild.get_role(ROLE_TOURISTE)
        if role_touriste is None:
            logger.warning("ROLE_TOURISTE introuvable, impossible de l'attribuer à %s", member)
            return

        await member.add_roles(role_touriste, reason="Arrivée sur le serveur")

    @tasks.loop(minutes=5)
    async def check_touristes(self):
        for guild in self.bot.guilds:
            role_touriste = guild.get_role(ROLE_TOURISTE)
            if role_touriste is None:
                continue

            for member in guild.members:
                if member.bot:
                    continue
                if len(member.roles) <= 1:  # seulement @everyone
                    await member.add_roles(role_touriste, reason="Aucun rôle détecté")

    @check_touristes.before_loop
    async def before_check_touristes(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Roles(bot))
