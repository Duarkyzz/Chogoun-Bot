import groq
print('groq', getattr(groq, '__version__', '<unknown>'))
from groq import Groq
c = Groq(api_key='x')
print('has chat', hasattr(c, 'chat'))
print('chat attrs', [a for a in dir(c) if 'chat' in a.lower()])

chat_obj = c.chat
print('chat type', type(chat_obj))
print('chat methods maybe', [a for a in dir(chat_obj) if 'completion' in a.lower() or 'create' in a.lower()])
