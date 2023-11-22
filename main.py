import threading
from time import time

import cv2
import cvzone
import telebot
from pvrecorder import PvRecorder

import config
from face_det_module import FaceDetector
from hand_track_module import HandDetector
from config import porcupine
from speech_to_text import speech_to_text
from openai_module import (generate_image, vision, audio_to_text, say, 
                            submit_message, wait_on_run, get_response, 
                            pretty_print)

send_photo_flag = False

def main():
    # generate_image("Iron man suit with a blue and red color scheme")
    # text = vision("img/screenshot.jpg")
    # text = listen("sound/test.mp3")

    # Recorder for a wakeup word
    recorder = PvRecorder(device_index=1, frame_length=config.porcupine.frame_length)
    recorder.start()
    print('Using device: %s' % recorder.selected_device)

    ltc = time() - 1000

    while True:
        try:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                recorder.stop()
                # text_to_speech("Yes, sir!", "yes_sir.mp3")
                say("Yes, sir!")
                recorder.start()
                ltc = time()
                
            while time() - ltc <= 15:
                msg = speech_to_text()
                if msg:
                    print(f"\nHuman: \033[94m{msg}\033[0m")

                    # Add a msg to openai thread
                    run = submit_message(config.ASSISTANT_ID, config.THREAD_ID, msg)
                    wait_on_run(run, config.THREAD_ID)
                    response = get_response(config.THREAD_ID)
                    pretty_print(response)
                    say(response.data[0].content[0].text.value)

        except KeyboardInterrupt:
            # th.join()
            porcupine.delete()
            break


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
                # ---- Get Data  ---- #
                center = bbox["center"]
                x, y, w, h = bbox['bbox']
                score = int(bbox['score'][0] * 100)

                # ---- Draw Data  ---- #
                cv2.circle(img, center, 5, (255, 0, 255), cv2.FILLED)
                cvzone.putTextRect(img, f'{score}%', (x, y - 10))
                cvzone.cornerRect(img, (x, y, w, h))

        # Check if any hands are detected
        if hands:
            # Information for the first hand detected
            hand1 = hands[0]  # Get the first hand detected
            lmList1 = hand1["lmList"]  # List of 21 landmarks for the first hand
            bbox1 = hand1["bbox"]  # Bounding box around the first hand (x,y,w,h coordinates)
            center1 = hand1['center']  # Center coordinates of the first hand
            handType1 = hand1["type"]  # Type of the first hand ("Left" or "Right")

            # Count the number of fingers up for the first hand
            fingers1 = detector_hand.fingersUp(hand1)
            
            if fingers1 == [0, 0, 0, 0, 0]:
                print("Yes, sir!")
                # threading.Thread(target=play_audio, args=("sound/yes_sir.mp3", )).start()

            if fingers1 == [0, 1, 1, 0, 0]:
                take_photo_flag = True
                init_time = time.time()


            # Check if a second hand is detected
            if len(hands) == 2:
                # Information for the second hand
                hand2 = hands[1]
                lmList2 = hand2["lmList"]
                bbox2 = hand2["bbox"]
                center2 = hand2['center']
                handType2 = hand2["type"]

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