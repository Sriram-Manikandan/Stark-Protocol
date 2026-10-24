# ULTRON: OFFLINE

A local voice-agent demo with three modes:

- **Jarvis** — a helpful assistant persona.
- **Ultron** — a skeptical, challenging persona.
- **Debate** — Jarvis and Ultron debate a spoken or typed topic, then a judge gives a verdict.

Chat requests go to the local Ollama API at `http://localhost:11434`. Speech uses the computer's installed voices via `pyttsx3`; speech recognition uses `faster-whisper` and the `tiny` model.

## Requirements

- Windows with Python 3.10 or newer
- [Ollama for Windows](https://ollama.com/download)
- The `gemma4:e4b` model downloaded in Ollama
- A microphone for voice input (optional; keyboard input is used if microphone setup fails)

## Setup in Git Bash

From this project directory:

```bash
python -m venv venv
source venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
ollama pull gemma4:e4b
```

Check that Ollama has the model and is serving its local API:

```bash
ollama list
curl http://localhost:11434/api/tags
```

The model list should include `gemma4:e4b`. Start the app with:

```bash
python main.py
```

Choose `1` for Jarvis, `2` for Ultron, `3` for debate, or `q` to quit. Say `menu` during a direct chat to return to the menu.

## First run and offline demo

The first speech-recognition setup may download the Whisper `tiny` model. Allow that download to finish before disconnecting from the internet. Ollama and the Gemma model must also be installed locally beforehand. After those are ready, the app's chat requests use the local Ollama server, and speech recognition can use its cached model.

If microphone dependencies or initialization fail, the app prints a warning and accepts typed input instead. If recording fails after startup, check Windows microphone permissions and the selected input device.

The app itself sends chat requests only to `localhost`. To disable Ollama's cloud features as an extra precaution, set `OLLAMA_NO_CLOUD=1` for the Ollama server process and restart that process. Setting the variable in a separate Git Bash window does not change an already-running Ollama server.

## Project files

- `main.py` — menu, direct-chat loop, and debate flow
- `brain.py` — local Ollama requests, text-to-speech, and microphone transcription
- `personas.py` — Jarvis, Ultron, and judge prompts
