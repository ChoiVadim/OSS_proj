import speech_recognition as sr
from pvrecorder import PvRecorder

from modules import config
from modules.openai_module import audio_to_text


def speech_to_text():
    r = sr.Recognizer()
    r.energy_threshold = 4000

    try:
            print("Listening...")
            with sr.Microphone() as source:
                audio = r.listen(source, timeout = 10)

            with open("sound/microphone-results.wav", "wb") as f:
                f.write(audio.get_wav_data())
            
            print("Audio record end. Transcribing...")
            transcript = audio_to_text("sound/microphone-results.wav")

            
        
    except Exception as e:
        transcript = False
        print("No audio detected!")

    return transcript


def main():
    recorder = PvRecorder(device_index=1, frame_length=config.porcupine.frame_length)
    recorder.start()
    print('Using device: %s' % recorder.selected_device)

    while True:
        pcm = recorder.read()
        keyword_index = config.porcupine.process(pcm)

        if keyword_index >= 0:
            recorder.stop()
            print("Yes, sir.")
            recorder.start()
            print(speech_to_text())

if __name__ == "__main__":
    main()