import time
import socket
import threading
from threading import Thread

import cv2
import cvzone 
import openai
import telebot
from openai import OpenAI
from pvrecorder import PvRecorder
from pydub.playback import play
from pydub import AudioSegment

from modules import config
from modules.config import porcupine
from modules.commands import *
from modules.face_det_module import FaceDetector
from modules.hand_track_module import HandDetector
from modules.speech_to_text import speech_to_text
from modules.openai_module import (generate_image, say,
                                    add_message_to_thread,
                                    get_answer, describe_img)


# Global variables
take_photo_flag = False
send_photo_flag = False
init_time = 0
MSG = False

# #For local server
# server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.bind(config.ADDR)

# # For bluetooth server
# server = socket.socket(socket.AF_BLUETOOTH,
#                         socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
# server.bind((config.HOST_BLUETOOTH, config.PORT_BLUETOOTH))

# server.listen(3)

# Not in main for using in threads
openai.api_key = config.OPENAI_KEY
client = OpenAI()
# Create a thread for assistant
# You can add already existing thread id
thread = client.beta.threads.create()


def main():
    # Run event for threads
    run_event = threading.Event()
    run_event.set()

    # Create a thread for jarvis vision
    thread_for_jarvis_vis = threading.Thread(target=jarvis_vis,
                                                args=(run_event, ))
    thread_for_jarvis_vis.daemon = True
    thread_for_jarvis_vis.start()

    # # Create a thread for server
    # thread_for_server = threading.Thread(target=start_server,
    #                                         args=(run_event, ))
    # thread_for_server.daemon = True
    # thread_for_server.start()

    # # Create a thread for telebot
    # telebot_thread = threading.Thread(target=send_photo, args=(run_event, ))
    # telebot_thread.daemon = True
    # telebot_thread.start()

    # Recorder for a wakeup word
    recorder = PvRecorder(device_index=config.MICROPHONE_DEVICE_INDEX,
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
                        print(resp)
                        if "mute" in resp: mute()
                        if "unmute" in resp: unmute()
                        if "move" in resp: move()
                        if "wake_up" in resp: wake_up()
                        if "search_video" in resp:
                            Thread(target=search_video, args=(resp, )).start()

                        if "take_a_photo" in resp: 
                            take_photo()
                            say("Say cheese!")
          
                        if "find_place" in resp: 
                            Thread(target=find_place, args=(resp, )).start()

                        if "search_and_play_song" in resp:
                            Thread(target=search_and_play_song, args=(resp, )).start()
                    
                        if "generate_image" in resp:
                            Thread(say("It will take some time, please wait.")).start()
                            generate_image(resp)   

                        if "describe_img" in resp: 
                            res = describe_img("img/screenshot.jpg")
                            print(f"Jarvis: \033[95m{res}\033[0m")
                            say(res)
                        
                        add_message_to_thread(thread.id, " ")
                        res = get_answer(config.ASSISTANT_ID, thread)
                        print(f"Jarvis: \033[95m{res}\033[0m\n")
                        say(res)
       
            except KeyboardInterrupt:
                run_event.clear()
                recorder.stop()
                porcupine.delete()
                thread_for_jarvis_vis.join()
                thread_for_server.join()
                print("Goodbye!")
                break

            except openai.BadRequestError as e:
                print(f"An error occurred: {str(e)}")
                say("Sorry, im tired, i need to rest.")
                time.sleep(10)
            
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                say("Sorry, i dont understand you.")
                time.sleep(10)
            

def jarvis_vis(run_event):
    global take_photo_flag
    global send_photo_flag
    global init_time
    global MSG
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
            
            if fingers1 == [1, 0, 0, 0, 0]:
                MSG = "left"
            if fingers1 == [0, 0, 0, 0, 1]:
                MSG = "right"
            if fingers1 == [0, 1, 0, 0, 0]:
                MSG = "up"
            if fingers1 == [0, 1, 1, 1, 1]:
                MSG = "down"
            if fingers1 == [1, 1, 1, 1, 1]:
                MSG = "open"
            if fingers1 == [0, 0, 0, 0, 0]:
                MSG = "close"
            if fingers1 == [1, 1, 0, 0, 1]:
                MSG = "!DISCONNECT"
            

            if fingers1 == [0, 1, 1, 0, 0]:
                take_photo_flag = True
                init_time = time.time()
                MSG = "send photo"

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
                take_photo_flag = False
                send_photo_flag = True
                MSG = "send photo"


        # Display the image in a window
        cv2.imshow("Jarvis Eyes", img)

        # Keep the window open and update it for each frame; wait for 1 millisecond between frames
        if cv2.waitKey(1) & 0xff == ord('q'):
            return 0
    cv2.destroyAllWindows()


def handle_client_send(conn, addr):
    global MSG
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        if MSG:
            message = MSG.encode(config.FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(config.FORMAT)
            send_length += b" " * (config.HEADER - len(send_length))
            conn.send(send_length)
            conn.send(message)
            MSG = False

        if MSG == config.DISCONNECT_MESSAGE:
            connected = False
    conn.close()


def start_server(run_event):
    server.listen()
    print(f"[LISTENING] Server is listening on {config.SERVER}")
    while run_event.is_set():
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client_send, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def take_photo():
    global take_photo_flag
    global init_time
    global MSG
    take_photo_flag = True
    init_time = time.time()

def send_photo(run_event):
    global send_photo_flag

    bot = telebot.TeleBot(config.TELEGRAM_TOKEN)
    while run_event.is_set():

        if send_photo_flag: 
            with open('img/screenshot.jpg', 'rb') as photo:
                bot.send_photo('1815092465', photo)
                send_photo_flag = False

def move():
    global MSG
    MSG = "move"

if __name__ == "__main__":
    main()