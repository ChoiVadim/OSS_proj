import threading
from time import time
from random import randint
import json

import openai
from openai import OpenAI
import cv2
import cvzone
import telebot
from pvrecorder import PvRecorder
from pydub.playback import play
from pydub import AudioSegment

import config
from face_det_module import FaceDetector
from hand_track_module import HandDetector
from config import porcupine
from speech_to_text import speech_to_text
from openai_module import (generate_image, say, add_message_to_thread,
                           get_answer)


send_photo_flag = False
openai.api_key = config.OPENAI_KEY
client = OpenAI()
thread = client.beta.threads.create()

def main():
    # text = vision("img/screenshot.jpg")

    # Recorder for a wakeup word
    recorder = PvRecorder(device_index=1, frame_length=config.porcupine.frame_length)
    recorder.start()
    print('Using device: %s' % recorder.selected_device)

    # Check how mush time has been passed before lust
    # wakeup word was called 
    ltc = time() - 1000

    while True:
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            recorder.stop()
            audio = AudioSegment.from_file("sound/greetings/main_greet.mp3", format="mp3")
            play(audio)
            recorder.start()
            ltc = time()
            
        while time() - ltc <= 20:
            try:
                my_msg = speech_to_text()
                if my_msg:
                    print(f"Human: \033[94m{my_msg}\033[0m")
                    add_message_to_thread(thread.id, my_msg)
                    jarvis_resp = get_answer(config.ASSISTANT_ID, thread)

                    if type(jarvis_resp) == str:
                        print(f"Jarvis: \033[95m{jarvis_resp}\033[0m\n")
                        say(jarvis_resp)

                    else:
                        func_name = jarvis_resp[0]
                        func_arg = json.loads(jarvis_resp[1])["prompt"]

                        if func_name == "generate_image":
                            say("Yes, sure! Will do it right now.")
                            print("Drawing... Wait a second!")
                            generate_image(func_arg)                   
       

            except KeyboardInterrupt:
                # th.join()
                porcupine.delete()
                break
            except Exception as e:
                print(e)
                say("Sorry, I didn't get that.")

   
def telegram_jarvis_bot():
    bot = telebot.TeleBot(config.TELEGRAM_TOKEN)

    def send_photo():
        global send_photo_flag

        while True:
            if send_photo_flag: 
                with open('screenshot.jpg', 'rb') as photo:
                    bot.send_photo('1815092465', photo)
                    send_photo_flag = False

    threading.Thread(target=send_photo).start()

    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)

def jarvis_vis():
    global send_photo_flag
    take_photo_flag = False

    cap = cv2.VideoCapture(0)

    detector_hand = HandDetector(staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5)
    detector_face = FaceDetector(minDetectionCon=0.5, modelSelection=0)

    face_detection_flag = True
    while True:
        success, img = cap.read()
        photo = img.copy()

        hands, img = detector_hand.findHands(img, draw=True, flipType=True)
        img, bboxs = detector_face.findFaces(img, draw=False)

        if not bboxs:
            face_det_flag = True
        if bboxs:
            if face_det_flag:
                # threading.Thread(target=play, args=("sound/yes_sir.mp3", )).start()
                face_det_flag = False
            
            for bbox in bboxs:
                x, y, w, h = bbox['bbox']
                cvzone.cornerRect(img, (x, y, w, h))

        # Check if any hands are detected
        if hands:
            # Information for the first hand detected
            hand1 = hands[0] 
            fingers1 = detector_hand.fingersUp(hand1)
            
            if fingers1 == [0, 0, 0, 0, 0]:
                print("Yes, sir!")
                # threading.Thread(target=play_audio, args=("sound/yes_sir.mp3", )).start()

            if fingers1 == [0, 1, 1, 0, 0]:
                take_photo_flag = True
                init_time = time.time()


            # Check if a second hand is detected
            if len(hands) == 2:
                hand2 = hands[1]

        # Set timer for taking a photo and send it to telegram
        if take_photo_flag:
            timer = int(time.time() - init_time)
            if timer <= 3:
                cv2.putText(img, str(timer), (150, 350), cv2.FONT_HERSHEY_PLAIN, 25, (255, 255, 255), 20)
            if timer > 3:
                cv2.imwrite("screenshot.jpg", photo)
                send_photo_flag = True
                take_photo_flag = False

        # Display the image in a window
        cv2.imshow("Image", img)

        # Keep the window open and update it for each frame; wait for 1 millisecond between frames
        if cv2.waitKey(1) & 0xff == ord('q'):
            break

if __name__ == "__main__":
    main()