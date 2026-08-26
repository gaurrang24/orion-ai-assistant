import gc
import datetime
import webbrowser
import time

from core.router import route_command, Intent

from tools.youtube import YouTubeTool
from services.chrome import ChromeService
from tools import system_volume
from tools.yt_ads import YouTubeAdTool

import numpy as np
import speech_recognition as sr
import sounddevice as sd
from kokoro import KPipeline


# ==================================================
# CHROME / YOUTUBE
# ==================================================

chrome = ChromeService()
driver = chrome.create_driver()
youtube = YouTubeTool(chrome)
youtube_ads = YouTubeAdTool(driver)

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

        if not chrome.is_alive():
            chrome.restart()

        song = result.parameters.get("song")

        if song:

            if youtube.play(song):
                speak(f"Playing {song}.")
            else:
                speak("I couldn't play that song.")

        else:
            speak("Which song should I play?")

    # ==================================================
    # PAUSE MUSIC
    # ==================================================

    elif result.intent == Intent.PAUSE_MUSIC:

        if not chrome.is_alive():
            chrome.restart()

        if youtube.pause():
            speak("Music paused.")
        else:
            speak("I couldn't pause the music.")

    # ==================================================
    # RESUME MUSIC
    # ==================================================

    elif result.intent == Intent.RESUME_MUSIC:

        if not chrome.is_alive():
            chrome.restart()

        if youtube.resume():
            speak("Music resumed.")
        else:
            speak("I couldn't resume the music.")


        # ==================================================
    # SKIP YOUTUBE ADS
    # ==================================================

    elif result.intent == Intent.SKIP_AD:

        if not chrome.is_alive():
            chrome.restart()

        if youtube_ads.skip_ads():
            speak("Ad skipped.")
        else:
            speak("I couldn't find a skippable ad.")
    #volume control

    elif result.intent == Intent.VOLUME_UP:
        try:
            system_volume.volume_up()
            speak("Volume increased.")

        except Exception as e:
            print("Volume UP error:", repr(e))
            speak("I couldn't change the volume.")

   
    elif result.intent == Intent.VOLUME_DOWN:
        try:
            system_volume.volume_down()
            speak("Volume decreased.")

        except Exception as e:
            print("Volume DOWN error:", repr(e))
            speak("I couldn't change the volume.")


    elif result.intent == Intent.SET_VOLUME:
        try:
           level = float(result.parameters.get("level", 0.5))
           system_volume.set_system_volume(level)
           speak(f"Volume set to {int(level*100)} percent.")

        except Exception as e:
            print("Volume SET error:", repr(e))
            speak("I couldn't set the volume.")

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
            webbrowser.open(
                "https://github.com/gaurrang24/orion-ai-assistant.git"
            )

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
            chrome.stop()
        except Exception:
            pass
        break

    except Exception as e:
        print("Unexpected error:", e)