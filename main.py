import gc
import datetime
import webbrowser
import time
import threading

from core.router import route_command, Intent

from tools.youtube import YouTubeTool
from services.chrome import ChromeService
from tools import system_volume
from tools.yt_ads import YouTubeAdTool
from tools.windows_control import WindowsControlTool

import numpy as np
import speech_recognition as sr
import sounddevice as sd
from kokoro import KPipeline


# ==================================================
# UI HOOKS
# ==================================================
# main_window.py sets these two before calling start_orion().
# Keeping them as plain callables (not Qt signals) means this
# file stays UI-framework agnostic - main_window.py is the one
# that wraps them into thread-safe Qt signals.

on_status = None   # callable(status: str) -> "idle" | "active" | "listening" | "speaking"
on_message = None  # callable(text: str, role: str) -> role in ("user", "orion")


def _notify_status(status):
    if on_status:
        try:
            on_status(status)
        except Exception as e:
            print("UI status hook error:", e)


def _notify_message(text, role="orion"):
    if on_message:
        try:
            on_message(text, role)
        except Exception as e:
            print("UI message hook error:", e)


# ==================================================
# GLOBALS (populated by initialize(), not at import time)
# ==================================================

chrome = None
driver = None
youtube = None
youtube_ads = None
windows = None
pipeline = None
recognizer = None
microphone = None

VOICE = "af_heart"
SAMPLE_RATE = 24000

_initialized = False
_init_lock = threading.Lock()


def initialize():
    """
    Runs everything that used to sit at module level:
    Chrome/Selenium startup, TTS model load, and mic calibration.

    Import-time side effects freeze the GUI event loop, so this is
    now an explicit call made from the background thread that runs
    start_orion() - never from the main/UI thread.
    """
    global chrome, driver, youtube, youtube_ads, windows
    global pipeline, recognizer, microphone, _initialized

    with _init_lock:
        if _initialized:
            return

        print("Starting Orion Chrome...")
        chrome = ChromeService()
        driver = chrome.create_driver()
        youtube = YouTubeTool(chrome)
        youtube_ads = YouTubeAdTool(driver)
        windows = WindowsControlTool()

        print("Loading Orion's voice...")
        pipeline = KPipeline(lang_code="a")

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        microphone = sr.Microphone()

        print("Calibrating microphone...")
        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone ready.")

        _initialized = True


# ==================================================
# ORION TTS
# ==================================================


def speak(text):
    """
    Streams TTS audio directly to the output device chunk-by-chunk
    instead of buffering the whole utterance in memory.
    """
    print("Orion:", text)
    _notify_status("speaking")
    _notify_message(text, "orion")

    try:
        generator = pipeline(text, voice=VOICE, speed=1.0)

        with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
            for _, _, audio in generator:
                stream.write(np.asarray(audio, dtype=np.float32))

    except Exception as e:
        print("TTS error:", e)

    finally:
        try:
            del generator
        except NameError:
            pass
        gc.collect()


# ==================================================
# SPEECH RECOGNITION
# ==================================================


def listen(timeout, phrase_time_limit):
    with microphone as source:
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

    try:
        text = recognizer.recognize_google(audio, language="en-IN").lower().strip()
    finally:
        del audio

    return text


# ==================================================
# COMMAND HANDLING
# ==================================================

SLEEP_PHRASES = ("go to sleep", "go sleep", "sleep", "stop listening", "stop")


def confirm_action(message):
    speak(message)
    time.sleep(1)

    try:
        response = listen(timeout=8, phrase_time_limit=4)
        print("Confirmation:", response)

        positive_responses = ["yes", "yeah", "yep", "yes please", "sure", "okay", "ok", "do it", "confirm", "go ahead"]
        negative_responses = ["no", "nope", "cancel", "don't", "do not", "never mind", "never"]

        if response in positive_responses:
            return True
        if response in negative_responses:
            return False
        if any(word in response for word in ["yes", "sure", "go ahead", "do it"]):
            return True
        return False

    except sr.WaitTimeoutError:
        speak("I didn't hear a confirmation.")
        return False
    except sr.UnknownValueError:
        speak("I couldn't understand your confirmation.")
        return False
    except sr.RequestError as e:
        print("Confirmation speech error:", e)
        speak("I couldn't verify your confirmation.")
        return False


