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
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x8B8B8B
    )
    embed.set_footer(text="Chogoun • Imperador das Montanhas 🏔️")
    return embed

def chogoun_music_embed(titulo, descricao, thumbnail_url):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x8B8B8B
    )
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Chogoun • Imperador das Montanhas 🏔️")
    return embed

def chogoun_ia_embed(titulo, descricao):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x8B8B8B
    )
    embed.set_footer(text="Resposta gerada por Chogoun, o imperador e divindade das montanhas 🏔️")
    return embed

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logou em {self.user}')
        await self.change_presence(
            activity=discord.Game(name="Deitado no alto de suas montanhas 🏔️")
        )

    async def on_error(self, event, *args, **kwargs):
        print(f"Erro no evento {event}")

    async def on_guild_join(self, guild):
        general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)

        if general and general.permissions_for(guild.me).send_messages:
            await general.send(embed=chogoun_embed(
                "Saudações, súditos do reino!",
                "Eu sou Chogoun, o imperador das montanhas 🏔️"
            ))

    async def on_message(self, message):
        if message.author == self.user:
            return

        # =========================
        # !QUESTION
        # =========================
        if message.content.startswith("!question"):
            if len(message.content.split()) == 1:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Faça uma pergunta após o comando."
                ))
                return

            question = message.content[len("!question"):].strip()
            if not question:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Faça uma pergunta após o comando."
                ))
                return

            try:
                response = group_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": personality},
                        {"role": "user", "content": question}
                    ],
                    max_tokens=800,
                    temperature=0.2
                )

                answer = None
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        answer = choice.message.content
                    elif 'text' in choice:
                        answer = choice['text']

                if not answer:
                    answer = 'O modelo respondeu, mas não foi possível extrair texto da resposta.'

            except Exception as e:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ FALHA AO CONSULTAR IA",
                    f"Erro ao gerar resposta: {e}"
                ))
                return

            embed = chogoun_ia_embed(
                titulo="🏔️ Pergunta ao Imperador",
                descricao=answer.strip()
            )
            await message.channel.send(embed=embed)
            return

        # =========================
        # TODO: Comandos de moderação e música permanecem como no seu código original...
        # =========================

        # =========================
        # !UNO START
        # =========================
        if message.content.startswith("!uno start"):
            if message.guild.id in uno_games:
                await message.channel.send(embed=chogoun_embed(
                    "Espera um momento... VOCÊ DESEJA JOGAR UNO??",
                    "Já existe um jogo em andamento neste servidor."
                ))
                return
            
            uno_games[message.guild.id] = {
                "players": [],
                "started": False,
                "turn_index": 0,
                "direction": 1,
                "deck": [],
                "discard_pile": [],
                "hands": {}
            }

            await message.channel.send(embed=chogoun_embed(
                "🏔️ Uno invocado pelo Imperador!",
                "Digite `!uno join` para participar. (Máx 10 jogadores)"
            ))
            return

        # =========================
        # !UNO JOIN
        # =========================
        if message.content.startswith("!uno join"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo foi iniciado humano...",
                    "Use `!uno start` para iniciar um novo jogo."
                ))
                return

            if len(game["players"]) >= 10:
                await message.channel.send(embed=chogoun_embed(
                    "O limite de jogadores foi atingido humano...",
                    "Apenas 10 jogadores podem participar do jogo."
                ))
                return
            
            if message.author.id in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você já está no jogo humano...",
                    f"{message.author.mention}, aguarde o início do jogo."
                ))
                return
            
            game["players"].append(message.author.id)
            await message.channel.send(embed=chogoun_embed(
                "Jogador adicionado!",
                f"{message.author.mention} se juntou ao jogo. {len(game['players'])} jogadores no total."
            ))
            return

        # =========================
        # !UNO DEAL (início do jogo)
        # =========================
        if message.content.startswith("!uno deal"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo iniciado...",
                    "Use `!uno start` para iniciar."
                ))
                return

            if len(game["players"]) < 2:
                await message.channel.send(embed=chogoun_embed(
                    "Não há jogadores suficientes...",
                    "Espere mais jogadores se juntarem com `!uno join`."
                ))
                return

            if game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "O jogo já começou...",
                    "Não pode distribuir cartas novamente."
                ))
                return

            game["deck"] = create_deck()
            game["discard_pile"] = []
            game["hands"] = {}

            for player_id in game["players"]:
                hand = [game["deck"].pop() for _ in range(7)]
                game["hands"][player_id] = hand
                user = await self.fetch_user(player_id)
                try:
                    await user.send(embed=chogoun_embed(
                        "Suas cartas foram distribuídas!",
                        f"Sua mão: {', '.join(hand)}"
                    ))
                except:
                    pass

            game["started"] = True
            first_card = game["deck"].pop()
            game["discard_pile"].append(first_card)

            await message.channel.send(embed=chogoun_embed(
                "Cartas distribuídas! O jogo começou!",
                f"O primeiro card da pilha: **{first_card}**"
            ))
            return

# =========================
# INICIALIZAÇÃO
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.voice_states = True

client = Client(intents=intents)

print("TOKEN carregado:", bool(TOKEN))
print("GROQ carregado:", bool(GROQ_API_KEY))

try:
    client.run(TOKEN)
except Exception as e:
    print("ERRO AO INICIAR O BOT:", e)