import re
from enum import Enum
from dataclasses import dataclass
from tools.yt_ads import YouTubeAdTool

class Intent(Enum):
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    MINIMIZE_APPLICATION = "minimize_application"
    MAXIMIZE_APPLICATION = "maximize_application"
    OPEN_WEBSITE = "open_website"
    PLAY_MUSIC = "play_music"
    PAUSE_MUSIC = "pause_music"
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
    # MUSIC
    # ==============================

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

    if any(phrase in command for phrase in [
        "skip ad",
        "skip ads",
        "skip the ad",
        "skip advertisement",
        "skip advertisements"
    ]):
       return Intent.SKIP_AD


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

        Intent.OPEN_WEBSITE: "open_website",

        Intent.PLAY_MUSIC: "play_music",
        Intent.PAUSE_MUSIC: "pause_music",
        Intent.RESUME_MUSIC: "resume_music",

        Intent.VOLUME_UP: "volume_up",
        Intent.VOLUME_DOWN: "volume_down",
        Intent.SKIP_AD: "skip_ad",

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