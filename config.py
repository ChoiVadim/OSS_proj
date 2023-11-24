import os
import socket

import pvporcupine
from dotenv import load_dotenv


load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
THREAD_ID = os.getenv('THREAD_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PVPORCUPINE_KEY = os.getenv('ACCESS_KEY')

ASSISTANT_VOICE = "alloy"
ASSISTANT_VOICE_MODEL = "tts-1"

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
HOST_BLUETOOTH  = 'C0:3C:59:D8:CE:8E'
PORT_BLUETOOTH = 6
ADDR = (SERVER, PORT)
FORMAT = "ASCII"
DISCONNECT_MESSAGE = "!DISCONNECT"
MSG = ""

porcupine = pvporcupine.create(
    access_key=PVPORCUPINE_KEY,
    keywords=['jarvis'],
    sensitivities=[1]
)
#print(pvporcupine.KEYWORDS)

# pip freeze > requirements.txt
# pip install -r requirements.txt

