from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')
THREAD_ID = os.getenv('THREAD_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PVPORCUPINE_KEY = os.getenv('ACCESS_KEY')

ASSISTANT_VOICE = "alloy"
ASSISTANT_VOICE_MODEL = "tts-1"

#INSTRUCTIONS = """Answer the following questions to generate a short response"""