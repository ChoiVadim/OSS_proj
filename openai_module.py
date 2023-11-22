import io
import time
import webbrowser
import base64
import requests

import openai
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play

import config


openai.api_key = config.OPENAI_KEY
client = OpenAI()

def main():
    generate_image("Iron man suit with a blue and red color scheme")
    text = vision("img/screenshot.jpg")
    print(text)
    listen("sound/test.mp3")

    while True:
        msg = input("You: ")
        run = submit_message(config.ASSISTANT_ID, config.THREAD_ID, msg)
        wait_on_run(run, config.THREAD_ID)
        response = get_response(config.THREAD_ID)
        pretty_print(response)
        speak(response.data[0].content[0].text.value)


def submit_message(assistant_id, thread, user_message):
    client.beta.threads.messages.create(
        thread_id=thread, role="user", content=user_message
    )
    return client.beta.threads.runs.create(
        thread_id=thread,
        assistant_id=assistant_id,
    )

def get_response(thread):
    return client.beta.threads.messages.list(thread_id=thread)

# Pretty printing helper
def pretty_print(messages):
    print(f"{messages.data[0].role}: {messages.data[0].content[0].text.value}\n")


# Waiting in a loop
def wait_on_run(run, thread):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def speak(text):
    response = client.audio.speech.create(
        model=config.ASSISTANT_VOICE_MODEL,
        voice=config.ASSISTANT_VOICE,
        input=text
    )
    byte_stream = io.BytesIO(response.content)
    audio = AudioSegment.from_file(byte_stream, format="mp3")
    play(audio)

def listen(file_path):
    audio_file = open(file_path, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
    )
    return transcript

def vision_url(image_url):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Whats in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

def vision(image_path):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_KEY}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "What is in this image?"
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()

def generate_image(prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    webbrowser.open(image_url, new=0, autoraise=True)


if __name__ == "__main__":
    main()