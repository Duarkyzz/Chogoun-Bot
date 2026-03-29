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


# =========================
# UNO HELPERS
# =========================
def create_deck():
    colors = ['Vermelho', 'Amarelo', 'Verde', 'Azul']
    deck = []

    for color in colors:
        deck.append(f"{color}0")
        for number in range(1, 10):
            deck.append(f"{color}{number}")
            deck.append(f"{color}{number}")

        for action in ["Pular", "Inverter", "Comprar 2"]:
            deck.append(f"{color}{action}")
            deck.append(f"{color}{action}")

    for _ in range(4):
        deck.append("W")
        deck.append("W + 4")

    random.shuffle(deck)
    return deck


def get_card_color(card):
    colors = ['Vermelho', 'Amarelo', 'Verde', 'Azul']
    for color in colors:
        if card.startswith(color):
            return color
    return None


def get_card_value(card):
    color = get_card_color(card)
    if color:
        return card[len(color):]
    return card


def can_play(card, top_card, current_color):
    if card in ["W", "W + 4"]:
        return True

    card_color = get_card_color(card)
    card_value = get_card_value(card)
    top_color = current_color if current_color else get_card_color(top_card)
    top_value = get_card_value(top_card)

    return card_color == top_color or card_value == top_value


def reshuffle_if_needed(game):
    if len(game["deck"]) == 0 and len(game["discard_pile"]) > 1:
        top = game["discard_pile"].pop()
        game["deck"] = game["discard_pile"][:]
        random.shuffle(game["deck"])
        game["discard_pile"] = [top]


def draw_cards(game, player_id, amount):
    drawn = []
    for _ in range(amount):
        reshuffle_if_needed(game)
        if len(game["deck"]) == 0:
            break
        card = game["deck"].pop()
        game["hands"][player_id].append(card)
        drawn.append(card)
    return drawn


def advance_turn(game, steps=1):
    total_players = len(game["players"])
    if total_players == 0:
        return
    game["turn_index"] = (game["turn_index"] + (steps * game["direction"])) % total_players


def get_current_player_id(game):
    return game["players"][game["turn_index"]]


def format_hand(hand):
    return ", ".join(hand) if hand else "Sem cartas."


def normalize_turn_index(game):
    if len(game["players"]) == 0:
        game["turn_index"] = 0
    else:
        game["turn_index"] %= len(game["players"])


async def send_hand(client, player_id, game):
    user = await client.fetch_user(player_id)
    try:
        await user.send(embed=chogoun_embed(
            "Sua mão atual no Uno do Imperador 🏔️",
            f"Suas cartas: {format_hand(game['hands'][player_id])}"
        ))
    except Exception as e:
        print(f"ERRO AO ENVIAR MÃO PARA {user}: {e}")


async def send_all_hands(client, game):
    for player_id in game["players"]:
        await send_hand(client, player_id, game)


async def check_uno_penalty(client, channel, game, player_id):
    """
    Se o jogador ficou com 1 carta e não declarou UNO,
    ele pode ser punido via !uno catch
    """
    if player_id in game["hands"] and len(game["hands"][player_id]) == 1:
        game["uno_pending"][player_id] = True
        game["uno_declared"][player_id] = False
    else:
        game["uno_pending"][player_id] = False
        game["uno_declared"][player_id] = False


