import threading
from threading import Thread
import time

import cv2
import telebot
import openai
import cvzone 
from openai import OpenAI
from pvrecorder import PvRecorder
from pydub.playback import play
from pydub import AudioSegment

import config
from config import porcupine
from modules.face_det_module import FaceDetector
from modules.hand_track_module import HandDetector
from modules.speech_to_text import speech_to_text
from modules.openai_module import (generate_image, say, add_message_to_thread,
                           get_answer, describe_img)
from modules.commands import *


# Global variables
send_photo_flag = False
take_photo_flag = False
init_time = 0


# Not in main for using in threads
openai.api_key = config.OPENAI_KEY
client = OpenAI()
# Create a thread for assistant
# You can add already existing thread id
thread = client.beta.threads.create()


def main():
    # Create a thread for jarvis vision
    run_event = threading.Event()
    run_event.set()
    thread_for_jarvis_vis = threading.Thread(target=jarvis_vis,
                                             args=(run_event, ))
    thread_for_jarvis_vis.daemon = True
    thread_for_jarvis_vis.start()

    # # Create a thread for telegram bot
    # thread_for_telegram_bot = threading.Thread(target=telegram_bot,
    #                                            args=(run_event, ))
    # thread_for_telegram_bot.daemon = True
    # thread_for_telegram_bot.start()


    # Recorder for a wakeup word
    recorder = PvRecorder(device_index=1,
                          frame_length=config.porcupine.frame_length)
    recorder.start()
    print('Using device: %s' % recorder.selected_device)

    # Var for check how much time has been passed
    # before lust wakeup word was called 
    wakeup_word_time = time.time() - 1000

    while True:
        # Read audio for a wakeup word
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)

        # If a wakeup word was called
        if keyword_index >= 0:
            recorder.stop()
            audio = AudioSegment.from_file("sound/greetings/main_greet.mp3",
                                           format="mp3")
            play(audio)
            recorder.start()
            wakeup_word_time = time.time()
            
        while time.time() - wakeup_word_time <= 20:
            try:
                my_msg = speech_to_text()
                if my_msg:
                    print(f"Human: \033[94m{my_msg}\033[0m")
                    add_message_to_thread(thread.id, my_msg)
                    resp = get_answer(config.ASSISTANT_ID, thread)

                    if type(resp) == str:
                        print(f"Jarvis: \033[95m{resp}\033[0m\n")
                        say(resp)

                    else:
                        if "mute" in resp: mute()
                        if "unmute" in resp: unmute()
                        if "take_a_photo" in resp: take_a_photo()
                        if "generate_image" in resp: generate_image(resp)   
                        if "describe_img" in resp: say(describe_img("jpg/screenshot.jpg"))
                        if "search_and_play_song" in resp:
                            Thread(target=search_and_play_song, args=(resp, )).start()
       
            except KeyboardInterrupt:
                run_event.clear()
                thread_for_jarvis_vis.join()
                # thread_for_telegram_bot.join()
                recorder.stop()
                porcupine.delete()
                print("Goodbye!")
                break

            except (OpenAI.TryAgain, OpenAI.ServiceUnavailableError, 
                    OpenAI.TooManyRequestsError):
                say("Sorry, Too many requests. Try again later.")
                time.sleep(120)

            except OpenAI.OpenAIError as e:
                print(e)
                break
            

def jarvis_vis(run_event):
    global send_photo_flag
    global take_photo_flag
    global init_time
    face_detection_flag = True

    # Create a video capture object
    cap = cv2.VideoCapture(0)

    # Create a hand and face detector object
    detector_hand = HandDetector(staticMode=False, maxHands=2, modelComplexity=1,
                                 detectionCon=0.5, minTrackCon=0.5)
    detector_face = FaceDetector(minDetectionCon=0.5, modelSelection=0)

    while run_event.is_set():
        success, img = cap.read()
        photo = img.copy()

        # Find the hands and face in the current frame
        hands, img = detector_hand.findHands(img, draw=True, flipType=True)
        img, bboxs = detector_face.findFaces(img, draw=False)

        if not bboxs:
            face_detection_flag = True
        if bboxs:
            if face_detection_flag:
                # any func to do
                face_detection_flag = False
            
            # Draw the bounding box around the face
            for bbox in bboxs:
                x, y, w, h = bbox['bbox']
                cvzone.cornerRect(img, (x, y, w, h))


        # Check if any hands are detected
        if hands:
            # Information for the first hand detected
            hand1 = hands[0] 
            fingers1 = detector_hand.fingersUp(hand1)
            

            if fingers1 == [0, 1, 1, 0, 0]:
                take_photo_flag = True
                init_time = time.time()

            # Check if a second hand is detected
            if len(hands) == 2:
                hand2 = hands[1]

        # Set timer for taking a photo adn take a photo
        if take_photo_flag:
            timer = int(time.time() - init_time)
            if timer <= 3:
                cv2.putText(img, str(timer), (150, 350), cv2.FONT_HERSHEY_PLAIN,
                            25, (255, 255, 255), 20)
            if timer > 3:
                cv2.imwrite("img/screenshot.jpg", photo)
                send_photo_flag = True
                take_photo_flag = False


        # Display the image in a window
        cv2.imshow("Jarvis Eyes", img)

        # Keep the window open and update it for each frame; wait for 1 millisecond between frames
        if cv2.waitKey(1) & 0xff == ord('q'):
            return 0
    cv2.destroyAllWindows()


def telegram_bot(run_event):
    bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

    def send_photo():
        global send_photo_flag
        while run_event.is_set():  
            if send_photo_flag: 
                with open('img/screenshot.jpg', 'rb') as photo:
                    bot.send_photo('1815092465', photo)
                    send_photo_flag = False
        bot.stop_polling()

    try:
        print("Bot is running...")
        th = threading.Thread(target=send_photo)
        th.start()
        bot.polling(none_stop=True)
        th.join()
    except Exception as e:
        print(e)


def take_a_photo():
    global take_photo_flag
    global init_time
    take_photo_flag = True
    init_time = time.time()


if __name__ == "__main__":
    main()