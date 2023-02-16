import os

from dotenv import load_dotenv

load_dotenv()

token_practicum = os.getenv('PRACTICUM_TOKEN')

token_auth = os.getenv('TELEGRAM_TOKEN')

token_id = os.getenv('TELEGRAM_CHAT_ID')

print(token_practicum)
print(token_auth)
print(token_id)
