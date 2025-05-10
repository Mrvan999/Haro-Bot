import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import sqlite3
# from datetime import datetime # datetime não parece ser usado diretamente neste arquivo, mas não prejudica.

ID_SERVIDOR_TESTE = 1038628552150614046 # Certifique-se que este é o ID correto do seu servidor de teste

DB_PATH = "data/bot.db" # Considere mover DB_PATH para um arquivo de configuração central ou passá-lo para o cog.

def buscar_fichas_do_usuario(guild_id: int, user_id: int):
    # ... (sua função) ...
    pass # Placeholder

def criar_embed_ficha_completa(data, idx, total):
    # ... (sua função) ...
    pass # Placeholder

class NavegarFichasView(discord.ui.View):
    def __init__(self, interaction: Interaction, fichas):
        super().__init__(timeout=180)
        self.interaction = interaction # Mantém a interação original
        self.fichas = fichas
        self.index = 0
        self.message = None # Para armazenar a mensagem da view

    async def update_embed(self):
        embed = criar_embed_ficha_completa(self.fichas[self.index], self.index, len(self.fichas))
        if self.message: # Garante que a mensagem existe
            await self.message.edit(embed=embed, view=self)

    # ... (botões anterior e proxima) ...
    @discord.ui.button(label="⬅️ Anterior", style=discord.ButtonStyle.secondary)
    async def anterior(self, button_interaction: Interaction, button: discord.ui.Button): # Renomeado para button_interaction
        if button_interaction.user.id != self.interaction.user.id:
            await button_interaction.response.send_message("❌ Você não pode usar este menu.", ephemeral=True)
            return
        self.index = (self.index - 1) % len(self.fichas)
        await self.update_embed()
        await button_interaction.response.defer() # Deferir a interação do botão

    @discord.ui.button(label="➡️ Próxima", style=discord.ButtonStyle.secondary)
    async def proxima(self, button_interaction: Interaction, button: discord.ui.Button): # Renomeado para button_interaction
        if button_interaction.user.id != self.interaction.user.id:
            await button_interaction.response.send_message("❌ Você não pode usar este menu.", ephemeral=True)
            return
        self.index = (self.index + 1) % len(self.fichas)
        await self.update_embed()
        await button_interaction.response.defer() # Deferir a interação do botão

    async def send_initial(self, original_interaction: Interaction): # Recebe a interação original do comando
        embed = criar_embed_ficha_completa(self.fichas[self.index], self.index, len(self.fichas))
        # Responde à interação original do comando
        if original_interaction.response.is_done():
            self.message = await original_interaction.followup.send(embed=embed, view=self, ephemeral=True)
        else:
            await original_interaction.response.send_message(embed=embed, view=self, ephemeral=True)
            self.message = await original_interaction.original_response()


class MinhasFichas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="minhas_fichas", description="Exibe o histórico das suas fichas.")
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE)) # ✅ ADICIONADO DECORADOR
    async def minhas_fichas(self, interaction: Interaction):
        fichas = buscar_fichas_do_usuario(interaction.guild.id, interaction.user.id)
        if not fichas:
            await interaction.response.send_message("📭 Você ainda não tem fichas avaliadas.", ephemeral=True)
            return

        view = NavegarFichasView(interaction, fichas) # Passa a interação original
        await view.send_initial(interaction) # Chama send_initial com a interação do comando

async def setup(bot: commands.Bot):
    # A função setup estava dentro da classe no arquivo que você me enviou, corrigido:
    if bot.get_cog("MinhasFichas") is None:
        await bot.add_cog(MinhasFichas(bot))