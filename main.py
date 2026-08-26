import gc
import datetime
import webbrowser
import time
import urllib.parse
from core.router import route_command, Intent

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import numpy as np
import speech_recognition as sr
import sounddevice as sd
from kokoro import KPipeline

# ==================================================
# CHROME / YOUTUBE
# ==================================================

CHROME_PROFILE = r"C:\Users\prach\OneDrive\Desktop\orion v1.0\orion_chrome_profile"


def create_driver():
    print("Starting Chrome...")

    options = Options()
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")

    # Helps prevent some automation-related Chrome issues
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")

    new_driver = webdriver.Chrome(options=options)
    new_driver.get("https://www.youtube.com")

    time.sleep(3)

    print("Chrome ready.")
    return new_driver


driver = create_driver()

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

    try:
        generator = pipeline(text, voice=VOICE, speed=1.0)

        with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
            for _, _, audio in generator:
                # asarray avoids an extra copy if it's already float32
                stream.write(np.asarray(audio, dtype=np.float32))

    except Exception as e:
        # TTS failing should never crash the assistant
        print("TTS error:", e)

    finally:
        # Drop any lingering references and free the generator/chunks promptly
        try:
            del generator
        except NameError:
            pass
        gc.collect()


# ==================================================
# MUSIC
# ==================================================

def restart_driver():
    global driver

    print("Restarting Chrome session...")

    try:
        driver.quit()
    except Exception:
        pass

    time.sleep(2)
    driver = create_driver()


def driver_is_alive():
    global driver

    try:
        driver.current_url
        return True
    except Exception:
        return False


def play_music(song):
    global driver

    print(f"Playing: {song}")

    # ------------------------------------------
    # CHECK SELENIUM SESSION
    # ------------------------------------------

    if not driver_is_alive():
        print("Chrome session is dead.")
        restart_driver()

    try:
        # --------------------------------------
        # SEARCH YOUTUBE
        # --------------------------------------

        search_url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote(song)
        )

        print("Searching YouTube...")
        driver.get(search_url)

        # --------------------------------------
        # WAIT FOR SEARCH RESULTS
        # --------------------------------------

        wait = WebDriverWait(driver, 10)

        first_video = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "ytd-video-renderer a#video-title")
            )
        )

        # --------------------------------------
        # CLICK FIRST RESULT
        # --------------------------------------

        driver.execute_script("arguments[0].click();", first_video)

        print("Song opened successfully.")
        time.sleep(2)

    except Exception as e:

        print("YouTube error:", e)

        # --------------------------------------
        # IF SESSION DIED, RESTART CHROME
        # --------------------------------------

        if not driver_is_alive():
            print("Chrome disconnected.")
            restart_driver()
            speak("Chrome was disconnected. I restarted it. Please try again.")
        else:
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


def listen(timeout, phrase_time_limit):
    """
    Shared listen+recognize helper so audio buffers don't linger
    as separate variables across the main loop.

    Raises:
        sr.WaitTimeoutError   - no speech started within `timeout`
        sr.UnknownValueError  - speech was captured but not understood
        sr.RequestError       - the recognition service failed/unreachable
    """
    with microphone as source:
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

    try:
        text = recognizer.recognize_google(audio, language="en-IN").lower().strip()
    finally:
        # audio can hold several seconds of raw samples; release it explicitly
        del audio

    return text


# ==================================================
# COMMAND HANDLING
# ==================================================

SLEEP_PHRASES = ("go to sleep", "go sleep", "sleep", "stop listening", "stop")