async def maybe_end_game_due_to_player_count(client, channel, guild_id):
    game = uno_games.get(guild_id)
    if not game:
        return True

    if len(game["players"]) == 1:
        winner_id = game["players"][0]
        winner = await client.fetch_user(winner_id)
        await channel.send(embed=chogoun_embed(
            "🏔️ VITÓRIA POR SOBREVIVÊNCIA 🏔️",
            f"{winner.mention} venceu o jogo de Uno do Imperador das Montanhas!"
        ))
        del uno_games[guild_id]
        return True

    if len(game["players"]) == 0:
        del uno_games[guild_id]
        await channel.send(embed=chogoun_embed(
            "Partida encerrada...",
            "Todos abandonaram o campo de batalha."
        ))
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
        # !BAN
        # =========================
        if message.content.startswith("!ban"):
            if not message.author.guild_permissions.ban_members:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            if len(message.mentions) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo..",
                    "Indique um alvo para banir, ou será considerado um ato de insubordinação."
                ))
                return

            member = message.mentions[0]

            await member.ban(reason="Banido pelo imperador Chogoun, por desrespeito ou comportamento inadequado.")
            await message.channel.send(embed=chogoun_embed(
                "DESTINO SELADO HUMANO",
                f"{member.mention} foi banido por ordem do imperador Chogoun."
            ))
            return

        # =========================
        # !KICK
        # =========================
        if message.content.startswith("!kick"):
            if not message.author.guild_permissions.kick_members:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            if len(message.mentions) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo..",
                    "Indique um alvo para expulsar, ou será considerado um ato de insubordinação."
                ))
                return

            member = message.mentions[0]

            await member.kick(reason="Expulso por ordem do imperador Chogoun, por desrespeito ou comportamento inadequado.")
            await message.channel.send(embed=chogoun_embed(
                "DESTINO SELADO HUMANO",
                f"{member.mention} foi expulso por ordem do imperador Chogoun."
            ))
            return

        # =========================
        # !MUTE
        # =========================
        if message.content.startswith("!mute"):
            if not message.author.guild_permissions.mute_members:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            args = message.content.split()

            if len(message.mentions) == 0 or len(args) < 3:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo..",
                    "Indique um alvo e um tempo para silenciar. Exemplo: !mute @usuário 10m"
                ))
                return

            member = message.mentions[0]
            time_str = args[2]
            duration = parse_time(time_str)

            if duration is None:
                await message.channel.send(embed=chogoun_embed(
                    "Imprestável humano..",
                    "Tempo inválido. Use um número seguido de uma letra. Exemplo: !mute @usuário 10m"
                ))
                return

            await member.timeout(duration, reason="Silenciado por ordem do imperador Chogoun.")
            await message.channel.send(embed=chogoun_embed(
                "CALADO!! SUA VOZ ME IRRITA HUMANO",
                f"{member.mention} foi silenciado por {time_str} por ordem do imperador Chogoun."
            ))
            return

        # =========================
        # !UNMUTE
        # =========================
        if message.content.startswith("!unmute"):
            if not message.author.guild_permissions.mute_members:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            if len(message.mentions) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "Imprestável humano..",
                    "Indique um alvo para remover o silêncio."
                ))
                return

            member = message.mentions[0]

            await member.timeout(None, reason="Silenciamento removido por ordem do imperador Chogoun.")
            await message.channel.send(embed=chogoun_embed(
                "PODE FALAR AGORA, MAS CUIDADO COM O QUE VAI DIZER HUMANO",
                f"O silêncio de {member.mention} foi removido por ordem do imperador Chogoun."
            ))
            return

        # =========================
        # !PLAY
        # =========================
        if message.content.startswith("!play"):
            print("Comando !play recebido:", message.content)

            args = message.content.split()

            if len(args) < 2:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Indique uma URL ou termo de pesquisa para reproduzir."
                ))
                return

            query = " ".join(args[1:])

            if message.author.voice is None or message.author.voice.channel is None:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você precisa estar em um canal de voz para usar este comando."
                ))
                return

            channel = message.author.voice.channel

            try:
                if message.guild.voice_client is None:
                    voice_client = await channel.connect()
                    print("Bot conectado ao canal de voz.")
                else:
                    voice_client = message.guild.voice_client
                    if voice_client.channel != channel:
                        await voice_client.move_to(channel)
                        print("Bot movido para outro canal.")
            except Exception as e:
                print("ERRO AO CONECTAR NA CALL:", e)
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ FALHA AO ENTRAR NA CALL",
                    f"Não consegui entrar no canal de voz.\n```{e}```"
                ))
                return

            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': False,
                'default_search': 'ytsearch',
                'no_warnings': False,
                'extract_flat': False,
            }

            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(query, download=False)

                    if 'entries' in info:
                        info = info['entries'][0]

                    audio_url = info['url']
                    title = info.get('title', 'Título desconhecido')
                    thumbnail = info.get('thumbnail') or "https://i.imgur.com/8Km9tLL.png"

                print("Áudio encontrado:", title)
                print("URL do áudio:", audio_url)

                source = await discord.FFmpegOpusAudio.from_probe(
                    audio_url,
                    **ffmpeg_options
                )

                if message.guild.voice_client.is_playing() or message.guild.voice_client.is_paused():
                    message.guild.voice_client.stop()

                def after_play(error):
                    if error:
                        print("ERRO NO PLAYER:", error)

                message.guild.voice_client.play(source, after=after_play)

                await message.channel.send(embed=chogoun_music_embed(
                    "🎶 Reproduzindo por ordem do Imperador das Montanhas 🏔️",
                    f"**{title}** ecoa pelas montanhas...",
                    thumbnail
                ))

            except Exception as e:
                print("ERRO NO !PLAY:", e)
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ FALHA NA REPRODUÇÃO",
                    f"Não foi possível reproduzir o áudio.\n```{e}```"
                ))
            return

        # =========================
        # !STOP
        # =========================
        if message.content.startswith("!stop"):
            voice_client = message.guild.voice_client

            if voice_client is None:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "O bot não está conectado a nenhum canal de voz."
                ))
                return

            await voice_client.disconnect()
            await message.channel.send(embed=chogoun_embed(
                "⚠️ ATENÇÃO HUMANO",
                "Desconectado do canal de voz."
            ))
            return

        # =========================
        # !PAUSE
        # =========================
        if message.content.startswith("!pause"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_playing():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve estar reproduzindo algo para pausar a reprodução."
                ))
                return

            voice_client.pause()
            await message.channel.send(embed=chogoun_embed(
                "Sua ordem será realizada, mero humano.🏔️",
                "Reprodução pausada."
            ))
            return

        # =========================
        # !RESUME
        # =========================
        if message.content.startswith("!resume"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_paused():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve ter algo pausado para retomar a reprodução."
                ))
                return

            voice_client.resume()
            await message.channel.send(embed=chogoun_embed(
                "Os ventos sopram a seu favor, humano.🏔️",
                "Reprodução retomada."
            ))
            return

        # =========================
        # !SKIP
        # =========================
        if message.content.startswith("!skip"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_playing():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve estar reproduzindo algo para pular a música atual."
                ))
                return

            voice_client.stop()
            await message.channel.send(embed=chogoun_embed(
                "Eu também considerei essa música digna de ser pulada, humano.",
                "Música pulada."
            ))
            return

        # =========================
        # !HELP
        # =========================
        if message.content.startswith("!help"):
            embed = chogoun_embed(
                "📜 Comandos do Imperador dos Mares",
                "Eis as ordens permitidas."
            )

            embed.add_field(
                name="⚔️ Moderação",
                value="`!ban @usuário`\n`!kick @usuário`\n`!mute @usuário 10m`\n`!unmute @usuário`",
                inline=False
            )

            embed.add_field(
                name="🎵 Música",
                value="`!play [URL ou termo de pesquisa]`\n`!stop`\n`!pause`\n`!resume`\n`!skip`",
                inline=False
            )

            embed.add_field(
                name="🧠 Inteligência",
                value="`!question [sua pergunta]`",
                inline=False
            )

            embed.add_field(
                name="👑 Administração de Cargos",
                value="`!addrole @usuário Cargo`\n`!removerole @usuário Cargo`",
                inline=False
            )

            embed.add_field(
                name="🎮 Uno",
                value=(
                    "`!uno start`\n"
                    "`!uno join`\n"
                    "`!uno deal`\n"
                    "`!uno hand`\n"
                    "`!uno status`\n"
                    "`!uno draw`\n"
                    "`!uno play [Carta]`\n"
                    "`!uno uno`\n"
                    "`!uno catch @usuário`\n"
                    "`!uno leave`\n"
                    "`!uno end`"
                ),
                inline=False
            )

            await message.channel.send(embed=embed)
            return

        # =========================
        # !ADDROLE
        # =========================
        if message.content.startswith("!addrole"):
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            args = message.content.split()

            if len(message.mentions) == 0 or len(args) < 3:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo..",
                    "Indique um alvo e o nome do cargo a ser adicionado.\nExemplo: `!addrole @usuário Cargo`"
                ))
                return

            member = message.mentions[0]
            role_name = " ".join(args[2:])
            role = discord.utils.get(message.guild.roles, name=role_name)

            if role is None:
                await message.channel.send(embed=chogoun_embed(
                    "Imprestável humano..",
                    f"O cargo **{role_name}** não existe."
                ))
                return

            if role in member.roles:
                await message.channel.send(embed=chogoun_embed(
                    "Inútil tentativa...",
                    f"{member.mention} já possui o cargo **{role.name}**."
                ))
                return

            if role >= message.guild.me.top_role:
                await message.channel.send(embed=chogoun_embed(
                    "Poder insuficiente...",
                    f"Não posso gerenciar o cargo **{role.name}** pois ele está acima de mim."
                ))
                return

            try:
                await member.add_roles(role, reason="Cargo adicionado por ordem do imperador Chogoun.")
                await message.channel.send(embed=chogoun_embed(
                    "Cargo concedido por ordem do Imperador das Montanhas 🏔️",
                    f"O cargo **{role.name}** foi adicionado a {member.mention}."
                ))
            except Exception as e:
                await message.channel.send(embed=chogoun_embed(
                    "Falha imperial...",
                    f"Não foi possível adicionar o cargo.\n`{e}`"
                ))
            return

        # =========================
        # !REMOVEROLE
        # =========================
        if message.content.startswith("!removerole"):
            if not message.author.guild_permissions.manage_roles:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    f"**{message.author.mention}**, ponha-se no seu lugar, verme maldito."
                ))
                return

            args = message.content.split()

            if len(message.mentions) == 0 or len(args) < 3:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo..",
                    "Indique um alvo e o nome do cargo a ser removido.\nExemplo: `!removerole @usuário Cargo`"
                ))
                return

            member = message.mentions[0]
            role_name = " ".join(args[2:])
            role = discord.utils.get(message.guild.roles, name=role_name)

            if role is None:
                await message.channel.send(embed=chogoun_embed(
                    "Imprestável humano..",
                    f"O cargo **{role_name}** não existe."
                ))
                return

            if role not in member.roles:
                await message.channel.send(embed=chogoun_embed(
                    "Tentativa inútil...",
                    f"{member.mention} não possui o cargo **{role.name}**."
                ))
                return

            if role >= message.guild.me.top_role:
                await message.channel.send(embed=chogoun_embed(
                    "Poder insuficiente...",
                    f"Não posso gerenciar o cargo **{role.name}** pois ele está acima de mim."
                ))
                return

            try:
                await member.remove_roles(role, reason="Cargo removido por ordem do imperador Chogoun.")
                await message.channel.send(embed=chogoun_embed(
                    "Cargo removido por ordem do Imperador das Montanhas 🏔️",
                    f"O cargo **{role.name}** foi removido de {member.mention}."
                ))
            except Exception as e:
                await message.channel.send(embed=chogoun_embed(
                    "Falha imperial...",
                    f"Não foi possível remover o cargo.\n`{e}`"
                ))
            return

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
                "hands": {},
                "current_color": None,
                "host": message.author.id,
                "uno_pending": {},
                "uno_declared": {}
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

            if game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Tarde demais humano...",
                    "O jogo já começou."
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
                    f"{message.author.mention}, aguarde o início da partida."
                ))
                return

            game["players"].append(message.author.id)
            game["uno_pending"][message.author.id] = False
            game["uno_declared"][message.author.id] = False

            await message.channel.send(embed=chogoun_embed(
                "Jogador adicionado ao Uno 🏔️",
                f"{message.author.mention} entrou no jogo.\nAtualmente: **{len(game['players'])}** jogadores."
            ))
            return

        # =========================
        # !UNO DEAL
        # =========================
        if message.content.startswith("!uno deal"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo foi iniciado humano...",
                    "Use `!uno start` para iniciar um novo jogo."
                ))
                return

            if len(game["players"]) < 2:
                await message.channel.send(embed=chogoun_embed(
                    "Não há jogadores suficientes humano...",
                    "São necessários pelo menos 2 jogadores."
                ))
                return

            if game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "O jogo já começou humano...",
                    "Não pode distribuir cartas novamente."
                ))
                return

            game["deck"] = create_deck()
            game["discard_pile"] = []
            game["hands"] = {}
            game["direction"] = 1
            game["turn_index"] = 0
            game["current_color"] = None

            for player_id in game["players"]:
                hand = [game["deck"].pop() for _ in range(7)]
                game["hands"][player_id] = hand
                game["uno_pending"][player_id] = False
                game["uno_declared"][player_id] = False

            while True:
                first_card = game["deck"].pop()
                if first_card not in ["W", "W + 4"]:
                    break
                game["deck"].insert(0, first_card)
                random.shuffle(game["deck"])

            game["discard_pile"].append(first_card)
            game["current_color"] = get_card_color(first_card)
            game["started"] = True

            await send_all_hands(self, game)

            current_player_id = get_current_player_id(game)
            current_user = await self.fetch_user(current_player_id)

            await message.channel.send(embed=chogoun_embed(
                "🏔️ O Uno começou!",
                f"Carta inicial: **{first_card}**\n"
                f"Cor atual: **{game['current_color']}**\n"
                f"Primeiro turno: {current_user.mention}"
            ))
            return

        # =========================
        # !UNO HAND
        # =========================
        if message.content.startswith("!uno hand"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo em andamento humano...",
                    "Use `!uno start` e `!uno deal`."
                ))
                return

            if message.author.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você não está neste jogo humano...",
                    "Não tente espionar a mesa imperial."
                ))
                return

            await send_hand(self, message.author.id, game)
            await message.channel.send(embed=chogoun_embed(
                "Sua mão foi enviada por DM 🏔️",
                f"{message.author.mention}, consulte sua DM."
            ))
            return

        # =========================
        # !UNO STATUS
        # =========================
        if message.content.startswith("!uno status"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo existe neste servidor...",
                    "Use `!uno start` para iniciar um."
                ))
                return

            if not game["started"]:
                players_mentions = []
                for pid in game["players"]:
                    user = await self.fetch_user(pid)
                    players_mentions.append(user.mention)

                await message.channel.send(embed=chogoun_embed(
                    "Estado atual da sala de Uno 🏔️",
                    f"Jogadores: {', '.join(players_mentions) if players_mentions else 'Nenhum'}\n"
                    f"Status: aguardando `!uno deal`"
                ))
                return

            top_card = game["discard_pile"][-1]
            current_player_id = get_current_player_id(game)
            current_user = await self.fetch_user(current_player_id)

            direction_icon = "➡️" if game["direction"] == 1 else "⬅️"

            desc = (
                f"Topo: **{top_card}**\n"
                f"Cor atual: **{game['current_color']}**\n"
                f"Direção: **{direction_icon}**\n"
                f"Vez de: {current_user.mention}\n\n"
            )

            for pid in game["players"]:
                user = await self.fetch_user(pid)
                uno_alert = ""
                if game["uno_pending"].get(pid, False) and not game["uno_declared"].get(pid, False):
                    uno_alert = " ⚠️ (não declarou UNO)"
                elif len(game["hands"].get(pid, [])) == 1 and game["uno_declared"].get(pid, False):
                    uno_alert = " 🔥 UNO!"
                desc += f"{user.mention}: **{len(game['hands'][pid])}** cartas{uno_alert}\n"

            await message.channel.send(embed=chogoun_embed(
                "Estado atual do Uno do Imperador 🏔️",
                desc
            ))
            return

        # =========================
        # !UNO UNO
        # =========================
        if message.content.startswith("!uno uno"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhuma partida em andamento...",
                    "Não tente invocar regras onde não há jogo."
                ))
                return

            if message.author.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você não está neste jogo...",
                    "O UNO não reconhecerá sua voz."
                ))
                return

            if len(game["hands"].get(message.author.id, [])) != 1:
                await message.channel.send(embed=chogoun_embed(
                    "Declaração inválida...",
                    "Você só pode declarar UNO quando tiver **1 carta**."
                ))
                return

            game["uno_declared"][message.author.id] = True
            game["uno_pending"][message.author.id] = True

            await message.channel.send(embed=chogoun_embed(
                "🔥 UNO DECLARADO 🔥",
                f"{message.author.mention} declarou **UNO!**"
            ))
            return

        # =========================
        # !UNO CATCH
        # =========================
        if message.content.startswith("!uno catch"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhuma partida em andamento...",
                    "Não há ninguém para acusar."
                ))
                return

            if len(message.mentions) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "Acusação incompleta...",
                    "Use `!uno catch @usuário`"
                ))
                return

            target = message.mentions[0]

            if target.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Acusação inválida...",
                    "Esse usuário nem está na partida."
                ))
                return

            if target.id == message.author.id:
                await message.channel.send(embed=chogoun_embed(
                    "Patético...",
                    "Você não pode denunciar a si mesmo."
                ))
                return

            if len(game["hands"].get(target.id, [])) == 1 and game["uno_pending"].get(target.id, False) and not game["uno_declared"].get(target.id, False):
                drawn = draw_cards(game, target.id, 2)
                game["uno_pending"][target.id] = False
                game["uno_declared"][target.id] = False
                await send_hand(self, target.id, game)

                await message.channel.send(embed=chogoun_embed(
                    "⚠️ UNO ESQUECIDO ⚠️",
                    f"{target.mention} esqueceu de declarar UNO e comprou **{len(drawn)}** cartas por punição."
                ))
            else:
                drawn = draw_cards(game, message.author.id, 1)
                await send_hand(self, message.author.id, game)

                await message.channel.send(embed=chogoun_embed(
                    "Acusação fracassada...",
                    f"{message.author.mention} acusou incorretamente e comprou **{len(drawn)}** carta."
                ))
            return

        # =========================
        # !UNO DRAW
        # =========================
        if message.content.startswith("!uno draw"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo em andamento humano...",
                    "Use `!uno start` e `!uno deal`."
                ))
                return

            if message.author.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você não está neste jogo humano...",
                    "Não tente trapacear diante do imperador."
                ))
                return

            current_player_id = get_current_player_id(game)
            if message.author.id != current_player_id:
                await message.channel.send(embed=chogoun_embed(
                    "Não é sua vez humano...",
                    "Aguarde seu turno."
                ))
                return

            drawn = draw_cards(game, message.author.id, 1)

            if not drawn:
                await message.channel.send(embed=chogoun_embed(
                    "O baralho se esgotou humano...",
                    "Nem mesmo o destino lhe concedeu uma carta."
                ))
                return

            await send_hand(self, message.author.id, game)

            # se o jogador tinha pendência de UNO e passou turno, continua punível
            advance_turn(game, 1)
            next_player_id = get_current_player_id(game)
            next_user = await self.fetch_user(next_player_id)

            await message.channel.send(embed=chogoun_embed(
                "Carta comprada 🏔️",
                f"{message.author.mention} comprou **{drawn[0]}** e encerrou seu turno.\n"
                f"Próximo jogador: {next_user.mention}"
            ))
            return

        # =========================
        # !UNO PLAY
        # =========================
        if message.content.startswith("!uno play"):
            game = uno_games.get(message.guild.id)
            if not game or not game["started"]:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo em andamento humano...",
                    "Use `!uno start` e `!uno deal` para começar."
                ))
                return

            if message.author.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você não está neste jogo humano...",
                    "Não interfira nos assuntos do Uno imperial."
                ))
                return

            current_player_id = get_current_player_id(game)
            if message.author.id != current_player_id:
                await message.channel.send(embed=chogoun_embed(
                    "Não é sua vez humano...",
                    "Você tentou agir antes da hora."
                ))
                return

            args = message.content.split()
            if len(args) < 3:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    "Exemplo: `!uno play Vermelho5`"
                ))
                return

            raw_play = " ".join(args[2:]).strip()
            chosen_color = None

            if raw_play.startswith("W + 4 "):
                card_to_play = "W + 4"
                chosen_color = raw_play.replace("W + 4", "", 1).strip()
            elif raw_play.startswith("W "):
                card_to_play = "W"
                chosen_color = raw_play.replace("W", "", 1).strip()
            else:
                card_to_play = raw_play

            valid_colors = ['Vermelho', 'Amarelo', 'Verde', 'Azul']

            if card_to_play in ["W", "W + 4"]:
                if chosen_color not in valid_colors:
                    await message.channel.send(embed=chogoun_embed(
                        "Cor inválida humano...",
                        "Use uma cor válida.\nExemplo: `!uno play W Verde` ou `!uno play W + 4 Azul`"
                    ))
                    return

            player_hand = game["hands"].get(message.author.id, [])

            if card_to_play not in player_hand:
                await message.channel.send(embed=chogoun_embed(
                    "Carta inválida humano...",
                    f"Você não possui a carta **{card_to_play}**.\nSua mão: {', '.join(player_hand)}"
                ))
                return

            top_card = game["discard_pile"][-1]

            if not can_play(card_to_play, top_card, game["current_color"]):
                await message.channel.send(embed=chogoun_embed(
                    "Jogada inválida humano...",
                    f"A carta **{card_to_play}** não pode ser jogada sobre **{top_card}**.\n"
                    f"Cor atual: **{game['current_color']}**"
                ))
                return

            player_hand.remove(card_to_play)
            game["discard_pile"].append(card_to_play)

            played_desc = f"{message.author.mention} jogou **{card_to_play}**"

            if card_to_play in ["W", "W + 4"]:
                game["current_color"] = chosen_color
                played_desc += f" e escolheu a cor **{chosen_color}**"
            else:
                game["current_color"] = get_card_color(card_to_play)

            # UNO tracking
            await check_uno_penalty(self, message.channel, game, message.author.id)

            # Vitória imediata
            if len(player_hand) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "🏔️ VITÓRIA NO UNO IMPERIAL 🏔️",
                    f"{message.author.mention} venceu o jogo de Uno do Imperador das Montanhas!"
                ))
                del uno_games[message.guild.id]
                return

            card_value = get_card_value(card_to_play)

            if card_to_play == "W":
                advance_turn(game, 1)

            elif card_to_play == "W + 4":
                advance_turn(game, 1)
                target_id = get_current_player_id(game)
                drawn = draw_cards(game, target_id, 4)
                await send_hand(self, target_id, game)
                advance_turn(game, 1)

                target_user = await self.fetch_user(target_id)
                played_desc += f"\n{target_user.mention} comprou **{len(drawn)}** cartas e perdeu a vez."

            elif card_value == "Comprar 2":
                advance_turn(game, 1)
                target_id = get_current_player_id(game)
                drawn = draw_cards(game, target_id, 2)
                await send_hand(self, target_id, game)
                advance_turn(game, 1)

                target_user = await self.fetch_user(target_id)
                played_desc += f"\n{target_user.mention} comprou **{len(drawn)}** cartas e perdeu a vez."

            elif card_value == "Pular":
                advance_turn(game, 2)

            elif card_value == "Inverter":
                game["direction"] *= -1
                if len(game["players"]) == 2:
                    advance_turn(game, 2)
                else:
                    advance_turn(game, 1)

            else:
                advance_turn(game, 1)

            await send_hand(self, message.author.id, game)

            next_player_id = get_current_player_id(game)
            next_user = await self.fetch_user(next_player_id)

            await message.channel.send(embed=chogoun_embed(
                "Jogada realizada!",
                f"{played_desc}\n"
                f"Carta no topo agora: **{card_to_play}**\n"
                f"Cor atual: **{game['current_color']}**\n"
                f"Próximo jogador: {next_user.mention}"
            ))
            return

        # =========================
        # !UNO LEAVE
        # =========================
        if message.content.startswith("!uno leave"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo existe neste servidor...",
                    "Nada para abandonar."
                ))
                return

            if message.author.id not in game["players"]:
                await message.channel.send(embed=chogoun_embed(
                    "Você não está nesta partida...",
                    "Nem sequer estava no campo de batalha."
                ))
                return

            leaving_id = message.author.id
            leaving_index = game["players"].index(leaving_id)

            game["players"].remove(leaving_id)
            game["hands"].pop(leaving_id, None)
            game["uno_pending"].pop(leaving_id, None)
            game["uno_declared"].pop(leaving_id, None)

            if len(game["players"]) == 0:
                del uno_games[message.guild.id]
                await message.channel.send(embed=chogoun_embed(
                    "Partida encerrada...",
                    "Todos abandonaram a disputa."
                ))
                return

            if leaving_index < game["turn_index"]:
                game["turn_index"] -= 1
            elif leaving_index == game["turn_index"]:
                # se saiu na própria vez, mantém o índice para o próximo assumir
                pass

            normalize_turn_index(game)

            await message.channel.send(embed=chogoun_embed(
                "Jogador abandonou a partida 🏔️",
                f"{message.author.mention} saiu do jogo."
            ))

            ended = await maybe_end_game_due_to_player_count(self, message.channel, message.guild.id)
            if ended:
                return

            if game["started"]:
                current_player_id = get_current_player_id(game)
                current_user = await self.fetch_user(current_player_id)
                await message.channel.send(embed=chogoun_embed(
                    "A partida continua...",
                    f"Agora é a vez de {current_user.mention}."
                ))
            return

        # =========================
        # !UNO END
        # =========================
        if message.content.startswith("!uno end"):
            game = uno_games.get(message.guild.id)
            if not game:
                await message.channel.send(embed=chogoun_embed(
                    "Nenhum jogo existe neste servidor...",
                    "Nada para encerrar."
                ))
                return

            if message.author.id != game["host"] and not message.author.guild_permissions.manage_guild:
                await message.channel.send(embed=chogoun_embed(
                    "Você não pode encerrar este jogo humano...",
                    "Somente quem criou a partida ou um administrador pode encerrá-la."
                ))
                return

            del uno_games[message.guild.id]
            await message.channel.send(embed=chogoun_embed(
                "Jogo encerrado 🏔️",
                "A partida de Uno foi finalizada por ordem superior."
            ))
            return


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