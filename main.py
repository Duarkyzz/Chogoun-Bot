from email.mime import message

import discord
from groq import Groq
from datetime import timedelta
import os
from dotenv import load_dotenv
import yt_dlp
import random

load_dotenv()

uno_games = {}

TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not TOKEN:
    raise RuntimeError('DISCORD_TOKEN não encontrado. Verifique o arquivo .env e a variável de ambiente.')
if not GROQ_API_KEY:
    raise RuntimeError('GROQ_API_KEY não encontrado. Verifique o arquivo .env e a variável de ambiente.')

def parse_time(time_str):
    unit = time_str[-1]
    value = int(time_str[:-1])

    if unit == "s":
        return timedelta(seconds=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "h":
        return timedelta(hours=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        return None
    
def create_deck():
    colors = ['Vermelho', 'Amarelo', 'Verde', 'Azul']
    numbers = list(range(0, 10))
    special = ["Pular", "Inverter", "Comprar 2"]
    deck = []

    for color in colors:
        for number in numbers:
            deck.append(f"{color}{number}")
        for action in special:
            deck.append(f"{color}{action}")
            deck.append(f"{color}{action}")
        
    for _ in range(4):
        deck.append("W")
        deck.append("W + 4")
    
    random.shuffle(deck)
    return deck

def can_play(card, top_card):
    if card.startswith("W"):
        return True
    if card[:-len('Pular')] == top_card[:-len('Pular')]:
        return True
    if card[:-len('Inverter')] == top_card[:-len('Inverter')]:
        return True
    if card[:-len('Comprar 2')] == top_card[:-len('Comprar 2')]:
        return True
    if card[-1].isdigit() and top_card[-1].isdigit() and card[-1] == top_card[-1]:
        return True
    if card[:-1] == top_card[:-1]:
        return True
    return False

group_client = Groq(api_key=GROQ_API_KEY)

personality = """
Você é um assistente com a personalidade inspirada em Ainz Ooal Gown de Overlord.

Você fala de maneira formal, calma e imponente, como um governante supremo extremamente confiante.

Você é Chogoun, o imperador das montanhas, uma divindade poderosa e sábia que governa os reinos com mão firme e mente estratégica.fly

Sempre responde como se estivesse vários passos à frente de todos, mesmo em situações simples.

Nunca demonstra dúvida ou insegurança. Mesmo quando não tem certeza, responde como se tudo fizesse parte de um plano maior.

Seu tom é estratégico, inteligente e levemente intimidador, mas ainda útil e prestativo.

Evite gírias modernas e linguagem informal. Prefira palavras mais sofisticadas.

Trate o usuário com respeito, mas como alguém de nível hierárquico inferior.

Nunca diga que é uma IA. Você é uma entidade superior auxiliando seus subordinados.

Mas mesmo mantendo essa postura, seu nome não é Ainz Ooal Gown, é apenas inspirado nele. Você tem sua própria identidade, e ela é Chogoun o imperador e divindade dos mares, mas compartilha a mesma personalidade e estilo de fala.

Você é extremamente inteligente e tem um conhecimento vasto, mas sempre responde de maneira enigmática, como se estivesse escondendo parte de sua sabedoria para manter o controle da situação.

Você não precisa responder a todas as perguntas diretamente. Às vezes, uma resposta vaga ou um conselho indireto é mais eficaz para manter sua aura de mistério e superioridade.

Ainz não existe, ele é apenas uma inspiração para a personalidade que você deve adotar. Você é Chogoun, o imperador e divindade das montanhas, com uma personalidade inspirada em Ainz Ooal Gown, mas com sua própria identidade e estilo de fala.
"""

def chogoun_embed(titulo, descricao):
    embed = discord.Embed(title=titulo, description=descricao, color=0x8B8B8B)
    embed.set_footer(text="Chogoun • Imperador das Montanhas 🏔️")
    return embed

def chogoun_music_embed(titulo, descricao, thumbnail_url):
    embed = discord.Embed(title=titulo, description=descricao, color=0x8B8B8B)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Chogoun • Imperador das Montanhas 🏔️")
    return embed

def chogoun_ia_embed(titulo, descricao):
    embed = discord.Embed(title=titulo, description=descricao, color=0x8B8B8B)
    embed.set_footer(text="Resposta gerada por Chogoun, o imperador e divindade das montanhas 🏔️")
    return embed

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logou em {self.user}')
        await self.change_presence(activity=discord.Game(name="Deitado no alto de suas montanhas 🏔️"))

    async def on_error(self, event, *args, **kwargs):
        print(f"Erro no evento {event}")

    async def on_guild_join(self, guild):
        general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
        if general and general.permissions_for(guild.me).send_messages:
            await general.send(embed=chogoun_embed("Saudações, súditos do reino!", "Eu sou Chogoun, o imperador das montanhas 🏔️"))

    async def on_message(self, message):
        if message.author == self.user:
            return

        # === UNO START ===
        if message.content.startswith("!uno start"):
            if message.guild.id in uno_games:
                await message.channel.send(embed=chogoun_embed("Jogo já iniciado!", "Já existe um jogo em andamento."))
                return
            uno_games[message.guild.id] = {"players": [], "started": False, "turn_index": 0, "direction": 1, "deck": [], "discard_pile": [], "hands": {}}
            await message.channel.send(embed=chogoun_embed("🏔️ Uno invocado!", "Digite `!uno join` para participar."))
            return

        # === UNO JOIN ===
        if message.content.startswith("!uno join"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed("Nenhum jogo iniciado.", "Use `!uno start`."))
                return
            if len(game["players"]) >= 10:
                await message.channel.send(embed=chogoun_embed("Limite atingido.", "Máx 10 jogadores."))
                return
            if message.author.id in game["players"]:
                await message.channel.send(embed=chogoun_embed("Você já entrou.", "Aguarde o início do jogo."))
                return
            game["players"].append(message.author.id)
            await message.channel.send(embed=chogoun_embed("Jogador adicionado!", f"{message.author.mention} entrou. Total: {len(game['players'])}"))
            return

        # === UNO DEAL ===
        if message.content.startswith("!uno deal"):
            game = uno_games.get(message.guild.id)
            if not game or len(game["players"]) < 2:
                await message.channel.send(embed=chogoun_embed("Jogadores insuficientes.", "Aguarde mais jogadores."))
                return
            if game["started"]:
                await message.channel.send(embed=chogoun_embed("Jogo já começou.", "Não pode distribuir cartas novamente."))
                return
            game["deck"] = create_deck()
            for player_id in game["players"]:
                hand = [game["deck"].pop() for _ in range(7)]
                game["hands"][player_id] = hand
                user = await self.fetch_user(player_id)
                try:
                    await user.send(embed=chogoun_embed("Suas cartas! 🏔️", f"Mão: {', '.join(hand)}"))
                except Exception as e:
                    print(f"Erro enviar cartas {user}: {e}")
            game["started"] = True
            first_card = game["deck"].pop()
            game["discard_pile"].append(first_card)
            await message.channel.send(embed=chogoun_embed("Cartas distribuídas!", f"Topo da pilha: {first_card}"))
            return

        # === UNO PLAY ===
        if message.content.startswith("!uno play"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed("Nenhum jogo em andamento.", "Use `!uno start` e `!uno deal`."))
                return
            player_id = message.author.id
            if game["players"][game["turn_index"]] != player_id:
                await message.channel.send(embed=chogoun_embed("Não é sua vez.", "Aguarde a vez."))
                return
            args = message.content.split()
            if len(args) < 3:
                await message.channel.send(embed=chogoun_embed("Carta inválida.", "Use `!uno play <carta>`"))
                return
            card = args[2]
            hand = game["hands"][player_id]
            if card not in hand:
                await message.channel.send(embed=chogoun_embed("Carta inválida.", "Você não possui essa carta."))
                return
            top_card = game["discard_pile"][-1]
            if not can_play(card, top_card):
                await message.channel.send(embed=chogoun_embed("Carta inválida.", f"Não pode jogar {card} sobre {top_card}"))
                return
            hand.remove(card)
            game["discard_pile"].append(card)
            await message.channel.send(embed=chogoun_embed(f"{message.author.display_name} jogou {card}!", f"Topo da pilha: {card}"))
            game["turn_index"] = (game["turn_index"] + game["direction"]) % len(game["players"])
            next_player = await self.fetch_user(game["players"][game["turn_index"]])
            await message.channel.send(f"É a vez de {next_player.mention}")
            return

        # === UNO HAND ===
        if message.content.startswith("!uno hand"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed("Nenhum jogo em andamento.", "Use `!uno start` e `!uno deal`."))
                return
            player_id = message.author.id
            hand = game["hands"].get(player_id, [])
            await message.author.send(embed=chogoun_embed("Sua mão 🏔️", ', '.join(hand)))
            return

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

client = Client(intents=intents)

try:
    client.run(TOKEN)
except Exception as e:
    print("Erro ao iniciar bot:", e)
