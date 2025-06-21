import discord
from discord.ext import commands
from discord import app_commands, Interaction, Object
import sqlite3
import asyncio

ID_SERVIDOR_TESTE = 
DB_PATH = "data/bot.db"

def listar_usuarios_com_fichas(guild_id: int):
    """Lista todos os usuários que têm fichas no sistema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Busca usuários com fichas concluídas
    cursor.execute("""
        SELECT 
            user_id, 
            COUNT(*) as total_fichas
        FROM fichas_concluidas 
        WHERE guild_id = ?
        GROUP BY user_id
        ORDER BY total_fichas DESC
    """, (guild_id,))
    
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios

def buscar_fichas_do_usuario(guild_id: int, user_id: int):
    """Busca todas as fichas de um usuário específico"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, nome, status, data_avaliacao
        FROM fichas_concluidas
        WHERE guild_id = ? AND user_id = ?
        ORDER BY data_avaliacao DESC
    """, (guild_id, user_id))
    
    fichas = cursor.fetchall()
    conn.close()
    
    fichas_formatadas = []
    for ficha in fichas:
        fichas_formatadas.append({
            "id": ficha[0],
            "nome": ficha[1],
            "status": ficha[2],
            "data": ficha[3]
        })
    
    return fichas_formatadas

def apagar_ficha(ficha_id: int):
    """Apaga uma ficha específica"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fichas_concluidas WHERE id = ?", (ficha_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def atualizar_status_ficha(ficha_id: int, novo_status: str):
    """Atualiza o status de uma ficha"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fichas_concluidas 
        SET status = ?
        WHERE id = ?
    """, (novo_status, ficha_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def transferir_ficha(ficha_id: int, novo_user_id: int):
    """Transfere uma ficha para outro usuário"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE fichas_concluidas 
        SET user_id = ?
        WHERE id = ?
    """, (novo_user_id, ficha_id))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def get_nome_usuario(guild, user_id: int):
    """Obtém o nome de um usuário pelo ID"""
    membro = guild.get_member(user_id)
    return membro.display_name if membro else f"ID: {user_id}"

class DataManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.acoes = {} 

    @app_commands.command(
        name="data",
        description="Ferramentas de gerenciamento de dados de fichas"
    )
    @app_commands.guilds(Object(id=ID_SERVIDOR_TESTE))
    async def data(self, interaction: Interaction):
        """Menu principal de gerenciamento de dados"""
        embed = discord.Embed(
            title="📊 Gerenciamento de Dados",
            description="Selecione uma opção:\n\n1. Fichas por Usuário",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.acoes[interaction.user.id] = {"estado": "menu_principal"}

    @commands.Cog.listener()
    async def on_message(self, message):
        """Processa respostas do usuário no fluxo de gerenciamento"""
        if message.author.bot or message.guild is None:
            return
        
        user_id = message.author.id
        estado = self.acoes.get(user_id, {}).get("estado")
        if not estado:
            return
        
        try:
            # Menu principal
            if estado == "menu_principal":
                if message.content.strip() == "1":
                    usuarios = listar_usuarios_com_fichas(message.guild.id)
                    
                    if not usuarios:
                        await message.channel.send("❌ Nenhum usuário com fichas encontrado.", delete_after=15)
                        del self.acoes[user_id]
                        return
                    lista = []
                    for idx, (user_id_db, total) in enumerate(usuarios, 1):
                        nome = get_nome_usuario(message.guild, user_id_db)
                        lista.append(f"{idx} - {user_id_db} ({nome}) [{total} fichas]")
                    
                    embed = discord.Embed(
                        title="👥 Usuários com Fichas",
                        description="\n".join(lista),
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed, delete_after=120)
                    await message.channel.send(
                        "Digite o número do usuário que deseja gerenciar:",
                        delete_after=60
                    )
                    self.acoes[user_id] = {
                        "estado": "selecionar_usuario",
                        "usuarios": usuarios
                    }
                else:
                    await message.channel.send("❌ Opção inválida. Tente novamente.", delete_after=15)
            elif estado == "selecionar_usuario":
                try:
                    idx = int(message.content.strip()) - 1
                    usuarios = self.acoes[user_id]["usuarios"]
                    
                    if idx < 0 or idx >= len(usuarios):
                        await message.channel.send("❌ Número inválido. Tente novamente.", delete_after=15)
                        return
                    
                    user_id_alvo, _ = usuarios[idx]
                    fichas = buscar_fichas_do_usuario(message.guild.id, user_id_alvo)
                    lista = []
                    for idx_ficha, ficha in enumerate(fichas, 1):
                        status_emoji = "✅" if ficha["status"] == "aprovada" else "❌"
                        lista.append(f"{idx_ficha}. {ficha['nome']} {status_emoji} (ID: {ficha['id']})")
                    
                    nome_usuario = get_nome_usuario(message.guild, user_id_alvo)
                    embed = discord.Embed(
                        title=f"📝 Fichas de {nome_usuario}",
                        description="\n".join(lista) or "Nenhuma ficha encontrada",
                        color=discord.Color.blue()
                    )
                    await message.channel.send(embed=embed, delete_after=120)
                    await message.channel.send(
                        "Selecione uma ação:\n\n"
                        "1. Apagar ficha\n"
                        "2. Alterar status\n"
                        "3. Transferir posse\n"
                        "Digite o número da ação:",
                        delete_after=60
                    )
                    
                    # Atualizar estado
                    self.acoes[user_id] = {
                        "estado": "selecionar_acao",
                        "user_id_alvo": user_id_alvo,
                        "fichas": fichas
                    }
                
                except ValueError:
                    await message.channel.send("❌ Digite um número válido.", delete_after=15)
            
            # Selecionar ação
            elif estado == "selecionar_acao":
                acao = message.content.strip()
                fichas = self.acoes[user_id]["fichas"]
                
                if acao not in ["1", "2", "3"]:
                    await message.channel.send("❌ Ação inválida. Tente novamente.", delete_after=15)
                    return
                
                await message.channel.send(
                    "Digite o número da ficha que deseja gerenciar:",
                    delete_after=60
                )
                self.acoes[user_id] = {
                    **self.acoes[user_id],
                    "estado": "selecionar_ficha",
                    "acao": acao
                }
            
            # Selecionar ficha
            elif estado == "selecionar_ficha":
                try:
                    idx = int(message.content.strip()) - 1
                    fichas = self.acoes[user_id]["fichas"]
                    acao = self.acoes[user_id]["acao"]
                    
                    if idx < 0 or idx >= len(fichas):
                        await message.channel.send("❌ Número inválido. Tente novamente.", delete_after=15)
                        return
                    
                    ficha_id = fichas[idx]["id"]
                    if acao == "1":  # Apagar ficha
                        sucesso = apagar_ficha(ficha_id)
                        if sucesso:
                            await message.channel.send(f"✅ Ficha ID {ficha_id} apagada com sucesso!", delete_after=15)
                        else:
                            await message.channel.send(f"❌ Falha ao apagar ficha ID {ficha_id}", delete_after=15)
                    
                    elif acao == "2":  # Alterar status
                        await message.channel.send(
                            "Selecione o novo status:\n\n1. Aprovada ✅\n2. Reprovada ❌\nDigite o número:",
                            delete_after=60
                        )
                        self.acoes[user_id] = {
                            **self.acoes[user_id],
                            "estado": "alterar_status",
                            "ficha_id": ficha_id
                        }
                        return
                    
                    elif acao == "3":  # Transferir posse
                        await message.channel.send(
                            "Digite o ID do novo usuário:",
                            delete_after=60
                        )
                        self.acoes[user_id] = {
                            **self.acoes[user_id],
                            "estado": "transferir_posse",
                            "ficha_id": ficha_id
                        }
                        return
                    del self.acoes[user_id]
                
                except ValueError:
                    await message.channel.send("❌ Digite um número válido.", delete_after=15)
            
            # Alterar status
            elif estado == "alterar_status":
                if message.content.strip() == "1":
                    novo_status = "aprovada"
                elif message.content.strip() == "2":
                    novo_status = "reprovada"
                else:
                    await message.channel.send("❌ Opção inválida. Tente novamente.", delete_after=15)
                    return
                
                ficha_id = self.acoes[user_id]["ficha_id"]
                sucesso = atualizar_status_ficha(ficha_id, novo_status)
                
                if sucesso:
                    await message.channel.send(
                        f"✅ Status da ficha ID {ficha_id} alterado para {novo_status}!",
                        delete_after=15
                    )
                else:
                    await message.channel.send(
                        f"❌ Falha ao atualizar status da ficha ID {ficha_id}",
                        delete_after=15
                    )
                
                del self.acoes[user_id]
            
            # Transferir posse
            elif estado == "transferir_posse":
                try:
                    novo_user_id = int(message.content.strip())
                    ficha_id = self.acoes[user_id]["ficha_id"]
                    sucesso = transferir_ficha(ficha_id, novo_user_id)
                    
                    if sucesso:
                        novo_nome = get_nome_usuario(message.guild, novo_user_id)
                        await message.channel.send(
                            f"✅ Ficha ID {ficha_id} transferida para {novo_nome} (ID: {novo_user_id})!",
                            delete_after=15
                        )
                    else:
                        await message.channel.send(
                            f"❌ Falha ao transferir ficha ID {ficha_id}",
                            delete_after=15
                        )
                    
                    del self.acoes[user_id]
                
                except ValueError:
                    await message.channel.send("❌ Digite um ID de usuário válido.", delete_after=15)
        
        except Exception as e:
            await message.channel.send(f"❌ Ocorreu um erro: {str(e)}", delete_after=15)
            if user_id in self.acoes:
                del self.acoes[user_id]

async def setup(bot: commands.Bot):
    await bot.add_cog(DataManager(bot))