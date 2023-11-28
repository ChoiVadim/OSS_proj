import config
from openai_module import say

import time
import json
from threading import Thread
from multiprocessing import Process

import praw
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import folium
from selenium import webdriver
import pyautogui
from selenium.webdriver.common.keys import Keys
from pydub import AudioSegment
from pydub.playback import play

# Volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = interface.QueryInterface(IAudioEndpointVolume)


def mute():
    volume.SetMute(1, None)

def unmute():
    volume.SetMute(0, None)


def find_place(cord):
    cord = json.loads(cord["find_place"])["cord"]
    cord = cord.split(", ")
    mymap=folium.Map(cord, zoom_start=15)
    folium.Marker(cord, tooltip="Your place", icon=folium.Icon(color="red", icon="", prefix="fa" )
    ).add_to(mymap)

    mymap.show_in_browser()


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
        time.sleep(7)
        pyautogui.click(x=800, y=600)
        # Wait for the video to load
        time.sleep(120)


    except Exception as e:
        print(f"An error occurred: {str(e)}")
        driver.quit()


def wake_up():
    # Play 
    audio = AudioSegment.from_file("sound/acdc.mp3", format="mp3")
    process = Process(target=play, args=(audio,))    
    process.start()

    # Open Chrome
    driver = webdriver.Chrome()
    driver.get("https://www.reddit.com/r/programming/top/")

    reddit_parc()
    # Wait and close
    time.sleep(10)
    process.terminate()
    driver.close()


def reddit_parc():
    # Set up your Reddit API credentials
    reddit = praw.Reddit(client_id=config.reddit_client_id,
                        client_secret=config.reddit_client_secret,
                        user_agent=config.reddit_user_agent,
                        username=config.reddit_username,
                        password=config.reddit_password)

    # Choose the programming-related subreddit
    subreddit_name = 'programming'
    subreddit = reddit.subreddit(subreddit_name)
    
    # Fetch and print the top 10 hot submissions
    
    say("Here are the top 10 hot news about programming from Reddit for today")
    for submission in subreddit.hot(limit=10):
        say(submission.title)
        print(submission.title)
        print('-----')

def main():
    wake_up()

if __name__ == "__main__":
    main()