# STARK DUAL-PROTOCOL: JARVIS & ULTRON

A dual-core AI code review & debate assistant with two distinct personas:

- **Jarvis** — a helpful assistant persona.
- **Ultron** — a skeptical, challenging persona.

Chat requests go to the local Ollama API at `http://localhost:11434`. The browser interface uses browser speech synthesis for spoken replies; the terminal app uses Windows SAPI. Speech recognition uses local `faster-whisper` with the `base.en` model.

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

## Browser interface

Start the local web app from Git Bash:

```bash
python web_app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Allow microphone access in the browser to record a message; the recording is transcribed locally and placed in the message box for review before sending. Choose the microphone from the selector after granting access. Chat requests go to the local Ollama server. Replies can be read aloud using an installed browser voice; the app prefers a British English voice if available and changes pitch/rate for Ultron. Voice choices depend on voices installed on the computer and cannot guarantee a particular accent or sound.

The default chat model is `gemma4:e4b`. A smaller model may answer faster but can be less capable. To try the already-installed `gemma3:1b` model for one Git Bash session:

```bash
OLLAMA_MODEL=gemma3:1b python web_app.py
```

For the best answers, keep `gemma4:e4b` selected. Responses are no longer forced under 35 words, so more detailed replies can take longer to generate.

The browser microphone uses the browser's echo cancellation, noise suppression, and automatic gain control where supported. Local `base.en` transcription is more capable than `tiny`, but it may not match commercial services such as Wispr Flow, particularly with quiet or noisy microphone input. Speech recordings are processed by the local Python app.

The **CONNECT FOLDER** button opens a local Windows folder picker. Jarvis and Ultron can list folders, search filenames, and preview UTF-8 text files under the folder you select. Attach a preview as context by asking a question while the file is selected. This is read-only: the app does not modify or delete files, and previews are limited to 1 MB.

Check that Ollama has the model and is serving its local API:

```bash
ollama list
curl http://localhost:11434/api/tags
```

The model list should include `gemma4:e4b`. Start the app with:

```bash
python main.py
```

Choose `1` for Jarvis, `2` for Ultron, or `q` to quit. During a direct chat, say or type `menu`, `back`, or `exit` to return to the main menu. For voice input, press Enter to start recording, say the command, then press Enter again to stop recording and return to the menu.

## First run and offline demo

The first speech-recognition setup downloads the Whisper `base.en` model (about 150 MB). Allow that download to finish before disconnecting from the internet. Ollama and the Gemma model must also be installed locally beforehand. After those are ready, the app's chat requests use the local Ollama server, and speech recognition can use its cached model.

If microphone dependencies or initialization fail, the app prints a warning and accepts typed input instead. If recording fails after startup, check Windows microphone permissions and the selected input device.

The app itself sends chat requests only to `localhost`. To disable Ollama's cloud features as an extra precaution, set `OLLAMA_NO_CLOUD=1` for the Ollama server process and restart that process. Setting the variable in a separate Git Bash window does not change an already-running Ollama server.

## Project files

- `main.py` — terminal menu and direct-chat loop
- `brain.py` — local Ollama requests, text-to-speech, and microphone transcription
- `personas.py` — Jarvis and Ultron prompts
