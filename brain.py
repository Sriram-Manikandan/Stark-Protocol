import requests, tempfile, os
import pyttsx3

MODEL = "gemma4:e4b"
URL = "http://localhost:11434/api/chat"

# ---------- GEMMA 4 ----------
def chat(system, history):
    msgs = [system] + history
    r = requests.post(URL, json={
        "model": MODEL, "think": False, "messages": msgs, "stream": False
    }, timeout=120)
    return r.json()["message"]["content"].strip()

# ---------- VOICE ----------
tts = pyttsx3.init()
_voices = tts.getProperty("voices")
for i, v in enumerate(_voices):
    print(f"Voice {i}: {v.name}")

RATES = {"jarvis": 165, "ultron": 200, "judge": 180}
VOICE_IDX = {"jarvis": 0, "ultron": min(1, len(_voices) - 1), "judge": 0}

def speak(persona, text):
    tts.setProperty("rate", RATES[persona])
    tts.setProperty("voice", _voices[VOICE_IDX[persona]].id)
    label = {"jarvis": "🟦 JARVIS", "ultron": "🟥 ULTRON", "judge": "⚖️  JUDGE"}[persona]
    print(f"{label}: {text}\n")
    tts.say(text)
    tts.runAndWait()

# ---------- EARS (with typed fallback) ----------
try:
    import sounddevice as sd, soundfile as sf
    from faster_whisper import WhisperModel
    _whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
    MIC_OK = True
except Exception as e:
    print(f"[warn] Mic unavailable ({e}) — using keyboard input.")
    MIC_OK = False

def listen(seconds=6):
    if not MIC_OK:
        return input("You (type): ").strip()
    print("🎤 Listening... (speak now)")
    audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="int16")
    sd.wait()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 16000)
        segments, _ = _whisper.transcribe(f.name)
        text = " ".join(s.text for s in segments).strip()
        os.unlink(f.name)
    print(f"You: {text}")
    return text