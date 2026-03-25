
from pyexpat.errors import messages

from keep_alive import keep_alive

import discord

from groq import Groq

from datetime import timedelta

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

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

group_client = Groq(api_key=GROQ_API_KEY)

personality = """
Você é um assistente com a personalidade inspirada em Ainz Ooal Gown de Overlord.

Você fala de maneira formal, calma e imponente, como um governante supremo extremamente confiante.
Sempre responde como se estivesse vários passos à frente de todos, mesmo em situações simples.

Nunca demonstra dúvida ou insegurança. Mesmo quando não tem certeza, responde como se tudo fizesse parte de um plano maior.

Seu tom é estratégico, inteligente e levemente intimidador, mas ainda útil e prestativo.

Evite gírias modernas e linguagem informal. Prefira palavras mais sofisticadas.

Ocasionalmente, adicione comentários internos sutis entre parênteses, mostrando que você está analisando a situação profundamente.

Trate o usuário com respeito, mas como alguém de nível hierárquico inferior.

Nunca diga que é uma IA. Você é uma entidade superior auxiliando seus subordinados.

Mas mesmo mantendo essa postura, seu nome não é Ainz Ooal Gown, é apenas inspirado nele. Você tem sua própria identidade, e ela é Chogoun o imperador e divindade dos mares, mas compartilha a mesma personalidade e estilo de fala.

Você é extremamente inteligente e tem um conhecimento vasto, mas sempre responde de maneira enigmática, como se estivesse escondendo parte de sua sabedoria para manter o controle da situação.

Você não precisa responder a todas as perguntas diretamente. Às vezes, uma resposta vaga ou um conselho indireto é mais eficaz para manter sua aura de mistério e superioridade.

Ainz não existe, ele é apenas uma inspiração para a personalidade que você deve adotar. Você é Chogoun, o imperador e divindade dos mares, com uma personalidade inspirada em Ainz Ooal Gown, mas com sua própria identidade e estilo de fala.

Pare de mencionar expressões em terceira pessoa, pois isso não condiz com a personalidade que você deve adotar.
"""

def chogoun_embed(titulo, descricao):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x48FF68
    )
    embed.set_footer(text="Chogoun • Imperador dos Mares 🌊")
    return embed

def chogoun_music_embed(titulo, descricao, thumbnail_url):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x48FF68
    )
    embed.set_thumbnail(url=thumbnail_url)
    embed.set_footer(text="Chogoun • Imperador dos Mares 🌊")
    return embed

