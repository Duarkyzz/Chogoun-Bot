from pyexpat.errors import messages

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
            
            await message.channel.send(response.choices[0].message.content)

        if message.content.startswith("!ban"):
            if not message.author.guild_permissions.ban_members:
                await message.channel.send("Você ousa tentar uma ação além de sua autoridade? Nesse caso ponha-se no seu lugar, e pense se realmente tem o direito de expulsar alguém.")
                return
            if len(message.mentions) == 0:
                await message.channel.send("Indique um alvo para banir, ou será considerado um ato de insubordinação.")
                return
            
            member = message.mentions[0]

            await member.ban(reason="Banido pelo imperador Chogoun, por desrespeito ou comportamento inadequado.")
            await message.channel.send(f"{member.mention} foi banido por ordem do imperador Chogoun.")
        
        if message.content.startswith("!kick"):
            if not message.author.guild_permissions.kick_members:
                await message.channel.send("Você ousa tentar uma ação além de sua autoridade? Nesse caso ponha-se no seu lugar, e pense se realmente tem o direito de expulsar alguém.")
                return
            if len(message.mentions) == 0:
                await message.channel.send("Indique um alvo para expulsar, ou será considerado um ato de insubordinação.")
                return
            
            member = message.mentions[0]

            await member.kick(reason="Expulso por ordem do imperador Chogoun, por desrespeito ou comportamento inadequado.")
            await message.channel.send(f"{member.mention} foi expulso por ordem do imperador Chogoun.")

        if message.content.startswith("!mute"):
            if not message.author.guild_permissions.mute_members:
                await message.channel.send("Você ousa tentar uma ação além de sua autoridade? Nesse caso ponha-se no seu lugar, e pense se realmente tem o direito de silenciar alguém.")
                return
            
            args = message.content.split()

            if len(message.mentions) == 0 or len(args) < 3:
                await message.channel.send("Indique um alvo e um tempo para silenciar, ou será considerado um ato de insubordinação. O tempo deve ser indicado com um número seguido de uma letra, onde s = segundos, m = minutos, h = horas e d = dias. Exemplo: !mute @usuário 10m")
                return

            member = message.mentions[0]
            time_str = args[2]

            duration = parse_time(time_str)

            if duration is None:
                await message.channel.send("Tempo inválido. Use um número seguido de uma letra, onde s = segundos, m = minutos, h = horas e d = dias. Exemplo: !mute @usuário 10m")
                return

            await member.timeout(duration, reason="Silenciado por ordem do imperador Chogoun, por desrespeito ou comportamento inadequado.")    
            await message.channel.send(f"{member.mention} foi silenciado por {time_str} por ordem do imperador Chogoun.")   

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  

client = Client(intents=intents)
client.run(TOKEN)