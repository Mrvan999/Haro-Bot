import sqlite3
import discord
import os
import asyncio
from discord import app_commands
from discord.ext import commands
# Removi imports não utilizados aqui, mas mantenha os que você precisa
# from datetime import datetime, timezone, timedelta
# from discord.ext import tasks


# 🔹 Configurações do Bot
TOKEN = "SEU_TOKEN_AQUI" # Substitua pelo seu token real
ID_SERVIDOR_TESTE = 1038628552150614046
# ID_SERVIDOR_OFICIAL = 1107444557873942581 # Se não estiver usando, pode comentar
# CLIENT_ID = 1339387984138469477 # Geralmente não é necessário para o código do bot
PREFIX = ";"
intents = discord.Intents.all() # Use intents específicas se possível para melhor performance/segurança
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# --- DEFINIÇÕES DO BANCO DE DADOS MOVIDAS PARA CIMA ---
db_path = os.path.join(os.path.dirname(__file__), "data", "bot.db")

def initialize_database():
    # Cria o diretório 'data' se não existir
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canais_configurados (
            guild_id INTEGER NOT NULL,
            canal_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            PRIMARY KEY (guild_id, tipo)
        )
    ''')
    # Adicione outras tabelas que seus cogs usam aqui, como fichas_pendentes, fichas_concluidas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fichas_pendentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message_id INTEGER,
            nome TEXT,
            idade TEXT,
            altura TEXT,
            nacionalidade TEXT,
            genero TEXT,
            meta_poder TEXT,
            raca TEXT,
            imagem_url TEXT,
            data_envio TEXT, /* ISOFORMAT string */
            status TEXT DEFAULT 'pendente' /* pendente, aprovada, reprovada */
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fichas_concluidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            nome TEXT,
            idade TEXT,
            altura TEXT,
            nacionalidade TEXT,
            genero TEXT,
            meta_poder TEXT,
            raca TEXT,
            imagem_url TEXT,
            data_criacao TEXT, /* ISOFORMAT string da ficha original */
            data_avaliacao TEXT, /* ISOFORMAT string */
            status TEXT, /* aprovada, reprovada */
            motivo TEXT,
            avaliador_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print("Banco de dados inicializado/verificado.")

# Função para setar um canal de um determinado tipo (exemplo, se você ainda precisar dela em HaroDS.py)
# Geralmente, essa lógica estaria mais ligada ao comando /setarcanal
def setar_canal_teste(guild_id: int, canal_id: int, tipo: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO canais_configurados (guild_id, canal_id, tipo)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id, tipo)
        DO UPDATE SET canal_id=excluded.canal_id
    ''', (guild_id, canal_id, tipo))
    conn.commit()
    conn.close()
    print(f"Canal de teste setado: {guild_id}, {canal_id}, {tipo}")

# --- FIM DAS DEFINIÇÕES DO BANCO DE DADOS ---

async def load_extensions():
    extensions = [
        "commands.Setarcanal", # Certifique-se que o nome do arquivo é Setarcanal.py
        "commands.criarficha",
        "eventos.aprovacao",   # Ou commands.aprovacao se estiver na pasta commands
        "commands.log_ficha",
        "commands.minhas_fichas"
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Extensão '{extension}' carregada com sucesso.")
        except commands.errors.CommandAlreadyRegistered as e:
            print(f"AVISO ao carregar '{extension}': {e} - O comando já estava registrado. Isso pode ser normal se você deu reload.")
        except Exception as e:
            print(f"ERRO ao carregar extensão '{extension}': {e}")
            # Você pode querer re-levantar o erro para parar o bot se uma extensão crítica falhar
            # raise

async def startup_procedure():
    initialize_database() # Agora initialize_database() está definida
    # Removi a chamada setar_canal_teste daqui, pois a configuração de canais deve ser feita via comando.
    # Se você precisar de dados de teste, pode adicionar uma função separada para isso.
    # setar_canal_teste(guild_id=123456789, canal_id=987654321, tipo="Canal de Aprovacao") # Exemplo de dados de teste
    
    await load_extensions()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name} (ID: {bot.user.id})")
    print(f"Latência: {round(bot.latency * 1000)}ms")
    print(f"Servidores conectados: {len(bot.guilds)}")

    # Sincronização de comandos de aplicativo (slash commands)
    try:
        # Sincronizar globalmente (pode levar até 1 hora para atualizar em todos os servidores)
        # synced_global = await bot.tree.sync()
        # print(f"Sincronizados {len(synced_global)} comandos globais.")
        
        # É mais rápido sincronizar para guilds específicas durante o desenvolvimento
        guild_obj = discord.Object(id=ID_SERVIDOR_TESTE) # Use seu ID de servidor de teste
        synced_guild = await bot.tree.sync(guild=guild_obj)
        print(f"Sincronizados {len(synced_guild)} comandos para o servidor de teste (ID: {ID_SERVIDOR_TESTE}).")

        # Se você tiver um servidor oficial e quiser sincronizar para ele também:
        # guild_oficial_obj = discord.Object(id=ID_SERVIDOR_OFICIAL)
        # synced_oficial = await bot.tree.sync(guild=guild_oficial_obj)
        # print(f"Sincronizados {len(synced_oficial)} comandos para o servidor oficial (ID: {ID_SERVIDOR_OFICIAL}).")

    except Exception as e:
        print(f"Erro ao sincronizar comandos em on_ready: {e}")

# Comandos de prefixo para sincronização manual (opcional, mas útil)
@bot.command(name="sync", hidden=True)
@commands.is_owner()
async def sync_prefix_cmd(ctx: commands.Context, guild_id: int = None):
    if guild_id:
        guild = discord.Object(id=guild_id)
        await bot.tree.sync(guild=guild)
        await ctx.send(f"Comandos sincronizados para a guild {guild_id}.")
    else:
        await bot.tree.sync()
        await ctx.send("Comandos globais sincronizados.")
    print("Comandos sincronizados via comando de prefixo.")

async def main_async():
    async with bot: # Garante o setup/teardown correto do bot
        await startup_procedure() # Carrega DB, extensões, etc.
        await bot.start(TOKEN)

if __name__ == "__main__":
    # Verificar e criar o diretório data se não existir (redundante se initialize_database já faz)
    # data_dir = os.path.join(os.path.dirname(__file__), "data")
    # os.makedirs(data_dir, exist_ok=True)
    
    asyncio.run(main_async())