import gc
import datetime
import webbrowser
import time
import urllib.parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import numpy as np
import speech_recognition as sr
import sounddevice as sd
from kokoro import KPipeline
import pywhatkit

# ==================================================
# CHROME / YOUTUBE PROFILE
# ==================================================

chrome_options = Options()

chrome_options.add_argument(
    r"--user-data-dir=C:\Users\prach\OneDrive\Desktop\orion v1.0\orion_chrome_profile"
)

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.youtube.com")
time.sleep(3)

# ==================================================
# ORION TTS
# ==================================================

print("Loading Orion's voice...")

pipeline = KPipeline(lang_code="a")

VOICE = "af_heart"
SAMPLE_RATE = 24000


def speak(text):
    """
    Streams TTS audio directly to the output device chunk-by-chunk
    instead of buffering the whole utterance in memory.

    Old approach: audio_chunks = [] -> np.concatenate() -> sd.play()
        This holds the full audio TWICE in RAM (the list of chunks +
        the concatenated array) before playback even starts.

    New approach: write each chunk to an open OutputStream as it's
        generated. Peak memory is just one chunk at a time, and audio
        starts playing sooner too.
    """
    print("Orion:", text)

    generator = pipeline(text, voice=VOICE, speed=1.0)

    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        for _, _, audio in generator:
            # astype(..., copy=False) avoids an extra copy if it's already float32
            stream.write(np.asarray(audio, dtype=np.float32))

    # Drop any lingering references and free the generator/chunks promptly
    del generator
    gc.collect()

# ==================================================
# MUSIC
# ==================================================

def play_music(song):
    print(f"Playing: {song}")
    speak(f"Playing {song}")

    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(song)

    driver.get(search_url)

    time.sleep(4)

    try:
        # Find the first video result
        first_video = driver.find_element(
            By.CSS_SELECTOR,
            "ytd-video-renderer a#video-title"
        )

        first_video.click()

        print("Song opened successfully.")

        time.sleep(5)

    except Exception as e:
        print("Could not find the song:", e)
        speak("I couldn't find that song.")

# ==================================================
# SPEECH RECOGNITION
# ==================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8

microphone = sr.Microphone()  # created once, reused everywhere


# ==================================================
# MICROPHONE CALIBRATION
# ==================================================

print("Calibrating microphone...")

with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)

print("Microphone ready.")


# ==================================================
# ORION START
# ==================================================

print()
print("================================")
print("        ORION AI ASSISTANT    ")
print("================================")
print()
print("Orion is sleeping...")
print("Say 'Orion' to wake me.")
print()


def listen(timeout, phrase_time_limit):
    """Shared listen+recognize helper so audio buffers don't linger
    as separate variables across the main loop."""
    with microphone as source:
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

    text = recognizer.recognize_google(audio, language="en-IN").lower().strip()

    # audio can hold several seconds of raw samples; release it explicitly
    del audio
    return text

# ==================================================
# MAIN LOOP
# ==================================================

while True:

    try:

        # ------------------------------------------
        # SLEEP MODE
        # ------------------------------------------

        print("😴 Waiting for wake word...")
        command = listen(timeout=10, phrase_time_limit=4)

        print("You said:", command)


        # ------------------------------------------
        # WAKE ORION
        # ------------------------------------------

        if command in ["orion", "hey orion"]:

            speak("Yes, I'm listening.")
            # Give the speaker/microphone time to settle
          
            # ======================================
            # ACTIVE CONVERSATION MODE
            # ======================================

            while True:

                print("🎤 Listening for your command...")

                try:
                    command = listen(
                        timeout=10,
                        phrase_time_limit=8
                    )

                    print("Command:", command)

                except sr.WaitTimeoutError:
                    print("No command detected.")
                    continue

                # --------------------------------------
                # GO BACK TO SLEEP
                # --------------------------------------

                if (
                    "go to sleep" in command
                    or "go sleep" in command
                    or command == "sleep"
                    or "stop listening" in command
                ):
                    speak("Going back to sleep.")
                    break

            # --------------------------------------
            # COMMANDS
            # --------------------------------------

                if "hello" in command:
                    speak("Hello. How can I help you?")

                elif "how are you" in command:
                    speak("I'm doing great. Thank you for asking.")

                elif "who are you" in command:
                    speak("I am Orion, your personal voice assistant.")

                elif "time" in command:
                    current_time = datetime.datetime.now().strftime("%I:%M %p")
                    speak(f"The time is {current_time}.")

                elif command.startswith("play "):
                   song = command[5:].strip()

                   if song:
                       play_music(song)
                   else:
                       speak("Which song should I play?")

                elif "open youtube" in command:
                    speak("Opening YouTube.")
                    webbrowser.open("https://www.youtube.com/")

                elif "open google" in command:
                    speak("Opening Google.")
                    webbrowser.open("https://www.google.com")

                elif "open udemy" in command:
                    speak("Opening Udemy.")
                    webbrowser.open("https://www.udemy.com/course/100-days-of-code/learn/lecture/23544648#overview")

                elif "open google" in command:
                    speak("Opening Google.")
                    webbrowser.open("https://www.google.com")

                elif "open chatgpt" in command:
                    speak("Opening ChatGPT.")
                    webbrowser.open("https://chatgpt.com")

                elif "stop" in command or "go to sleep" in command:
                    speak("Going back to sleep.")
 
                else:
                    speak("Sorry, I don't know that command yet.")


            # --------------------------------------
            # BACK TO SLEEP
            # --------------------------------------

            print()
            print("😴 Orion is sleeping...")
            print("Say 'Orion' to wake me.")
            print()

            # Free anything accumulated during this wake cycle
            gc.collect()


    # ==================================================
    # ERROR HANDLING
    # ==================================================

    except sr.WaitTimeoutError:
        print("No speech detected.")

    except sr.UnknownValueError:
        print("I couldn't understand that.")

    except sr.RequestError as e:
        print("Speech recognition error:", e)

    except KeyboardInterrupt:
        print()
        print("Orion shutting down.")
        break

    except Exception as e:
        print("Unexpected error:", e)