def handle_command(command):
    """Route the user's command through router.py and execute the appropriate Orion action."""

    if command in SLEEP_PHRASES or any(p in command for p in ("go to sleep", "go sleep", "stop listening")):
        speak("Going back to sleep.")
        return False

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

    if result.intent == Intent.PLAY_MUSIC:
        alive = chrome.is_alive()
        if not alive:
            chrome.restart()

        song = result.parameters.get("song")
        if song:
            if youtube.play(song):
                speak(f"Playing {song}.")
            else:
                speak("I couldn't play that song.")
        else:
            speak("Which song should I play?")

    elif result.intent == Intent.PAUSE_MUSIC:
        if not chrome.is_alive():
            chrome.restart()
        if youtube.pause():
            speak("Music paused.")
        else:
            speak("I couldn't pause the music.")

    elif result.intent == Intent.RESUME_MUSIC:
        if not chrome.is_alive():
            chrome.restart()
        if youtube.resume():
            speak("Music resumed.")
        else:
            speak("I couldn't resume the music.")

    elif result.intent == Intent.SKIP_AD:
        if not chrome.is_alive():
            chrome.restart()
        if youtube_ads.skip_ads():
            speak("Ad skipped.")
        else:
            speak("I couldn't find a skippable ad.")

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

    elif result.intent == Intent.TAKE_SCREENSHOT:
        try:
            path = windows.screenshot()
            if path:
                speak("Screenshot taken.")
                print(f"Screenshot saved to: {path}")
            else:
                speak("I couldn't take the screenshot.")
        except Exception as e:
            print("Screenshot error:", repr(e))
            speak("I couldn't take the screenshot.")

    elif result.intent == Intent.LOCK_COMPUTER:
        try:
            speak("Locking your computer.")
            windows.lock()
        except Exception as e:
            print("Lock error:", repr(e))
            speak("I couldn't lock the computer.")

    elif result.intent == Intent.RESTART_COMPUTER:
        confirmed = confirm_action("Are you sure you want to restart your computer?")
        if confirmed:
            speak("Restarting your computer.")
            windows.restart()
        else:
            speak("Restart cancelled.")

    elif result.intent == Intent.OPEN_WEBSITE:
        website = result.parameters.get("website", "").lower().strip()

        if "youtube" in website:
            speak("Opening YouTube.")
            webbrowser.open("https://www.youtube.com/")
        elif "google" in website:
            speak("Opening Google.")
            webbrowser.open("https://www.google.com")
        elif "amazon" in website:
            speak("Opening Amazon.")
            webbrowser.open("https://www.amazon.in/")
        elif "github" in website:
            speak("Opening GitHub.")
            webbrowser.open("https://github.com/gaurrang24/orion-ai-assistant.git")
        elif "google workspace" in website:
            speak("Opening Google Workspace.")
            webbrowser.open("https://workspace.google.com/")
        elif "myntra" in website:
            speak("Opening Myntra.")
            webbrowser.open("https://www.myntra.com/")
        elif "gmail" in website:
            speak("Opening Gmail.")
            webbrowser.open("https://mail.google.com/mail/u/0/#inbox")
        elif "google account" in website:
            speak("Opening Google Account.")
            webbrowser.open("https://myaccount.google.com/")
        else:
            speak(f"I don't know how to open {website} yet.")

    elif result.intent == Intent.TIME:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}.")

    elif result.intent == Intent.CONVERSATION:
        if "who are you" in command:
            speak("I am Orion, your personal voice assistant.")
        elif "what can you do" in command:
            speak("I can open websites, play music, control applications, and help you with various tasks.")
        elif command in ("hello", "hi"):
            speak("Hello. How can I help you?")
        else:
            speak("Hello. How can I help you?")

    elif result.intent == Intent.UNKNOWN:
        speak("Sorry, I don't know that command yet.")

    else:
        speak(f"I detected {result.intent.value}, but that function is not connected yet.")

    return True


# ==================================================
# ORION CONTROL
# ==================================================

stop_event = threading.Event()


def start_orion():
    """
    Start Orion's voice assistant loop. Call this from a background
    thread (e.g. a QThread) - never from the UI/main thread, since
    initialize() and listen() both block.
    """
    initialize()
    stop_event.clear()

    print()
    print("================================")
    print("        ORION AI ASSISTANT")
    print("================================")
    print()
    print("Orion is sleeping...")
    print("Say 'Orion' to wake me.")
    print()

    WAKE_WORDS = ("orion", "hey orion")

    while not stop_event.is_set():
        try:
            _notify_status("idle")
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

            if command in WAKE_WORDS or any(w in command for w in WAKE_WORDS):
                _notify_status("active")
                speak("Yes, I'm listening.")
                time.sleep(2)

                while not stop_event.is_set():
                    _notify_status("listening")
                    print("Listening for your command...")

                    try:
                        command = listen(timeout=5, phrase_time_limit=3)
                        print("Command:", command)
                        _notify_message(command, "user")
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

                if not stop_event.is_set():
                    print()
                    print("Orion is sleeping...")
                    print("Say 'Orion' to wake me.")
                    print()

                gc.collect()

        except Exception as e:
            print("Unexpected error:", e)

    print()
    print("Orion shutting down.")
    _notify_status("idle")

    try:
        chrome.stop()
    except Exception:
        pass


def stop_orion():
    stop_event.set()


if __name__ == "__main__":
    try:
        start_orion()
    except KeyboardInterrupt:
        stop_orion()   