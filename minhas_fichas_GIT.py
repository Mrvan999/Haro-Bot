import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import sqlite3
from datetime import datetime

ID_SERVIDOR_TESTE = #Inserir id do Servidor de Teste
DB_PATH = "data/bot.db"

def buscar_fichas_do_usuario(guild_id: int, user_id: int):
    """Busca fichas do usuário na tabela fichas_concluidas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, nome, idade, altura, nacionalidade, 
            genero, meta_poder, raca, imagem_url, 
            data_criacao, status
        FROM fichas_concluidas
        WHERE guild_id = ? AND user_id = ? AND status = 'aprovada'
        ORDER BY data_avaliacao DESC
    """, (guild_id, user_id))
    
    fichas = cursor.fetchall()
    conn.close()
    
    fichas_formatadas = []
    for ficha in fichas:
        fichas_formatadas.append({
            "id": ficha[0],
            "nome": ficha[1],
            "idade": ficha[2],
            "altura": ficha[3],
            "nacionalidade": ficha[4],
            "genero": ficha[5],
            "meta_poder": ficha[6],
            "raca": ficha[7],
            "imagem_url": ficha[8],
            "data_criacao": ficha[9].split()[0] if ficha[9] else "Desconhecida",
            "status": ficha[10]
        })
    
    return fichas_formatadas

def criar_embed_ficha_completa(data, idx, total):
    """Cria embed com estrutura real das fichas"""
    embed = discord.Embed(
        title=f"Ficha de {data['nome']}",
        description=f"Ficha {idx+1} de {total} | Status: {data['status'].capitalize()}",
        color=discord.Color.green() if data['status'] == 'aprovada' else discord.Color.red()
    )
    
    # Informações básicas
    embed.add_field(name="👤 Nome", value=data['nome'], inline=True)
    embed.add_field(name="🎂 Idade", value=data['idade'], inline=True)
    embed.add_field(name="📏 Altura", value=data['altura'], inline=True)
    embed.add_field(name="🌎 Nacionalidade", value=data['nacionalidade'], inline=True)
    embed.add_field(name="⚧ Gênero", value=data['genero'], inline=True)
    embed.add_field(name="🧬 Raça", value=data['raca'], inline=True)
    embed.add_field(name="✨ Meta Poder", value=data['meta_poder'], inline=False)
    
    # Imagem e data
    if data['imagem_url'] and data['imagem_url'].startswith('http'):
        embed.set_thumbnail(url=data['imagem_url'])
    
    embed.set_footer(text=f"Criada em: {data['data_criacao']} | ID: {data['id']}")
    
    return embed

class NavegarFichasView(discord.ui.View):
    def __init__(self, interaction: Interaction, fichas):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.fichas = fichas
        self.index = 0
        self.message = None

    async def update_embed(self):
        embed = criar_embed_ficha_completa(self.fichas[self.index], self.index, len(self.fichas))
        if self.message:
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, button_interaction: Interaction, button: discord.ui.Button):
        if button_interaction.user.id != self.interaction.user.id:
            await button_interaction.response.send_message("❌ Você não pode usar este menu.", ephemeral=True)
            return
        self.index = (self.index - 1) % len(self.fichas)
        await self.update_embed()
        await button_interaction.response.defer()

    @discord.ui.button(label="➡️ Próxima", style=discord.ButtonStyle.secondary)
    async def proxima(self, button_interaction: Interaction, button: discord.ui.Button):
        if button_interaction.user.id != self.interaction.user.id:
            await button_interaction.response.send_message("❌ Você não pode usar este menu.", ephemeral=True)
            return
        self.index = (self.index + 1) % len(self.fichas)
        await self.update_embed()
        await button_interaction.response.defer()

    async def send_initial(self, original_interaction: Interaction):
        embed = criar_embed_ficha_completa(self.fichas[self.index], self.index, len(self.fichas))
        if original_interaction.response.is_done():
            self.message = await original_interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await original_interaction.response.send_message(embed=embed, view=self, ephemeral=True)
            self.message = await original_interaction.original_response()


class MinhasFichas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="minhas_fichas", description="Exibe suas fichas aprovadas")
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def minhas_fichas(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        fichas = buscar_fichas_do_usuario(interaction.guild.id, interaction.user.id)
        
        if not fichas:
            await interaction.followup.send("📭 Você ainda não tem fichas aprovadas.", ephemeral=True)
            return

        view = NavegarFichasView(interaction, fichas)
        await view.send_initial(interaction)

async def setup(bot: commands.Bot):
    if bot.get_cog("MinhasFichas") is None:
        await bot.add_cog(MinhasFichas(bot))