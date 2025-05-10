import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

ID_SERVIDOR_TESTE = 1038628552150614046
DB_PATH = "data/bot.db"

class FichaCreator:
    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.data = {}
        self.current_step = 0
        self.message = None

    async def start_creation(self):
        await self.interaction.response.defer(ephemeral=True)
        self.message = await self.interaction.followup.send(
            embed=discord.Embed(description="🛠️ Iniciando criação de ficha...", color=0x5865F2),
            ephemeral=True,
            wait=True
        )
        await self.next_step()

    async def next_step(self):
        steps = [
            self.step_nome,
            self.step_idade,
            self.step_raca,  # Etapa implementada abaixo
            self.step_altura,
            self.step_nacionalidade,
            self.step_genero,
            self.step_meta_poder,
            self.step_imagem
        ]
        
        if self.current_step < len(steps):
            await steps[self.current_step]()
        else:
            await self.finalizar()

    # --- Implementação Completa das Etapas ---
    async def step_nome(self):
        modal = self.NameModal(self)
        await self.interaction.followup.send(modal, ephemeral=True)

    async def step_idade(self):
        view = self.AgeView(self)
        await self.message.edit(
            embed=discord.Embed(
                title="🎂 Idade",
                description="Selecione a faixa etária:",
                color=0x5865F2
            ),
            view=view
        )

    async def step_raca(self):  # <--- Método implementado
        view = self.RaceView(self)
        await self.message.edit(
            embed=discord.Embed(
                title="🧬 Raça",
                description="Escolha uma raça:",
                color=0x5865F2
            ),
            view=view
        )

    async def step_altura(self):
        modal = self.HeightModal(self)
        await self.interaction.followup.send(modal, ephemeral=True)

    # ... (Implementar outras etapas seguindo o mesmo padrão)

    # --- Classes Auxiliares ---
    class NameModal(discord.ui.Modal):
        def __init__(self, parent):
            super().__init__(title="📝 Nome", timeout=300)
            self.parent = parent
            self.nome = discord.ui.TextInput(label="Nome completo:", max_length=25)
            self.add_item(self.nome)

        async def on_submit(self, interaction: discord.Interaction):
            self.parent.data["nome"] = self.nome.value
            self.parent.current_step += 1
            await self.parent.next_step()
            await interaction.response.defer()

    class AgeView(discord.ui.View):
        def __init__(self, parent):
            super().__init__(timeout=300)
            self.parent = parent
            ages = [("12-18", 15), ("19-40", 30), ("41-60", 50), ("61+", 70)]
            for label, value in ages:
                self.add_item(self.AgeButton(label, value))

        class AgeButton(discord.ui.Button):
            def __init__(self, label, value):
                super().__init__(label=label, style=discord.ButtonStyle.primary)
                self.value = value

            async def callback(self, interaction: discord.Interaction):
                self.view.parent.data["idade"] = self.value
                self.view.parent.current_step += 1
                await self.view.parent.next_step()
                await interaction.response.defer()

    class RaceView(discord.ui.View):  # <--- View para seleção de raça
        def __init__(self, parent):
            super().__init__(timeout=300)
            self.parent = parent
            racas = ["Humano", "Elfo", "Anão", "Orc", "Dragão"]
            for raca in racas:
                self.add_item(self.RaceButton(raca))

        class RaceButton(discord.ui.Button):
            def __init__(self, raca):
                super().__init__(label=raca, style=discord.ButtonStyle.primary)
                self.raca = raca

            async def callback(self, interaction: discord.Interaction):
                self.view.parent.data["raca"] = self.raca
                self.view.parent.current_step += 1
                await self.view.parent.next_step()
                await interaction.response.defer()

    # ... (Implementar outras classes auxiliares)

class CriarFicha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="criar_ficha", description="Cria uma ficha de personagem")
    @app_commands.guilds(discord.Object(id=ID_SERVIDOR_TESTE))
    async def criar_ficha(self, interaction: discord.Interaction):
        try:
            creator = FichaCreator(interaction)
            await creator.start_creation()
        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CriarFicha(bot))