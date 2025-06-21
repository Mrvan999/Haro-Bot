from discord.ext import commands
from discord import app_commands, Interaction, TextChannel, Object
import discord
import sqlite3
import os

print(f"--- [Setarcanal.py] discord.__version__: {discord.__version__} ---")

ID_SERVIDOR_TESTE =

TIPOS_DE_CANAL = [
    "Canal de Fichas Pendentes",
    "Canal de Fichas Aprovadas",
    "Canal de Fichas Reprovadas"
]

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bot.db")

def salvar_canal(guild_id, canal_id, tipo):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO canais_configurados (guild_id, canal_id, tipo)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, tipo) DO UPDATE SET canal_id=excluded.canal_id
    ''', (guild_id, canal_id, tipo))
    conn.commit()
    conn.close()
    return True

class CanalConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=180)
        self.bot = bot
        self.add_item(CanalTipoSelect(bot))

class CanalTipoSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label=tipo, description=f"Define como {tipo}") 
            for tipo in TIPOS_DE_CANAL
        ]
        super().__init__(
            placeholder="Escolha o tipo de canal",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: Interaction):
        tipo_escolhido = self.values[0]
        await interaction.response.send_modal(
            CanalEscolhaModal(tipo_escolhido, self.bot)
        )

class CanalEscolhaModal(discord.ui.Modal):
    def __init__(self, tipo_escolhido: str, bot):
        super().__init__(title="Escolher Canal")
        self.tipo_escolhido = tipo_escolhido
        self.bot = bot
        self.canal_id = discord.ui.TextInput(
            label="ID do Canal",
            placeholder="1234567890",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.canal_id)

    async def on_submit(self, interaction: Interaction):
        try:
            canal_id_int = int(self.canal_id.value)
            canal = interaction.guild.get_channel(canal_id_int)
            
            if not canal:
                raise ValueError("❌ Canal não encontrado neste servidor")
                
            if not isinstance(canal, discord.TextChannel):
                raise ValueError("❌ O canal deve ser um canal de texto")
            perms = canal.permissions_for(interaction.guild.me)
            required_perms = ["view_channel", "send_messages", "read_message_history"]
            
            missing_perms = [perm for perm in required_perms if not getattr(perms, perm)]
            
            if missing_perms:
                raise ValueError(
                    f"❌ O bot precisa das permissões: {', '.join(missing_perms)}"
                )
            salvar_canal(interaction.guild.id, canal.id, self.tipo_escolhido)
            
            await interaction.response.send_message(
                f"✅ Canal {canal.mention} configurado como **{self.tipo_escolhido}**",
                ephemeral=True
            )
            
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Erro inesperado: {str(e)}",
                ephemeral=True
            )

class SetarCanalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="setarcanal",
        description="Define o canal para cada tipo de função.",
    )
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def setar_canal(self, interaction: Interaction):
        view = CanalConfigView(self.bot)
        await interaction.response.send_message(
            "Selecione o tipo de canal que deseja configurar:",
            view=view,
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(SetarCanalCog(bot))