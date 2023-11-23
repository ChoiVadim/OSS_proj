import time
import json

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pyautogui


# Volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)


def mute():
    volume.SetMute(1, None)
def unmute():
    volume.SetMute(0, None)

def search_and_play_song(name):
    args = json.loads(name["search_and_play_song"])

    try:
        # Open Chrome
        driver = webdriver.Chrome()

        # Open YouTube
        driver.get("https://www.youtube.com")

        # Find the search input and type the song name
        search_box = driver.find_element("name", "search_query")
        search_box.send_keys(args["name"])
        search_box.send_keys(Keys.RETURN)

        # Wait for search results to load
        time.sleep(5)

        # Click on the first video (assuming it's the top result)
        pyautogui.click(x=300, y=400)  # Adjust the coordinates based on your screen resolution

        # Wait for the video to load
        time.sleep(120)


    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.quit()

    