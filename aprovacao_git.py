import discord
from discord.ext import commands
from discord import RawReactionActionEvent
import aiosqlite
import asyncio

DB_PATH = "data/bot.db"

async def get_canal_por_tipo(guild_id: int, tipo: str) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT canal_id FROM canais_configurados WHERE guild_id = ? AND tipo = ?",
            (guild_id, tipo)
        )
        result = await cursor.fetchone()
        return result[0] if result else None

class AprovacaoHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.processadas = set()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member is None or payload.member.bot:
            return
        if payload.message_id in self.processadas:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not message.embeds:
            return

        embed = message.embeds[0]

        if not embed.title or not any(word in embed.title.lower() for word in ["aprova", "análise", "ficha"]):
            return

        emoji = str(payload.emoji)
        autor_reagiu = payload.member.display_name
        try:
            await message.remove_reaction(payload.emoji, payload.member)
        except discord.Forbidden:
            print(f"Sem permissão para remover reações em {guild.name}")
        except discord.HTTPException:
            pass
        self.processadas.add(payload.message_id)
        try:
            if emoji == "✅":
                canal_destino_id = await get_canal_por_tipo(guild.id, "Canal de Fichas Aprovadas")
                if not canal_destino_id:
                    await channel.send("❌ Canal de fichas aprovadas não configurado!", delete_after=10)
                    return

                canal_destino = guild.get_channel(canal_destino_id)

                async with aiosqlite.connect(DB_PATH) as db:
                    cursor = await db.execute(
                        "SELECT * FROM fichas_pendentes WHERE message_id = ? AND guild_id = ?",
                        (message.id, guild.id)
                    )
                    ficha = await cursor.fetchone()

                    if ficha:
                        await db.execute("""
                            INSERT INTO fichas_concluidas (
                                guild_id, user_id, nome, idade, altura, raca,
                                nacionalidade, genero, meta_poder, imagem_url,
                                data_criacao, status, data_avaliacao
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 'aprovada', CURRENT_TIMESTAMP)
                        """, (
                            ficha[1], ficha[2], ficha[4], ficha[5], ficha[6], ficha[7],
                            ficha[8], ficha[9], ficha[10], ficha[11]
                        ))

                        await db.execute("DELETE FROM fichas_pendentes WHERE id = ?", (ficha[0],))
                        await db.commit()

                if canal_destino:
                    new_embed = discord.Embed.from_dict(embed.to_dict())
                    new_embed.title = "✅ Ficha Aprovada"
                    new_embed.color = discord.Color.green()
                    if new_embed.image.url:
                        new_embed.set_image(url=new_embed.image.url)
                    elif new_embed.thumbnail.url:
                        new_embed.set_image(url=new_embed.thumbnail.url)
                    await canal_destino.send(embed=new_embed)
                    aviso = await channel.send(
                        f"✅ Ficha aprovada por {autor_reagiu} e arquivada",
                        delete_after=10
                    )
                await message.clear_reactions()
                await message.delete()

            elif emoji == "❌":
                try:
                    aviso = await channel.send(
                        f"{payload.member.mention} ❌ Digite o motivo da reprovação (60 segundos):",
                        delete_after=60
                    )

                    def check(m):
                        return m.author.id == payload.user_id and m.channel.id == payload.channel_id

                    msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                    motivo = msg.content

                    try:
                        await msg.delete()
                    except discord.Forbidden:
                        pass

                    new_embed = discord.Embed.from_dict(embed.to_dict())
                    new_embed.title = "❌ Ficha Reprovada"
                    new_embed.color = discord.Color.red()
                    new_embed.add_field(
                        name="❌ Motivo da Reprovação",
                        value=motivo,
                        inline=False
                    )
                    new_embed.set_author(
                        name=f"Reprovada por {autor_reagiu}",
                        icon_url=payload.member.display_avatar.url
                    )

                    canal_reprovado_id = await get_canal_por_tipo(guild.id, "Canal de Fichas Reprovadas")
                    if canal_reprovado_id:
                        canal_reprovado = guild.get_channel(canal_reprovado_id)
                        if canal_reprovado:
                            await canal_reprovado.send(embed=new_embed)
                            await channel.send(
                                f"📤 Ficha reprovada e arquivada",
                                delete_after=10
                            )
                    await message.clear_reactions()
                    await message.delete()
                    
                except asyncio.TimeoutError:
                    await channel.send("⏱️ Tempo esgotado para informar motivo", delete_after=10)
                except Exception as e:
                    print(f"Erro na reprovação: {e}")
                    await channel.send("⚠️ Ocorreu um erro ao processar a reprovação", delete_after=10)
        finally:
            if payload.message_id in self.processadas:
                self.processadas.remove(payload.message_id)

async def setup(bot: commands.Bot):
    await bot.add_cog(AprovacaoHandler(bot))