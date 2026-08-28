import re
from enum import Enum
from dataclasses import dataclass


from tools.yt_ads import YouTubeAdTool
#from tools.yt_ads import YouTubeAdTool
from tools.windows_control import WindowsControlTool

class Intent(Enum):
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    MINIMIZE_APPLICATION = "minimize_application"
    MAXIMIZE_APPLICATION = "maximize_application"
    LOCK_COMPUTER = "lock_computer"
    RESTART_COMPUTER = "restart_computer"
    SHUTDOWN_COMPUTER = "shutdown_computer"
    SLEEP_COMPUTER = "sleep_computer"
    TAKE_SCREENSHOT = "take_screenshot"
    OPEN_WEBSITE = "open_website"
    PLAY_MUSIC = "play_music"
    PAUSE_MUSIC = "pause_music"
    NEXT_MUSIC = "next_music"
    SKIP_AD = "skip_ad"
    RESUME_MUSIC = "resume_music"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    SET_VOLUME = "set_volume"
    TIME = "time"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"

@dataclass
class RouteResult:
    intent: Intent
    tool: str | None
    parameters: dict
    confidence: float

def normalize(command: str) -> str:
    command = command.lower().strip()

    if command.startswith("orion"):
        command = command[5:].strip(" ,")

    return command

def classify_intent(command: str) -> Intent:

        # ==============================
    # WINDOWS CONTROL
    # ==============================

    if any(phrase in command for phrase in [
        "lock computer",
        "lock my computer",
        "lock the computer",
        "lock pc",
        "lock my pc",
        "lock the pc",
        "lock my system",
        "lock system",
        "lock the system",
        "lock workstation",
        "lock my workstation",
        

    ]):
        return Intent.LOCK_COMPUTER

        # RESTART COMPUTER
    if any(phrase in command for phrase in [
        "restart computer",
        "restart my computer",
        "restart the computer",
        "restart pc",
        "restart my pc",
        "restart the pc",
        "restart my system",
        "restart system",
        "restart the system",
        "reboot computer",
        "reboot my computer",
        "reboot pc",
        "reboot my pc",
        "reboot system",
        "reboot my system",
        "reboot the computer",
        "reboot the pc"
    ]):
        return Intent.RESTART_COMPUTER

    if any(phrase in command for phrase in [
        "shutdown computer",
        "shutdown my computer",
        "shutdown the computer",
        "shutdown pc",
        "shutdown my pc",
        "shutdown the pc",
        "shut down computer",
        "shut down my computer",
        "shut down the computer",
        "shut down pc",
        "shut down my pc",
        "turn off computer",
        "turn off my computer",
        "turn off the computer",
        "turn off pc",
        "turn off my pc",
        "power off computer",
        "power off my computer",
        "power off pc",
        "power off my pc"
    ]):
        return Intent.SHUTDOWN_COMPUTER

    if any(phrase in command for phrase in [
        "sleep computer",
        "sleep my computer",
        "sleep the computer",
        "sleep pc",
        "sleep my pc",
        "sleep the pc",
        "put computer to sleep",
        "put my computer to sleep",
        "put the computer to sleep",
        "put pc to sleep",
        "put my pc to sleep",
        "put the pc to sleep",
        "make computer sleep",
        "make my computer sleep",
        "computer sleep"
    ]):
        return Intent.SLEEP_COMPUTER

    if any(phrase in command for phrase in [
        "take screenshot",
        "take a screenshot",
        "take the screenshot",
        "capture screenshot",
        "capture a screenshot",
        "capture the screen",
        "capture my screen",
        "take screen shot",
        "screen shot",
        "screenshot",
        "capture screen"
    ]):
        return Intent.TAKE_SCREENSHOT
    
    if any(phrase in command for phrase in [
            "skip ad",
            "skip ads",
            "skip the ad",
            "skip advertisement",
            "skip advertisements"
        ]):
           return Intent.SKIP_AD

    
    # ==============================
    # MUSIC
    # ==============================

    if any(phrase in command for phrase in [
        "next song",
        "next music",
        "play next",
        "skip song",
        "next",
        "skip this",
        "skip"
      ]):
      return Intent.NEXT_MUSIC

    if (
      "play music" in command
       or "play song" in command
       or command.startswith("play ")
       ):
         return Intent.PLAY_MUSIC

    if any(word in command for word in ["pause music", "pause song"]):
      return Intent.PAUSE_MUSIC

    if any(word in command for word in ["resume music", "resume song"]):
      return Intent.RESUME_MUSIC
   
    # ==============================
    # VOLUME
    # ==============================

    if any(word in command for word in [
        "increase volume",
        "volume up",
        "louder"
    ]):
        return Intent.VOLUME_UP

    if any(word in command for word in [
        "decrease volume",
        "volume down",
        "lower volume"
    ]):
        return Intent.VOLUME_DOWN
        # SET VOLUME
    if re.search(r"\b(?:set\s+)?(?:the\s+)?(?:volume|sound)\s+(?:to\s+)?\d{1,3}\s*%?", command):
        return Intent.SET_VOLUME

    


    # ==============================
    # TIME
    # ==============================

    if any(word in command for word in [
        "what time",
        "current time"
    ]):
        return Intent.TIME


    # ==============================
    # CONVERSATION
    # ==============================

    if (
        command in ["hello", "hi"]
        or any(phrase in command for phrase in [
            "who are you",
            "what can you do"
        ])
    ):
        return Intent.CONVERSATION


    # ==============================
    # APPLICATION CONTROL
    # ==============================

    if any(word in command for word in [
        "minimize",
        "minimise"
    ]):
        return Intent.MINIMIZE_APPLICATION

    if any(word in command for word in [
        "maximize",
        "maximise"
    ]):
        return Intent.MAXIMIZE_APPLICATION


    # ==============================
    # WEBSITES
    # ==============================

    if any(website in command for website in [
        "open youtube",
        "open google",
        "open github"
    ]):
        return Intent.OPEN_WEBSITE


    # ==============================
    # APPLICATIONS
    # ==============================

    if any(word in command for word in [
        "open",
        "launch",
        "start"
    ]):
        return Intent.OPEN_APPLICATION

    if any(word in command for word in [
        "close",
        "exit",
        "quit"
    ]):
        return Intent.CLOSE_APPLICATION


    # ==============================
    # UNKNOWN
    # ==============================

    return Intent.UNKNOWN

