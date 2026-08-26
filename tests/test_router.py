from core.router import classify_intent, route_command


commands = [
    "open chrome",
    "launch vscode",
    "start calculator",
    "minimize chrome",
    "maximize chrome",

    "open youtube",
    "open google",
    "open github",

    "play music",
    "play believer",
    "play kesariya",
    "play arijit singh",

    "pause music",
    "resume music",

    "increase volume",
    "decrease volume",

    "what time is it",
    "who are you",
    "do something random"
]


for command in commands:
    intent = classify_intent(command)
    print(f"{command!r} -> {intent}")


print("\n" + "=" * 50)
print("ROUTE TESTS")
print("=" * 50)

for command in commands:
    result = route_command(command)

    print(f"\nCommand: {command!r}")
    print(f"Intent: {result.intent}")
    print(f"Tool: {result.tool}")
    print(f"Parameters: {result.parameters}")
    print(f"Confidence: {result.confidence}")