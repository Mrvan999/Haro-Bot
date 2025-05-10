from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Object
import discord
import sqlite3
import os

print(f"--- [Setarcanal.py] discord.__version__: {discord.__version__} ---")
print(f"--- [Setarcanal.py] app_commands: {app_commands} ---")
print(f"--- [Setarcanal.py] app_commands.command: {app_commands.command} ---")

ID_SERVIDOR_TESTE = 1038628552150614046 # Certifique-se que este é o ID correto do seu servidor de teste

# Lista de tipos válidos
TIPOS_DE_CANAL = [
    "Canal de Criação Fichas",
    "Canal de Aprovacao",
    "Canal de Fichas Aprovadas",
    "Canal de Fichas Reprovadas"
]

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bot.db")

def salvar_canal(guild_id, canal_id, tipo):
    """Salva ou atualiza um canal no banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO canais_configurados (guild_id, canal_id, tipo)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, tipo) DO UPDATE SET canal_id=excluded.canal_id
    ''', (guild_id, canal_id, tipo))
    conn.commit()
    conn.close()

class CanalConfigView(discord.ui.View):
    """View com o seletor de tipo de canal."""
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(CanalTipoSelect())

class CanalTipoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=tipo, description=f"Define como {tipo}") for tipo in TIPOS_DE_CANAL
        ]
        super().__init__(placeholder="Escolha o tipo de canal", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        tipo_escolhido = self.values[0]
        await interaction.response.send_modal(CanalEscolhaModal(tipo_escolhido))

class CanalEscolhaModal(discord.ui.Modal):
    """Modal para inserir o ID do canal."""
    def __init__(self, tipo_escolhido: str):
        super().__init__(title="Escolher Canal")
        self.tipo_escolhido = tipo_escolhido
        self.canal_id = discord.ui.TextInput(
            label="ID do Canal",
            placeholder="1234567890",
            style=discord.TextStyle.short
        )
        self.add_item(self.canal_id)

    async def on_submit(self, interaction: Interaction):
        try:
            canal_id_int = int(self.canal_id.value)
            canal = interaction.guild.get_channel(canal_id_int)

            if not canal or not isinstance(canal, TextChannel):
                raise ValueError("Canal inválido ou não encontrado.")

            # Salva o canal no banco
            salvar_canal(interaction.guild.id, canal.id, self.tipo_escolhido)

            await interaction.response.send_message(
                f"✅ Canal `{canal.name}` setado como **{self.tipo_escolhido}** com sucesso.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class SetarCanalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setarcanal",
        description="Define o canal para cada tipo de função.",
    )
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def setar_canal(self, interaction: Interaction):
        # ...
        view = CanalConfigView()
        await interaction.response.send_message("Selecione o tipo de canal:", view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    if bot.get_cog("SetarCanalCog") is None: # Boa prática
        await bot.add_cog(SetarCanalCog(bot))