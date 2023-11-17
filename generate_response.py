import os
from time import sleep
from threading import Thread

import openai
import webbrowser
from openai import OpenAI
from playsound import playsound


from dotenv import load_dotenv


load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI()


def main():
    image_url = input("Enter image url: ")
    
    res = image_rec(image_url)
    th2 = Thread(target=generate_image, args=(res,))
    th1 = Thread(target=text_to_speech, args=(res,))
    th1.start()
    th2.start()
    th1.join()
    th2.join()


def image_rec(image_url):
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

    res = response.choices[0]
    res = res.message.content
    return res


def text_to_speech(res):
    response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input=res
    )

    response.stream_to_file("speech.mp3")
    playsound("speech.mp3")
    sleep(1)
    os.remove("speech.mp3")


def generate_image(res):
    response = client.images.generate(
        model="dall-e-3",
        prompt=res,
        size="1792x1024",
        quality="hd",
        n=1,
    )

    image_url = response.data[0].url
    webbrowser.open(image_url, new=0, autoraise=True)


if __name__ == "__main__":
    main()