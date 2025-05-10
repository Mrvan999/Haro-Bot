
import discord
from discord.ext import commands
from discord import RawReactionActionEvent
import sqlite3
from datetime import datetime

DB_PATH = "data/bot.db"

def get_canal_por_tipo(guild_id: int, tipo: str) -> int | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT canal_id FROM canais_configurados WHERE guild_id = ? AND tipo = ?",
        (guild_id, tipo)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

class AprovacaoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member.bot:
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if not message.embeds:
            return

        embed = message.embeds[0]

        if embed.title != "📄 Ficha em Aprovação":
            return

        autor_reagiu = payload.member.display_name
        emoji = str(payload.emoji)

        if emoji == "✅":
            canal_destino_id = get_canal_por_tipo(guild.id, "Canal de Fichas Aprovadas")
            canal_destino = guild.get_channel(canal_destino_id)
            if canal_destino:
                embed.color = discord.Color.green()
                await canal_destino.send(embed=embed)
                await channel.send(f"✅ Ficha aprovada por {autor_reagiu} e enviada para {canal_destino.mention}", delete_after=10)
        elif emoji == "❌":
            def check(m):
                return m.author.id == payload.user_id and m.channel.id == payload.channel_id

            await channel.send(f"{payload.member.mention} ❌ Digite o motivo da reprovação da ficha:", delete_after=20)

            try:
                msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                motivo = msg.content

                embed.color = discord.Color.red()
                embed.add_field(name="❌ Motivo da Reprovação", value=motivo, inline=False)
                embed.set_author(name=f"Reprovada por {autor_reagiu}", icon_url=payload.member.display_avatar.url)

                canal_reprovado_id = get_canal_por_tipo(guild.id, "Canal de Fichas Reprovadas")
                canal_reprovado = guild.get_channel(canal_reprovado_id)

                if canal_reprovado:
                    await canal_reprovado.send(embed=embed)
                    await channel.send(f"📤 Ficha reprovada e enviada para {canal_reprovado.mention}", delete_after=10)
            except Exception:
                await channel.send("⏱️ Tempo esgotado para informar o motivo da reprovação.", delete_after=10)

async def setup(bot: commands.Bot):
    await bot.add_cog(AprovacaoHandler(bot))
