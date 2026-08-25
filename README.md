# 🤖 ORION V1.0 — AI Voice Assistant

> **ORION is a Python-based voice assistant designed to interact with your computer through natural voice commands.**

ORION listens for a wake word, understands spoken commands, responds using natural AI-generated speech, automates browser actions, and can control music playback on YouTube.

The project is designed as a foundation for building a more advanced personal AI assistant capable of interacting with a computer through voice.

---

## ✨ Features

### 🎙️ Voice Recognition

* Continuously listens through the microphone.
* Uses speech recognition to convert voice into text.
* Supports **English (India)** speech recognition.
* Automatically calibrates the microphone for ambient noise.

### 🧠 Wake-Word System

ORION normally stays in sleep mode and waits for:

```text
"Orion"
```

or

```text
"Hey Orion"
```

Once activated, ORION enters active listening mode.

### 🔊 Natural AI Voice

ORION uses **Kokoro TTS** to generate natural-sounding speech.

* Voice: `af_heart`
* Sample rate: 24 kHz
* Streams generated audio directly to the output device.
* Audio is processed in chunks to reduce unnecessary memory usage.

### 🎵 YouTube Music Control

You can give commands such as:

```text
"Play Believer"
"Play Thinking of You"
"Play Inam"
```

ORION searches YouTube and opens the first matching video using Selenium browser automation.

ORION also uses a dedicated Chrome profile so browser state can be maintained locally.

### 🌐 Browser Automation

ORION can open commonly used websites through voice commands:

```text
"Open YouTube"
"Open Google"
"Open Udemy"
"Open ChatGPT"
```

### 🕐 Time Information

Ask:

```text
"What is the time?"
```

ORION responds with the current system time.

### 💬 Basic Conversational Commands

ORION can respond to commands such as:

```text
"Hello"
"How are you?"
"Who are you?"
```

### 😴 Sleep Mode

ORION can return to sleep mode when you say:

```text
"Go to sleep"
"Stop listening"
"Sleep"
```

### 🛡️ Error Handling

The assistant handles common situations including:

* No speech detected
* Speech not understood
* Speech recognition service errors
* Unexpected runtime errors
* Keyboard interruption

---

## 🛠️ Technologies Used

| Technology                    | Purpose                             |
| ----------------------------- | ----------------------------------- |
| **Python**                    | Core programming language           |
| **SpeechRecognition**         | Voice-to-text processing            |
| **Google Speech Recognition** | Speech recognition engine           |
| **Kokoro TTS**                | Natural voice generation            |
| **SoundDevice**               | Real-time audio playback            |
| **NumPy**                     | Audio data processing               |
| **Selenium**                  | Browser automation                  |
| **Chrome WebDriver**          | YouTube/browser interaction         |
| **PyWhatKit**                 | Web/automation utility              |
| **Git & GitHub**              | Version control and project hosting |

---

## 🏗️ How ORION Works

```text
                 ┌──────────────────┐
                 │      USER        │
                 │   Voice Command  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   MICROPHONE     │
                 │ Audio Input      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ SPEECH           │
                 │ RECOGNITION      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ ORION COMMAND    │
                 │ PROCESSOR        │
                 └────────┬─────────┘
                          │
             ┌────────────┼─────────────┐
             ▼            ▼             ▼
        Web Actions    Music Control   System Info
             │            │             │
             └────────────┼─────────────┘
                          ▼
                 ┌──────────────────┐
                 │   KOKORO TTS     │
                 │ Natural Response │
                 └────────┬─────────┘
                          │
                          ▼
                 🔊 ORION SPEAKS
```

---

## 📁 Project Structure

```text
orion-ai-assistant/
│
├── core/
│   └── router.py
│
├── main.py
├── test_voice.py
├── .gitignore
├── LICENSE
└── README.md
```

### Important

The following files are intentionally excluded from GitHub:

```text
.env
.venv/
__pycache__/
orion_chrome_profile/
*.wav
```

This prevents private credentials, local environments, browser session data, and generated audio files from being committed.

---

## 💻 Requirements

Before running ORION, make sure you have:

* Python 3.10+
* Google Chrome
* ChromeDriver/Selenium-compatible Chrome setup
* Working microphone
* Working speakers/headphones
* Internet connection for speech recognition and web-based actions

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/gaurrang24/orion-ai-assistant.git
```

### 2. Open the project

```bash
cd orion-ai-assistant
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Install dependencies

Install the required Python packages used by the project:

```bash
pip install numpy SpeechRecognition sounddevice selenium kokoro pywhatkit
```

If your environment requires additional audio dependencies, install them according to the package requirements.

---

## ▶️ Run ORION

Start the assistant with:

```bash
python main.py
```

ORION will calibrate the microphone and enter sleep mode.

You should see:

```text
ORION AI ASSISTANT

Orion is sleeping...
Say 'Orion' to wake me.
```

Say:

```text
"Orion"
```

and ORION will respond:

```text
"Yes, I'm listening."
```

You can then give a command.

---

## 🎤 Example Commands

| Voice Command       | Action                                 |
| ------------------- | -------------------------------------- |
| `Orion`             | Wake ORION                             |
| `Hello`             | Greeting                               |
| `Who are you?`      | ORION identifies itself                |
| `What is the time?` | Gives current time                     |
| `Play a song`       | Searches and opens the song on YouTube |
| `Open YouTube`      | Opens YouTube                          |
| `Open Google`       | Opens Google                           |
| `Open Udemy`        | Opens Udemy                            |
| `Open ChatGPT`      | Opens ChatGPT                          |
| `Go to sleep`       | Returns to sleep mode                  |
| `Stop listening`    | Returns to sleep mode                  |

---

## 🔐 Security

**Never upload your `.env` file or browser session/profile to GitHub.**

ORION's `.gitignore` is configured to exclude:

```text
.env
.venv/
__pycache__/
orion_chrome_profile/
*.wav
```

If you add API keys or other credentials in the future, keep them in environment variables rather than hard-coding them into the source code.

---

## 🚀 Future Development

ORION V1.0 is the foundation of a larger personal AI assistant.

Planned improvements include:

* 🧠 More advanced natural-language command understanding
* 💬 Conversational AI integration
* 🖥️ More computer-control capabilities
* 📂 File and application management
* 🔎 Intelligent web search
* 📅 Calendar and task management
* 🏠 Smart-device integration
* 👁️ Computer vision
* 🗣️ Improved voice recognition
* ⚡ Faster command execution
* 🧩 Modular skill/plugin architecture

---

## 🎯 Project Goal

The long-term goal of ORION is to create a **hands-free personal AI assistant** that can understand natural voice commands and interact with a computer in a useful and intelligent way.

Instead of manually navigating applications, websites, and tools, the user should eventually be able to communicate with the computer naturally through ORION.

---

## 📌 Current Version

**ORION V1.0**

Current focus:

> **Voice interaction + browser automation + YouTube music control + natural speech output**

---

## 👨‍💻 Developer

**Gaurang Rajput**

GitHub:

https://github.com/gaurrang24

Project:

https://github.com/gaurrang24/orion-ai-assistant

---

## 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.

---

## ⭐ Support the Project

If you find ORION interesting, consider giving the repository a ⭐ on GitHub.

Every star helps motivate further development of the project.

---

### ORION V1.0

**Listen. Understand. Act. Speak.**

