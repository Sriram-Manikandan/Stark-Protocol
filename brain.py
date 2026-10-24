import os, requests, sys
from xml.sax.saxutils import escape
import win32com.client  # installed with pyttsx3 (pywin32)

MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")
URL = "http://localhost:11434/api/chat"

# ---------- LOCAL OLLAMA ----------
def chat(system, history, max_tokens=110):
    msgs = [system] + history[-6:]
    r = requests.post(URL, json={
        "model": MODEL, "think": False, "messages": msgs, "stream": False,
        "keep_alive": "30m",
        "options": {
            "num_predict": max_tokens,
            "num_ctx": 1536,
            "num_thread": 6,
            "temperature": 0.7
        }
    }, timeout=90)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()

def _warmup():
    print("Warming up Gemma (one-time, ~10s)...")
    try:
        requests.post(URL, json={"model": MODEL, "think": False, "stream": False,
            "keep_alive": "30m", "messages": [{"role": "user", "content": "hi"}],
            "options": {"num_predict": 1, "num_ctx": 512, "num_thread": 6}}, timeout=180)
    except Exception as e:
        print("[warn] warmup failed:", e)
_warmup()

# ---------- VOICE (SAPI directly: Mark for Jarvis, David for Ultron) ----------
_sapi = win32com.client.Dispatch("SAPI.SpVoice")
_sv = _sapi.GetVoices()
_voice_names = []
for i in range(_sv.Count):
    description = _sv.Item(i).GetDescription()
    _voice_names.append(description)
    print(f"Voice {i}: {description}")

_mark_voice = next((i for i, name in enumerate(_voice_names) if "mark" in name.lower()), 0)
_david_voice = next((i for i, name in enumerate(_voice_names) if "david" in name.lower()), 0)

# (voice index, speed -10..10, pitch -10..10)
STYLE = {
    "jarvis": (_mark_voice, 0, 1),      # Mark: articulate assistant
    "ultron": (_david_voice, -2, -9),   # David: slower, deep sinister pitch
}

class _T:                      # stub so "from brain import tts" still works
    def stop(self): pass
tts = _T()

def speak(persona, text):
    idx, rate, pitch = STYLE[persona]
    label = {"jarvis": "🟦 JARVIS", "ultron": "🟥 ULTRON"}[persona]
    print(f"{label}: {text}\n")
    _sapi.Voice = _sv.Item(idx)
    _sapi.Speak(f'<rate absspeed="{rate}"/><pitch absmiddle="{pitch}"/>{escape(text)}', 8)

# ---------- EARS (push-to-talk + typed fallback) ----------
try:
    import numpy as np
    import sounddevice as sd
    from faster_whisper import WhisperModel
    _whisper = WhisperModel("base.en", device="cpu", compute_type="int8")
    MIC_OK = True
except Exception as e:
    print(f"[warn] Mic unavailable ({e}) — using keyboard input.")
    MIC_OK = False

def transcribe_audio(audio):
    if not MIC_OK:
        raise RuntimeError("Speech recognition is unavailable; install the voice dependencies.")
    audio = np.asarray(audio, dtype=np.float32).flatten()
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak == 0.0:
        return ""
    audio *= min(0.8 / peak, 12.0)
    segments, _ = _whisper.transcribe(
        audio,
        language="en",
        beam_size=5,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text for segment in segments).strip()

def listen():
    if not MIC_OK:
        return input("You (type): ").strip()
    SR = 16000
    frames = []
    def cb(indata, n, t, status):
        frames.append(indata.copy())
        level = float(np.abs(indata).mean())
        bars = int(min(level * 400, 30))
        sys.stdout.write("\r🎤 RECORDING " + "█" * bars + " " * (30 - bars) + "  (press ENTER to stop)")
        sys.stdout.flush()
    typed = input("\n🎤 Press ENTER to speak (or type your question and press ENTER): ").strip()
    if typed:
        return typed
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", callback=cb):
        input()
    print("\n⏳ Transcribing...")
    if not frames:
        return input("Heard nothing. Type it: ").strip()
    audio = np.concatenate(frames).flatten()
    text = transcribe_audio(audio)
    if not text:
        return input("Couldn't catch that. Type it: ").strip()
    print(f"You: {text}")
    return text