def extract_parameters(command: str, intent: Intent) -> dict:

    if intent == Intent.OPEN_APPLICATION:
        for word in ["open", "launch", "start"]:
            if command.startswith(word):
                application = command[len(word):].strip()
                return {"application": application}

    if intent == Intent.CLOSE_APPLICATION:
        for word in ["close", "exit", "quit"]:
            if command.startswith(word):
                application = command[len(word):].strip()
                return {"application": application}

    if intent == Intent.MINIMIZE_APPLICATION:
        for word in ["minimize", "minimise"]:
            if command.startswith(word):
                application = command[len(word):].strip()
                return {"application": application}

    if intent == Intent.MAXIMIZE_APPLICATION:
        for word in ["maximize", "maximise"]:
            if command.startswith(word):
                application = command[len(word):].strip()
                return {"application": application}

    if intent == Intent.OPEN_WEBSITE:
        website = command

        for word in ["open", "launch", "start"]:
            if website.startswith(word):
                website = website[len(word):].strip()
                break

        return {"website": website}

    if intent == Intent.PLAY_MUSIC:
       for word in ["play music", "play song", "play"]:
           if command.startswith(word):
              song = command[len(word):].strip()

              if song:
                  return {"song": song}

    if intent == Intent.SET_VOLUME:
        match = re.search(r"\b(\d{1,3})\s*%?", command)

        if match:
            percentage = int(match.group(1))

            # Keep volume between 0% and 100%
            percentage = max(0, min(100, percentage))

            return {
                "level": percentage / 100
            }

        return {}
    if intent == Intent.VOLUME_UP:
        match = re.search(r"\bby\s+(\d+)\b", command)

        if match:
            return {
                "direction": "up",
                "amount": int(match.group(1))
            }

        return {"direction": "up"}

    if intent == Intent.VOLUME_DOWN:
        match = re.search(r"\bby\s+(\d+)\b", command)

        if match:
            return {
                "direction": "down",
                "amount": int(match.group(1))
            }

        return {"direction": "down"}

    return {}

def route_command(command: str) -> RouteResult:

    command = normalize(command)
    intent = classify_intent(command)
    parameters = extract_parameters(command, intent)

    tool_map = {
        Intent.OPEN_APPLICATION: "open_application",
        Intent.CLOSE_APPLICATION: "close_application",
        Intent.MINIMIZE_APPLICATION: "minimize_application",
        Intent.MAXIMIZE_APPLICATION: "maximize_application",

        Intent.LOCK_COMPUTER: "lock_computer",
        Intent.RESTART_COMPUTER: "restart_computer",
        Intent.SHUTDOWN_COMPUTER: "shutdown_computer",
        Intent.SLEEP_COMPUTER: "sleep_computer",
        Intent.TAKE_SCREENSHOT: "take_screenshot",

        Intent.OPEN_WEBSITE: "open_website",

        Intent.PLAY_MUSIC: "play_music",
        Intent.PAUSE_MUSIC: "pause_music",
        Intent.RESUME_MUSIC: "resume_music",
        Intent.NEXT_MUSIC: "next_music",

        Intent.VOLUME_UP: "volume_up",
        Intent.VOLUME_DOWN: "volume_down",
        Intent.SKIP_AD: "skip_ad",
        Intent.SET_VOLUME: "set_volume",
        Intent.TIME: "get_time",

        Intent.CONVERSATION: "conversation",
    }

    tool = tool_map.get(intent)

    if intent == Intent.UNKNOWN:
        confidence = 0.0
    else:
        confidence = 1.0

    return RouteResult(
        intent=intent,
        tool=tool,
        parameters=parameters,
        confidence=confidence
    )