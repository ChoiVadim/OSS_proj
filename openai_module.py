import io
import time
import webbrowser
import base64
import requests
import json

import openai
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play

import config


openai.api_key = config.OPENAI_KEY
client = OpenAI()

def main():
    thread = client.beta.threads.create()
    while True:
        add_message_to_thread(thread.id, input("Enter: "))
        msg = get_answer(config.ASSISTANT_ID, thread)
        if type(msg) == str:
            print(msg)
        else:
            func_name = msg[0]
            func_arg = json.loads(msg[1])["prompt"]
            if func_name == "generate_image":
                generate_image(func_arg)


def create_assistant():
    # Create the assistant
    assistant = client.beta.assistants.create(
        name="MateTest",
        instructions="This is a test assistant",
        model="gpt-4-1106-preview",
        tools=[],
    )
    return assistant

def add_message_to_thread(thread_id, user_question):
    # Create a message inside the thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content= user_question
    )
    return message

def get_answer(assistant_id, thread):
    print("Thinking...")
    # run assistant
    run =  client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # wait for the run to complete
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    print("All done...")

    if run.required_action:
        tool_id = run.required_action.submit_tool_outputs.tool_calls[0].id
        tool_arg = run.required_action.submit_tool_outputs.tool_calls[0].function.arguments
        func_name = run.required_action.submit_tool_outputs.tool_calls[0].function.name

        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=[
                {
                "tool_call_id": tool_id,
                "output": tool_arg,
                }
            ]
            )
        return [func_name, tool_arg]
    
    # Get messages from the thread
    messages = client.beta.threads.messages.list(thread.id)
    message_content = messages.data[0].content[0].text.value
    return message_content
#########################################################################



def say(text):
    response = client.audio.speech.create(
        model=config.ASSISTANT_VOICE_MODEL,
        voice=config.ASSISTANT_VOICE,
        input=text
    )
    byte_stream = io.BytesIO(response.content)
    audio = AudioSegment.from_file(byte_stream, format="mp3")
    play(audio)
    
def convert_to_audio(text, file_path):
    response = client.audio.speech.create(
        model=config.ASSISTANT_VOICE_MODEL,
        voice=config.ASSISTANT_VOICE,
        input=text
    )
    byte_stream = io.BytesIO(response.content)

    song = AudioSegment.from_file(byte_stream, format="mp3")
    song.export(file_path, format="mp3")

def audio_to_text(file_path):
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
        "Authorization": f"Bearer {config.OPENAI_KEY}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "What is in this image? Give a really short description. Should be less than 10 words."
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
    return response.json().get("choices")[0].get("message").get("content")

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