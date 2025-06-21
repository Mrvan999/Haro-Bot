
import asyncio
import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import sqlite3
from datetime import datetime, timedelta

ID_SERVIDOR_TESTE =

DB_PATH = "data/bot.db"

def buscar_fichas_expiradas(guild_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    limite_tempo = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

    cursor.execute("""
        SELECT id, nome, data_envio FROM fichas_pendentes
        WHERE status = 'pendente' AND data_envio < ? AND guild_id = ?
        ORDER BY data_envio ASC
    """, (limite_tempo, guild_id))
    
    fichas = cursor.fetchall()
    conn.close()
    return fichas

def get_ficha_completa(ficha_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fichas_pendentes WHERE id = ?", (ficha_id,))
    data = cursor.fetchone()
    conn.close()
    return data

def gerar_embed_ficha(ficha) -> discord.Embed:
    _, _, _, _, nome, idade, altura, nacionalidade, genero, meta_poder, raca, imagem_url, data_envio, _ = ficha[0:14]

    embed = discord.Embed(
        title="📄 Ficha Recuperada",
        color=discord.Color.yellow(),
        timestamp=datetime.fromisoformat(data_envio)
    )
    embed.set_thumbnail(url=imagem_url)
    embed.add_field(name="👤 Nome", value=nome, inline=True)
    embed.add_field(name="🎂 Idade", value=idade, inline=True)
    embed.add_field(name="📏 Altura", value=altura, inline=True)
    embed.add_field(name="🌎 Nacionalidade", value=nacionalidade, inline=True)
    embed.add_field(name="⚧ Gênero", value=genero, inline=True)
    embed.add_field(name="🎯 Meta/Poder", value=meta_poder, inline=True)
    embed.add_field(name="🧬 Raça", value=raca, inline=True)
    embed.set_footer(text=f"Original: {data_envio}")
    return embed

class LogFicha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="log_ficha", description="Recupera fichas pendentes de aprovação.")
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def log_ficha(self, interaction: Interaction):
        fichas = buscar_fichas_expiradas(interaction.guild.id)

        if not fichas:
            await interaction.response.send_message("✅ Nenhuma ficha pendente há mais de 30 minutos.", ephemeral=True)
            return

        lista = "\n".join([f"{idx+1}. {f[1]} (enviada em {f[2][:16].replace('T',' ')})" for idx, f in enumerate(fichas)])
        await interaction.response.send_message(
            f"📝 Fichas pendentes encontradas:\n```{lista}```\nDigite o número da ficha que deseja recuperar:",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60.0)
            idx = int(msg.content.strip()) - 1
            if idx < 0 or idx >= len(fichas):
                raise ValueError("Número inválido.")

            ficha_id = fichas[idx][0]
            ficha_completa = get_ficha_completa(ficha_id)
            if ficha_completa:
                embed = gerar_embed_ficha(ficha_completa)
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ Ficha com ID {ficha_id} não encontrada.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Tempo esgotado para escolher a ficha.", ephemeral=True)
        except ValueError:
             await interaction.followup.send("❌ Número da ficha inválido.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao recuperar ficha: {e}", ephemeral=True)


async def setup(bot: commands.Bot):
    if bot.get_cog("LogFicha") is None:
        await bot.add_cog(LogFicha(bot))