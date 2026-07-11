import discord
from discord.ext import commands
from datetime import datetime, timedelta

FOOTER_TEXT = "République Dominicaine - Nations Glory Blue"

COLOR_ANNONCE = discord.Color(0xD21E26)
COLOR_GUERRE = discord.Color(0x8B0000)
COLOR_PAIX = discord.Color(0x1E7A3F)
COLOR_VOTE = discord.Color(0x002D62)


class Annonces(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.slash_command(description="Lance un vote")
    @commands.has_permissions(manage_messages=True)
    async def vote(
        self,
        ctx,
        titre: str,
        message: str,
        option_1: str = "Oui",
        option_2: str = "Non",
        duree_heures: int = 24,
    ):
        date_fin = datetime.now() + timedelta(hours=duree_heures)
        embed = discord.Embed(title=f"🗳️ {titre}", description=message, color=COLOR_VOTE)
        embed.set_author(name="République Dominicaine · Vote", icon_url=ctx.author.display_avatar.url)
        embed.add_field(name=f"✅ {option_1}", value="0 vote", inline=True)
        embed.add_field(name=f"❌ {option_2}", value="0 vote", inline=True)
        embed.add_field(
            name="Informations",
            value=f"Vote clôturé le {date_fin.strftime('%d/%m/%Y à %Hh%M')} · Lancé par {ctx.author.mention}",
            inline=False,
        )
        self._footer(embed, ctx)
        await ctx.respond(embed=embed)

        message_envoye = await ctx.interaction.original_response()
        await message_envoye.add_reaction("✅")
        await message_envoye.add_reaction("❌")


def setup(bot):
    bot.add_cog(Annonces(bot))