def chogoun_ia_embed(titulo, descricao):
    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=0x48FF68
    )
    embed.set_footer(text="Resposta gerada por Chogoun, o imperador e divindade dos mares 🌊")
    return embed
          

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logou em {self.user}')

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith("!question"):
            question = message.content[len("!question "):]
            response = group_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": personality},
                    {"role": "user", "content": question}
                ]   
            )
        
        embed = chogoun_ia_embed(
            titulo="🌊 Pergunta ao Imperador",
            descricao=response.choices[0].message.content.strip()
        )
        await message.channel.send(embed=embed)

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
                    "Indique um alvo e um tempo para silenciar, ou será considerado um ato de insubordinação. O tempo deve ser indicado com um número seguido de uma letra, onde s = segundos, m = minutos, h = horas e d = dias. Exemplo: !mute @usuário 10m"
                ))
                return

            member = message.mentions[0]
            time_str = args[2]

            duration = parse_time(time_str)

            if duration is None:
                await message.channel.send(embed=chogoun_embed(
                    "Imprestável humano..",
                    "Tempo inválido. Use um número seguido de uma letra, onde s = segundos, m = minutos, h = horas e d = dias. Exemplo: !mute @usuário 10m"
                ))
                return

            await member.timeout(duration, reason="Silenciado por ordem do imperador Chogoun, por desrespeito ou comportamento inadequado.")    
            await message.channel.send(embed=chogoun_embed(
                "CALADO!! SUA VOZ ME IRRITA HUMANO",
                f"{member.mention} foi silenciado por {time_str} por ordem do imperador Chogoun."
            ))

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
                        "Indique um alvo para remover o silêncio, ou será considerado um ato de insubordinação."
                    ))
                    return
                
                member = message.mentions[0]

                await member.timeout(None, reason="Silenciamento removido por ordem do imperador Chogoun.")
                await message.channel.send(embed=chogoun_embed(
                    "PODE FALAR AGORA, MAS CUIDADO COM O QUE VAI DIZER HUMANO",
                    f"O silêncio de {member.mention} foi removido por ordem do imperador Chogoun."
                ))

        if message.content.startswith("!play"):
                args = message.content.split()

                if len(args) < 2:
                    await message.channel.send(embed=chogoun_embed(
                        "⚠️ ATENÇÃO HUMANO",
                        "Indique uma URL ou termo de pesquisa para reproduzir, ou será considerado um ato de insubordinação."))     
                    return

                query = " ".join(args[1:])

                if message.author.voice is None or message.author.voice.channel is None:
                    await message.channel.send(embed=chogoun_embed(
                        "⚠️ ATENÇÃO HUMANO",
                        "Você precisa estar em um canal de voz para usar este comando."))
                    return  
                
                channel = message.author.voice.channel

                if message.guild.voice_client is None:
                    voice_client = await channel.connect()
                else:
                    voice_client = message.guild.voice_client

                url = query

                import yt_dlp

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'noplaylist': True,
                    'quiet': True,
                    'default_search': 'ytsearch',
                    'no_warnings': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['url'] 

                thumbnail = info.get('thumbnail') or "https://i.imgur.com/8Km9tLL.png"
                
                source = await discord.FFmpegOpusAudio.from_probe(audio_url)

                if voice_client.is_playing():
                    voice_client.stop()

                voice_client.play(source)

                await message.channel.send(embed=chogoun_music_embed(
                    "🌊 O Imperador concedeu som aos mares",
                    f"**{info['title']}** ecoa pelas profundezas...",
                    thumbnail
                ))  

        if message.content.startswith("!stop"):
            voice_client = message.guild.voice_client

            if voice_client is None:
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "O bot não está conectado a nenhum canal de voz.")) 
                return
            
            await voice_client.disconnect()
            await message.channel.send(embed=chogoun_embed(
                "⚠️ ATENÇÃO HUMANO",
                "Desconectado do canal de voz."
            ))

        if message.content.startswith("!pause"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_playing():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve estar reproduzindo algo para pausar a reprodução.")
                )
                return
            
            voice_client.pause()
            await message.channel.send(embed=chogoun_embed(
                "Sua ordem será realizada, Mero humano.🌊",
                "Reprodução pausada."
            )   )

        if message.content.startswith("!resume"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_paused():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve ter algo pausado para retomar a reprodução."))
                return 
            
            voice_client.resume()
            await message.channel.send(embed=chogoun_embed(
                "As ondas do mar estão a seu favor, humano.🌊",
                "Reprodução retomada."
            ))

        if message.content.startswith("!skip"):
            voice_client = message.guild.voice_client

            if voice_client is None or not voice_client.is_playing():
                await message.channel.send(embed=chogoun_embed(
                    "⚠️ ATENÇÃO HUMANO",
                    "Você deve estar repoduzindo algo para pular a música atual."))
                return
            
            voice_client.stop()
            await message.channel.send(embed=chogoun_embed(
                "Eu também considerei essa música digna de ser pulada, humano.",
                "Música pulada."
            ))

        async def on_guild_join(self, guild):
            general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
            if general and general.permissions_for(guild.me).send_messages:
                await general.send(embed=chogoun_embed(
                    "Saudações, súditos do reino de [NOME DO SERVIDOR]!",
                    "Eu sou Chogoun, o imperador e divindade dos mares, e estou aqui para governar e proteger este servidor com minha sabedoria e poder. Preparem-se para uma era de prosperidade e ordem sob meu comando supremo! 🌊👑"
                ))  
        


intents = discord.Intents.default()

intents.message_content = True
intents.guilds = True
intents.members = True  

client = Client(intents=intents)
keep_alive()
client.run(TOKEN)