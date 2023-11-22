from dotenv import load_dotenv
import os
import pvporcupine

load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
THREAD_ID = os.getenv('THREAD_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PVPORCUPINE_KEY = os.getenv('ACCESS_KEY')

ASSISTANT_VOICE = "alloy"
ASSISTANT_VOICE_MODEL = "tts-1"


porcupine = pvporcupine.create(
    access_key=PVPORCUPINE_KEY,
    keywords=['jarvis'],
    sensitivities=[1]
)
#print(pvporcupine.KEYWORDS)

# INSTRUCTIONS = """Answer the following questions to generate a short response"""
# pip freeze > requirements.txt
# pip install -r requirements.txt