def handle_command(command):
    """
    Route the user's command through router.py
    and execute the appropriate Orion action.
    """

    # ==================================================
    # SLEEP
    # ==================================================

    if command in SLEEP_PHRASES or any(
        p in command
        for p in ("go to sleep", "go sleep", "stop listening")
    ):
        speak("Going back to sleep.")
        return False

    # ==================================================
    # ROUTER
    # ==================================================

    result = route_command(command)

    print()
    print("========== ORION ROUTER ==========")
    print("Command:", command)
    print("Intent:", result.intent)
    print("Tool:", result.tool)
    print("Parameters:", result.parameters)
    print("Confidence:", result.confidence)
    print("==================================")
    print()

        # ==================================================
    # PLAY MUSIC
    # ==================================================

    if result.intent == Intent.PLAY_MUSIC:

        song = result.parameters.get("song")

        if song:
            play_music(song)
        else:
            speak("Which song should I play?")

    # ==================================================
    # PAUSE MUSIC
    # ==================================================

    elif result.intent == Intent.PAUSE_MUSIC:

        try:
            if driver_is_alive():

                driver.execute_script("""
                    const video = document.querySelector('video');

                    if (video) {
                        video.pause();
                        return true;
                    }

                    return false;
                """)

                speak("Music paused.")

            else:
                speak("Chrome is not available.")

        except Exception as e:
            print("Pause error:", e)
            speak("I couldn't pause the music.")

    # ==================================================
    # RESUME MUSIC
    # ==================================================

    elif result.intent == Intent.RESUME_MUSIC:

        try:
            if driver_is_alive():

                result_js = driver.execute_script("""
                    const video = document.querySelector('video');

                    if (video) {
                        video.play();
                        return true;
                    }

                    return false;
                """)

                if result_js:
                    speak("Music resumed.")
                else:
                    speak("I couldn't find the music player.")

            else:
                speak("Chrome is not available.")

        except Exception as e:
            print("Resume error:", e)
            speak("I couldn't resume the music.")

    
   
    # ==================================================
    # OPEN WEBSITE
    # ==================================================

    elif result.intent == Intent.OPEN_WEBSITE:

        website = result.parameters.get(
            "website", ""
        ).lower().strip()

        if "youtube" in website:

            speak("Opening YouTube.")
            webbrowser.open("https://www.youtube.com/")

        elif "google" in website:

            speak("Opening Google.")
            webbrowser.open("https://www.google.com")

        elif "github" in website:

            speak("Opening GitHub.")
            webbrowser.open("https://github.com/gaurrang24/orion-ai-assistant.git")

        else:

            speak(
                f"I don't know how to open {website} yet."
            )

    # ==================================================
    # TIME
    # ==================================================

    elif result.intent == Intent.TIME:

        current_time = datetime.datetime.now().strftime("%I:%M %p")

        speak(f"The time is {current_time}.")

    # ==================================================
    # CONVERSATION
    # ==================================================

    elif result.intent == Intent.CONVERSATION:

        if "who are you" in command:

            speak("I am Orion, your personal voice assistant.")

        elif "what can you do" in command:

            speak(
                "I can open websites, play music, control applications, "
                "and help you with various tasks."
            )

        elif command in ("hello", "hi"):

            speak("Hello. How can I help you?")

        else:

            speak("Hello. How can I help you?")

    # ==================================================
    # UNKNOWN
    # ==================================================

    elif result.intent == Intent.UNKNOWN:

        speak("Sorry, I don't know that command yet.")

    # ==================================================
    # OTHER INTENTS
    # ==================================================

    else:

        speak(
            f"I detected {result.intent.value}, "
            "but that function is not connected yet."
        )

    return True


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

WAKE_WORDS = ("orion", "hey orion")

# ==================================================
# MAIN LOOP
# ==================================================

while True:

    try:

        # ------------------------------------------
        # SLEEP MODE
        # ------------------------------------------

        print("Waiting for wake word...")

        try:
            command = listen(timeout=5, phrase_time_limit=3)
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print("Speech recognition error:", e)
            continue

        print("You said:", command)

        # ------------------------------------------
        # WAKE ORION
        # ------------------------------------------

        if command in WAKE_WORDS or any(w in command for w in WAKE_WORDS):

            speak("Yes, I'm listening.")
            time.sleep(2)  # let mic/speaker settle

            # ======================================
            # ACTIVE CONVERSATION MODE
            # ======================================

            while True:

                print("Listening for your command...")

                try:
                    command = listen(timeout=5, phrase_time_limit=3)
                    print("Command:", command)

                except sr.WaitTimeoutError:
                    print("No command detected.")
                    continue

                except sr.UnknownValueError:
                    print("I couldn't understand that.")
                    continue

                except sr.RequestError as e:
                    print("Speech recognition error:", e)
                    continue

                keep_going = handle_command(command)
                if not keep_going:
                    break

            # --------------------------------------
            # BACK TO SLEEP
            # --------------------------------------

            print()
            print("Orion is sleeping...")
            print("Say 'Orion' to wake me.")
            print()

            # Free anything accumulated during this wake cycle
            gc.collect()

    # ==================================================
    # ERROR HANDLING (outer loop safety net)
    # ==================================================

    except KeyboardInterrupt:
        print()
        print("Orion shutting down.")
        try:
            driver.quit()
        except Exception:
            pass
        break

    except Exception as e:
        print("Unexpected error:", e)