import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import os
from datetime import datetime

ID_SERVIDOR_TESTE =
DB_PATH = "data/bot.db"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class CriarFicha(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS fichas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    nome TEXT NOT NULL,
                    idade TEXT NOT NULL,
                    altura TEXT NOT NULL,
                    raca TEXT NOT NULL,
                    nacionalidade TEXT NOT NULL,
                    genero TEXT NOT NULL,
                    meta_poder TEXT NOT NULL,
                    imagem_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS fichas_pendentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message_id INTEGER,
                    nome TEXT NOT NULL,
                    idade TEXT NOT NULL,
                    altura TEXT NOT NULL,
                    raca TEXT NOT NULL,
                    nacionalidade TEXT NOT NULL,
                    genero TEXT NOT NULL,
                    meta_poder TEXT NOT NULL,
                    imagem_url TEXT,
                    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pendente'
                )
            ''')
            await db.commit()

    @app_commands.command(name="criar_ficha", description="Cria uma ficha de personagem completa")
    @app_commands.guilds(discord.Object(id=ID_SERVIDOR_TESTE))
    @app_commands.describe(
        nome="Nome completo do personagem",
        idade="Idade do personagem (ex: 25, jovem, etc)",
        altura="Altura do personagem (ex: 175cm, 1.75m, etc)",
        raca="Raça do personagem (ex: Humano, Elfo, etc)",
        nacionalidade="Nacionalidade do personagem",
        genero="Gênero do personagem (ex: Masculino, Feminino, etc)",
        meta_poder="Descrição do poder metahumano",
    )
    async def criar_ficha(
        self, 
        interaction: discord.Interaction,
        nome: str,
        idade: str,
        altura: str,
        raca: str,
        nacionalidade: str,
        genero: str,
        meta_poder: str,
        imagem: discord.Attachment = None
    ):
        try:
            canal_aprovacao_id = await self.get_canal_por_tipo(
                interaction.guild.id, 
                "Canal de Fichas Pendentes"
            )
            
            if not canal_aprovacao_id:
                await interaction.response.send_message(
                    "⚠️ Canal de aprovação não configurado! Contate um administrador para configurar com `/setarcanal`.",
                    ephemeral=True
                )
                return
                
            canal_aprovacao = interaction.guild.get_channel(canal_aprovacao_id)
            if not canal_aprovacao:
                await interaction.response.send_message(
                    "⚠️ Canal de aprovação não encontrado! Contate um administrador para reconfigurar com `/setarcanal`.",
                    ephemeral=True
                )
                return
            bot_member = interaction.guild.get_member(self.bot.user.id)
            if not bot_member:
                await interaction.response.send_message(
                    "⚠️ Erro ao verificar permissões do bot!",
                    ephemeral=True
                )
                return
            
            # ===== TRATAMENTO DA IMAGEM =====
            imagem_url = None
            if imagem is not None:
                if isinstance(imagem, discord.Attachment):
                    imagem_url = imagem.url
                elif isinstance(imagem, str) and imagem.startswith("http"):
                    imagem_url = imagem
                else:
                    await interaction.response.send_message(
                        "❌ URL inválida ou imagem não fornecida!",
                        ephemeral=True
                    )
                    return
            if not imagem.content_type.startswith('image/'):
                await interaction.response.send_message(
                    "❌ O arquivo deve ser uma imagem (JPEG, PNG, etc)!",
                    ephemeral=True
                )
                return

            perms = canal_aprovacao.permissions_for(bot_member)
            required_perms = {
                "view_channel": "Ver o canal",
                "send_messages": "Enviar mensagens",
                "embed_links": "Inserir links (embeds)",
                "add_reactions": "Adicionar reações",
                "read_message_history": "Ler histórico de mensagens"
            }
            
            missing_perms = [perm_name for perm, perm_name in required_perms.items() if not getattr(perms, perm)]
            
            if missing_perms:
                await interaction.response.send_message(
                    f"⚠️ O bot precisa das seguintes permissões no canal de aprovação:\n"
                    f"- {', '.join(missing_perms)}\n"
                    f"Corrija as permissões e tente novamente.",
                    ephemeral=True
                )
                return
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute('''
                    INSERT INTO fichas_pendentes (
                        guild_id, user_id, nome, idade, altura, 
                        raca, nacionalidade, genero, meta_poder, imagem_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction.guild.id,
                    interaction.user.id,
                    nome,
                    idade,
                    altura,
                    raca,
                    nacionalidade,
                    genero,
                    meta_poder,
                    imagem_url
                ))
                await db.commit()
                cursor = await db.execute("SELECT last_insert_rowid()")
                ficha_id = (await cursor.fetchone())[0]
            embed = discord.Embed(
                title="📄 FICHA DE PERSONAGEM - EM APROVAÇÃO",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            # Seção 1: Identificação Básica
            embed.add_field(name="👤 NOME COMPLETO", value=nome, inline=False)
            embed.add_field(name="🧬 RAÇA/ESPÉCIE", value=raca, inline=True)
            embed.add_field(name="⚧ GÊNERO", value=genero, inline=True)
            
            # Seção 2: Características Físicas
            embed.add_field(name="\u200b", value="**📏 CARACTERÍSTICAS FÍSICAS**", inline=False)
            embed.add_field(name="🎂 IDADE", value=idade, inline=True)
            embed.add_field(name="📏 ALTURA", value=altura, inline=True)
            embed.add_field(name="🌎 NACIONALIDADE", value=nacionalidade, inline=True)
            
            # Seção 3: Poderes e Habilidades
            embed.add_field(name="\u200b", value="**✨ PODERES E HABILIDADES**", inline=False)
            embed.add_field(name="🔮 METAPODER PRINCIPAL", value=meta_poder, inline=False)
            
            # Imagem como destaque principal
            if imagem_url:
                embed.set_image(url=imagem_url if imagem_url else "https://i.imgur.com/5X0Qh3a.png")
            else:
                embed.set_image(url="https://i.imgur.com/5X0Qh3a.png")
            
            # Rodapé com informações do autor
            embed.set_footer(
                text=f"Enviado por {interaction.user.display_name} • {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} | ID: {ficha_id}",
                icon_url=interaction.user.display_avatar.url
            )

            # Enviar mensagem no canal de aprovação
            try:
                msg = await canal_aprovacao.send(embed=embed)
                await msg.add_reaction("✅")
                await msg.add_reaction("❌")
            except discord.Forbidden:
                await interaction.followup.send(
                    "⚠️ Erro: Sem permissão para enviar no canal de aprovação!",
                    ephemeral=True
                )
                return
            except discord.HTTPException as e:
                await interaction.followup.send(
                    f"⚠️ Erro ao enviar ficha: {str(e)}",
                    ephemeral=True
                )
                return
            
            # Salvar o message_id no banco de dados
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE fichas_pendentes SET message_id = ? WHERE id = ?",
                    (msg.id, ficha_id)
                )
                await db.commit()

            await interaction.response.send_message(
                "✅ Ficha enviada para aprovação dos moderadores!",
                ephemeral=True
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(
                    f"❌ Erro ao criar ficha: {str(e)}",
                    ephemeral=True
                )
            except:
                await interaction.followup.send(
                    f"❌ Erro ao criar ficha: {str(e)}",
                    ephemeral=True
                )

    async def get_canal_por_tipo(self, guild_id: int, tipo: str) -> int | None:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT canal_id FROM canais_configurados WHERE guild_id = ? AND tipo = ?",
                (guild_id, tipo)
            )
            result = await cursor.fetchone()
            return result[0] if result else None

async def setup(bot: commands.Bot):
    await bot.add_cog(CriarFicha(bot))