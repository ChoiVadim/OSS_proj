import openai
from openai import OpenAI

import config
from modules.openai_module import (generate_image, describe_img,
                           add_message_to_thread, get_answer)
from modules.commands import *
from threading import Thread


# Not in main for using in threads
openai.api_key = config.OPENAI_KEY
client = OpenAI()
thread = client.beta.threads.create()

while True:
    my_msg = input("Human: ")
    print(f"Human: \033[94m{my_msg}\033[0m")
    add_message_to_thread(thread.id, my_msg)
    jarvis_resp = get_answer(config.ASSISTANT_ID, thread)

    if type(jarvis_resp) == str:
        print(f"Jarvis: \033[95m{jarvis_resp}\033[0m\n")

    else:
        print(jarvis_resp)

        if "mute" in jarvis_resp: mute()
        if "unmute" in jarvis_resp: unmute()

        if "generate_image" in jarvis_resp: 
            generate_image(jarvis_resp)   

        if "describe_img" in jarvis_resp:
            text = describe_img("img/screenshot.jpg")
            print(f"Jarvis: \033[95m{text}\033[0m\n")

        if "search_and_play_song" in jarvis_resp:
            Thread(target=search_and_play_song, args=(jarvis_resp, )).start()

        if "take_a_photo" in jarvis_resp:
            print("Taking a photo...")



