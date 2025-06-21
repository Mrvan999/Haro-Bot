import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import asyncio
import googletrans
from googletrans import Translator
import re

ID_SERVIDOR_TESTE =
MAX_HISTORICO = 20  
MAX_CARACTERES = 1500  


traduzidas_cache = set()

class Tradutor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        self.tupperbox_pattern = re.compile(r"^\*\*(.+?)\*\*")

    def processar_mensagem(self, message):
        """Processa mensagens normais e de webhook (Tupperbox)"""
        tupper_name = None
        content = message.content
        if message.webhook_id:
            match = self.tupperbox_pattern.match(content)
            if match:
                tupper_name = match.group(1)
                content = content.replace(f"**{tupper_name}**", "", 1).strip()
            else:
                tupper_name = message.author.name if message.author else "Personagem"
        
        author_name = tupper_name or message.author.display_name
        
        return {
            "author": author_name,
            "content": content,
            "id": message.id,
            "timestamp": message.created_at.strftime("%H:%M"),
            "is_tupper": tupper_name is not None
        }

    @app_commands.command(
        name="translate",
        description="Traduz mensagens recentes no canal"
    )
    @app_commands.describe(
        direcao="Direção da tradução",
        quantidade="Número de mensagens a traduzir (1-10)"
    )
    @app_commands.choices(direcao=[
        app_commands.Choice(name="Inglês para Português", value="en-pt"),
        app_commands.Choice(name="Português para Inglês", value="pt-en"),
        app_commands.Choice(name="Detectar para Português", value="auto-pt"),
        app_commands.Choice(name="Detectar para Inglês", value="auto-en")
    ])
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def translate(
        self,
        interaction: Interaction,
        direcao: app_commands.Choice[str],
        quantidade: int = 5
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if quantidade < 1 or quantidade > 10:
            await interaction.followup.send(
                "❌ Quantidade inválida! Use um valor entre 1 e 10.",
                ephemeral=True
            )
            return
        src, dest = direcao.value.split('-')
        messages_to_translate = []
        total_chars = 0
        
        async for message in interaction.channel.history(limit=MAX_HISTORICO):
            if message.id in traduzidas_cache or message.author == self.bot.user:
                continue
            msg_data = self.processar_mensagem(message)
            if not msg_data["content"] and not message.embeds:
                continue
            if len(msg_data["content"]) > 300:
                continue
            if total_chars + len(msg_data["content"]) > MAX_CARACTERES:
                break
            messages_to_translate.append(msg_data)
            total_chars += len(msg_data["content"])
            if len(messages_to_translate) >= quantidade:
                break
        
        if not messages_to_translate:
            await interaction.followup.send(
                "❌ Nenhuma mensagem recente para traduzir.",
                ephemeral=True
            )
            return
        texto_original = "\n\n".join(
            f"[{msg['timestamp']}] {msg['author']}: {msg['content']}" 
            for msg in reversed(messages_to_translate)
        )
        try:
            if src == "auto":
                traducao = self.translator.translate(texto_original, dest=dest)
            else:
                traducao = self.translator.translate(texto_original, src=src, dest=dest)
            
            texto_traduzido = traducao.text
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erro na tradução: {str(e)}",
                ephemeral=True
            )
            return
        traduzidas_cache.update(msg["id"] for msg in messages_to_translate)
        embed = discord.Embed(
            title=f"🌍 Tradução ({direcao.name})",
            description=texto_traduzido,
            color=discord.Color.blue()
        )
        
        idioma_original = traducao.src.upper() if src == "auto" else src.upper()
        embed.add_field(
            name="ℹ️ Detalhes",
            value=f"• Mensagens: {len(messages_to_translate)}\n"
                  f"• Idioma original: {idioma_original}\n"
                  f"• Idioma destino: {dest.upper()}",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tradutor(bot))