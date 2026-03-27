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

                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()

                def after_play(error):
                    if error:
                        print("ERRO NO PLAYER:", error)

                voice_client.play(source, after=after_play)

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
                value="`!uno start`\n`!uno join`\n`!uno deal`",
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
                    "Finalmente um humano para eu me divertir, mas já tem um jogo em andamento neste servidor."
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
                "🏔️ Uno invocado pelo Imperador! Estou bastante empolgado!",
                "Quem deseja jogar comigo? Digite `!uno join` para participar. (Máx 10 jogadores)"
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
                    "Use `!uno start` para iniciar finalmente um novo jogo."
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
                    f"{message.author.mention}, aguarde o início do jogo ou convide outros jogadores para se juntarem usando `!uno join`."      
                ))
                return
        
            game["players"].append(message.author.id)   
            await message.channel.send(embed=chogoun_embed(
                    "Jogador adicionado ao jogo de Uno do Imperador das Montanhas! 🏔️",
                    f"{message.author.mention} se juntou ao jogo. Atualmente {len(game['players'])} jogadores."
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
                    "Espere mais jogadores se juntarem usando `!uno join`."
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
            
            for player_id in game["players"]:
                hand = [game["deck"].pop() for _ in range(7)]
                game["hands"][player_id] = hand
                user = await self.fetch_user(player_id)
                try:
                    await user.send(embed=chogoun_embed(
                        "Suas cartas foram distribuídas pelo Imperador das Montanhas! 🏔️",
                        f"Sua mão: {', '.join(hand)}"
                    ))
                except Exception as e:
                    print(f"ERRO AO ENVIAR CARTAS PARA {user}: {e}")
            
            game["started"] = True
            first_card = game["deck"].pop()
            game["discard_pile"].append(first_card)

            await message.channel.send(embed=chogoun_embed(
                "Cartas distribuídas! O jogo de Uno do Imperador das Montanhas começou! 🏔️",
                f"{len(game['players'])} jogadores estão prontos para jogar.\nCarta inicial: **{first_card}**"
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
            
            args = message.content.split()
            if len(args) < 3:
                await message.channel.send(embed=chogoun_embed(
                    "Humano tolo...",
                    "Indique a carta que deseja jogar. Exemplo: `!uno play Vermelho5`"
                ))
                return

            card_to_play = " ".join(args[2:])
            player_hand = game["hands"].get(message.author.id, [])

            if card_to_play not in player_hand:
                await message.channel.send(embed=chogoun_embed(
                    "Carta inválida humano...",
                    f"Você não possui a carta **{card_to_play}** na mão.\nSua mão: {', '.join(player_hand)}"
                ))
                return

            top_card = game["discard_pile"][-1]

            # Simples verificação de cor ou número
            if (top_card[0] != card_to_play[0]) and (top_card[-1] != card_to_play[-1]) and "W" not in card_to_play:
                await message.channel.send(embed=chogoun_embed(
                    "Jogada inválida humano...",
                    f"A carta **{card_to_play}** não pode ser jogada sobre **{top_card}**"
                ))
                return

            # Remove da mão e adiciona na pilha de descarte
            player_hand.remove(card_to_play)
            game["discard_pile"].append(card_to_play)

            await message.channel.send(embed=chogoun_embed(
                "Jogada realizada!",
                f"{message.author.mention} jogou **{card_to_play}**\nCarta no topo agora: **{card_to_play}**"
            ))
            
            # Verifica vitória
            if len(player_hand) == 0:
                await message.channel.send(embed=chogoun_embed(
                    "🏔️ HUMANO DERROTADO PELO IMPERADOR 🏔️",
                    f"{message.author.mention} venceu o jogo de Uno do Imperador das Montanhas!"
                ))
                del uno_games[message.guild.id]
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