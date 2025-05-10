import discord
print(f"--- ESTOU USANDO discord.py VERSÃO: {discord.__version__} ---")
print(f"--- CAMINHO PARA discord.py: {discord.__file__} ---")

import sqlite3
import discord
import os
import asyncio
from discord.ext import commands
from discord import app_commands

# 🔹 Configurações do Bot
TOKEN = "" # Substitua pelo seu token real
ID_SERVIDOR_TESTE = 
ID_SERVIDOR_OFICIAL =  # Se não estiver usando, pode comentar
CLIENT_ID =  
PREFIX = ";"
intents = discord.Intents.all()
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
        "commands.Setarcanal",
        "commands.criarficha",
        "eventos.aprovacao",
        "commands.log_ficha",
        "commands.minhas_fichas"
    ]
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Extensão '{extension}' carregada com sucesso.")
        # Capturar o CommandAlreadyRegistered de app_commands.errors
        except app_commands.errors.CommandAlreadyRegistered as e:
            print(f"AVISO ao carregar '{extension}': {e} - O comando de aplicativo já estava registrado.")
        # Capturar NoEntryPointError se uma extensão não tiver a função setup
        except commands.errors.NoEntryPointError as e:
            print(f"ERRO FATAL ao carregar '{extension}': {e} - A extensão não possui a função 'setup'.")
            # Considere levantar o erro aqui ou parar o bot, pois isso é um erro de programação.
            # raise
        # Capturar outros erros de carregamento de extensão
        except commands.errors.ExtensionError as e: # Erro mais genérico para problemas de extensão
            print(f"ERRO ao carregar extensão '{extension}': {e}")
            # raise
        # Capturar qualquer outra exceção inesperada
        except Exception as e:
            print(f"ERRO INESPERADO ao carregar extensão '{extension}': {type(e).__name__} - {e}")

async def startup_procedure():
    initialize_database() 
    await load_extensions()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user.name} (ID: {bot.user.id})")
    print(f"Latência: {round(bot.latency * 1000)}ms")
    print(f"Servidores conectados: {len(bot.guilds)}")

    # Sincronização de comandos de aplicativo (slash commands)
    try:
        print(f"Tentando sincronizar comandos para o servidor de teste (ID: {ID_SERVIDOR_TESTE})...") # Adicionado para clareza
        guild_obj_teste = discord.Object(id=ID_SERVIDOR_TESTE) # Use seu ID de servidor de teste
        
        # Opcional: Limpar comandos da guild antes de sincronizar para forçar uma atualização.
        # Use com cautela ou apenas durante o desenvolvimento intenso.
        # print(f"Limpando comandos para a guild de teste (ID: {ID_SERVIDOR_TESTE}) antes de sincronizar...")
        # bot.tree.clear_commands(guild=guild_obj_teste)
        # await bot.tree.sync(guild=guild_obj_teste) # Sincroniza o estado limpo
        # print("Comandos da guild de teste limpos.")

        # Sincroniza os comandos que estão na árvore local para esta guild
        synced_teste = await bot.tree.sync(guild=guild_obj_teste)
        print(f"Sincronizados {len(synced_teste)} comandos para o servidor de teste (ID: {ID_SERVIDOR_TESTE}).")

        if len(synced_teste) > 0:
            print(f"Comandos sincronizados no teste: {[cmd.name for cmd in synced_teste]}")
        else:
            # Se 0 comandos foram sincronizados, vamos verificar o que está na árvore local
            print("Nenhum comando novo foi sincronizado para a guild de teste. Verificando árvore local...")
            
            # Comandos registrados especificamente para esta guild
            local_commands_for_guild = [cmd.name for cmd in bot.tree.get_commands(guild=guild_obj_teste, type=discord.AppCommandType.chat_input)]
            print(f"Comandos locais na árvore PARA A GUILD DE TESTE (ID: {ID_SERVIDOR_TESTE}): {local_commands_for_guild}")
            
            # Comandos registrados como globais (sem guild_ids no decorador)
            local_global_commands = [cmd.name for cmd in bot.tree.get_commands(guild=None, type=discord.AppCommandType.chat_input)]
            print(f"Comandos locais GLOBAIS na árvore: {local_global_commands}")

            if not local_commands_for_guild and not local_global_commands:
                print("AVISO: NENHUM comando de aplicativo (slash command) encontrado na árvore local do bot.")
            elif not local_commands_for_guild and local_global_commands:
                print("INFO: Existem comandos globais na árvore, mas eles não foram especificamente sincronizados para esta guild ou já estão sincronizados globalmente.")
                print("      Para desenvolvimento rápido, considere adicionar 'guilds=[discord.Object(id=ID_SERVIDOR_TESTE)]' aos seus decoradores @app_commands.command.")

    except Exception as e:
        print(f"Erro CRÍTICO ao sincronizar comandos em on_ready: {e}")
        import traceback
        traceback.print_exc() # Imprime o traceback completo para ajudar a depurar erros de sincronização

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