import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Vérifie que le bot répond")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.respond(f"Pong ! Latence : {latency}ms")

    @commands.slash_command(description="Affiche des infos sur le serveur")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blue())
        embed.add_field(name="Membres", value=guild.member_count)
        embed.add_field(name="Créé le", value=guild.created_at.strftime("%d/%m/%Y"))
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))