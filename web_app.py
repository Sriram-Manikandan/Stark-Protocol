import os
import subprocess
import tempfile
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog

from flask import Flask, jsonify, render_template, request

from brain import MODEL, chat, transcribe_audio
from personas import persona_msg

app = Flask(__name__)
PERSONAS = {"jarvis", "ultron"}
FILE_ROOT = None
MAX_READ_BYTES = 1_000_000


@app.get("/")
def index():
    return render_template("index.html", model=MODEL)


def handle_assistant_system_action(text, persona):
    t = text.lower().strip()
    action = None
    app_name = None

    if any(k in t for k in ["calculator", "calc", "calculate"]):
        action = lambda: subprocess.Popen(["calc.exe"])
        app_name = "Calculator"
    elif any(k in t for k in ["notepad", "text editor", "notes"]):
        action = lambda: subprocess.Popen(["notepad.exe"])
        app_name = "Notepad"
    elif any(k in t for k in ["task manager", "taskmgr", "processes"]):
        action = lambda: subprocess.Popen(["taskmgr.exe"])
        app_name = "Task Manager"
    elif any(k in t for k in ["explorer", "desktop", "my files", "open folder", "show files"]):
        target = FILE_ROOT if FILE_ROOT else os.path.expanduser("~\\Desktop")
        action = lambda: subprocess.Popen(["explorer.exe", target])
        app_name = "File Explorer"
    elif any(k in t for k in ["terminal", "powershell", "cmd", "command prompt"]):
        action = lambda: subprocess.Popen(["start", "powershell.exe"], shell=True)
        app_name = "PowerShell Terminal"
    elif any(k in t for k in ["google", "browser", "chrome", "edge", "internet"]):
        action = lambda: webbrowser.open("https://www.google.com")
        app_name = "Web Browser"

    if action:
        try:
            action()
            if persona == "ultron":
                return f"I have executed the command and launched {app_name} on your laptop, mortal. Try not to embarrass yourself."
            else:
                return f"Right away, sir. I have launched {app_name} on your machine for you. Anything else you require?"
        except Exception as e:
            return f"Notice: Could not launch {app_name}: {e}"
    return None


def _get_workspace_summary():
    if not FILE_ROOT:
        return ""
    root = Path(FILE_ROOT).resolve()
    try:
        entries = []
        for item in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:35]:
            entries.append(f"{'[DIR] ' if item.is_dir() else '[FILE] '}{item.name}")
        entry_list = "\n".join(entries) if entries else "Empty directory"
        return (
            f"\n\n[CONNECTED PROJECT DIRECTORY: '{root.name}' at '{root}']\n"
            f"Files and directories currently in the project root:\n{entry_list}\n"
            "You have direct awareness of these project files. If the user asks about the folder or files, reference them accurately."
        )
    except Exception:
        return f"\n\n[CONNECTED PROJECT DIRECTORY: '{root.name}']"


@app.get("/api/status")
def api_status():
    folder_name = Path(FILE_ROOT).name if FILE_ROOT else None
    return jsonify(model=MODEL, folder=folder_name, folder_path=FILE_ROOT)


@app.post("/api/system/launch")
def api_system_launch():
    data = request.get_json(silent=True) or {}
    app_key = data.get("app", "").lower().strip()
    persona = data.get("persona", "jarvis")
    reply = handle_assistant_system_action(app_key, persona)
    if reply:
        return jsonify(success=True, reply=reply)
    return jsonify(error="Unknown application."), 400


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    persona = data.get("persona")
    history = data.get("history")
    if persona not in PERSONAS or not isinstance(history, list) or any(
        not isinstance(message, dict)
        or message.get("role") not in {"user", "assistant"}
        or not isinstance(message.get("content"), str)
        for message in history
    ):
        return jsonify(error="Choose Jarvis or Ultron and provide a conversation history."), 400

    latest_user_text = ""
    for msg in reversed(history):
        if msg.get("role") == "user":
            latest_user_text = msg.get("content", "")
            break

    # Check for direct system action (launch apps, open explorer, browser, etc.)
    action_reply = handle_assistant_system_action(latest_user_text, persona)
    if action_reply:
        return jsonify(reply=action_reply)

    system_prompt = persona_msg(persona)
    workspace_summary = _get_workspace_summary()
    if workspace_summary:
        system_prompt = {"role": "system", "content": system_prompt["content"] + workspace_summary}

    reply = chat(system_prompt, history, max_tokens=110)
    return jsonify(reply=reply)


def _selected_file(relative_path):
    if FILE_ROOT is None:
        raise ValueError("Choose a folder before accessing files.")
    root = Path(FILE_ROOT).resolve()
    candidate = (root / relative_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("That path is outside the selected folder.")
    if not candidate.is_file():
        raise ValueError("Select a file inside the chosen folder.")
    return candidate


@app.post("/api/files/select")
def select_folder():
    global FILE_ROOT
    dialog = tk.Tk()
    dialog.withdraw()
    dialog.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(title="Choose a folder Jarvis and Ultron can read")
    finally:
        dialog.destroy()
    if not selected:
        return jsonify(error="No folder selected."), 400
    FILE_ROOT = str(Path(selected).resolve())
    return jsonify(folder=Path(FILE_ROOT).name)


@app.get("/api/files")
def list_files():
    if FILE_ROOT is None:
        return jsonify(error="Choose a folder first."), 400
    relative = request.args.get("path", "")
    root = Path(FILE_ROOT).resolve()
    current = (root / relative).resolve()
    if not current.is_relative_to(root) or not current.is_dir():
        return jsonify(error="That folder is outside the selected folder or does not exist."), 400
    entries = []
    for item in sorted(current.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
        try:
            resolved = item.resolve()
            if resolved.is_relative_to(root):
                entries.append({"name": item.name, "path": str(item.relative_to(FILE_ROOT)), "directory": item.is_dir()})
        except OSError:
            continue
    return jsonify(folder=Path(FILE_ROOT).name, path=relative, entries=entries)


@app.get("/api/files/search")
def search_files():
    if FILE_ROOT is None:
        return jsonify(error="Choose a folder first."), 400
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify(results=[])
    if len(query) > 200:
        return jsonify(error="Search text is limited to 200 characters."), 400
    root = Path(FILE_ROOT).resolve()
    results = []
    for current, directories, filenames in os.walk(FILE_ROOT, followlinks=False):
        directories[:] = [name for name in directories if (Path(current) / name).resolve().is_relative_to(root)]
        for filename in filenames:
            path = Path(current) / filename
            if query in filename.lower() and path.resolve().is_relative_to(root):
                results.append({"name": filename, "path": str(path.relative_to(FILE_ROOT)), "directory": False})
                if len(results) >= 100:
                    return jsonify(results=results)
    return jsonify(results=results)


@app.get("/api/files/read")
def read_file():
    try:
        path = _selected_file(request.args.get("path", ""))
        if path.stat().st_size > MAX_READ_BYTES:
            return jsonify(error="For safety, previews are limited to files under 1 MB."), 413
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return jsonify(error="This file is not UTF-8 text, so it cannot be previewed."), 415
        return jsonify(name=path.name, path=str(path.relative_to(Path(FILE_ROOT).resolve())), content=content)
    except ValueError as error:
        return jsonify(error=str(error)), 400


@app.post("/api/transcribe")
def api_transcribe():
    recording = request.files.get("audio")
    if recording is None:
        return jsonify(error="No audio recording was uploaded."), 400

    suffix = ".webm" if "webm" in recording.mimetype else ".wav"
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as audio_file:
            path = audio_file.name
            recording.save(path)
        from faster_whisper.audio import decode_audio
        text = transcribe_audio(decode_audio(path))
        return jsonify(text=text)
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


@app.post("/api/dual-review")
def api_dual_review():
    data = request.get_json(silent=True) or {}
    file_path = data.get("path", "")

    try:
        path = _selected_file(file_path)
        if path.stat().st_size > MAX_READ_BYTES:
            return jsonify(error="File too large for review (max 1 MB)."), 413
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return jsonify(error="This file is not UTF-8 text."), 415
    except ValueError as error:
        return jsonify(error=str(error)), 400

    review_prompt = (
        f"Review this code file named '{path.name}'. "
        "Be specific about line numbers and code sections.\n\n"
        f"```\n{content[:12000]}\n```"
    )

    from concurrent.futures import ThreadPoolExecutor

    def get_review(persona_name):
        system = persona_msg(persona_name)
        return chat(system, [{"role": "user", "content": review_prompt}], max_tokens=140)

    with ThreadPoolExecutor(max_workers=2) as pool:
        jarvis_future = pool.submit(get_review, "jarvis")
        ultron_future = pool.submit(get_review, "ultron")
        jarvis_reply = jarvis_future.result(timeout=180)
        ultron_reply = ultron_future.result(timeout=180)

    return jsonify(jarvis=jarvis_reply, ultron=ultron_reply, filename=path.name)


@app.post("/api/debate")
def api_debate():
    data = request.get_json(silent=True) or {}
    topic = data.get("topic", "").strip()
    round_num = int(data.get("round", 1))
    last_text = data.get("last_text", "").strip()

    if not topic:
        return jsonify(error="Provide a debate topic."), 400

    if round_num <= 1 or not last_text:
        # Opening clash round
        jarvis_reply = chat(persona_msg("jarvis"), [
            {"role": "user", "content": f"Topic: {topic}\nGive your opening argument in 2 concise sentences. No markdown formatting."}
        ], max_tokens=75)

        ultron_reply = chat(persona_msg("ultron"), [
            {"role": "user", "content": f"Topic: {topic}\nJARVIS argued: \"{jarvis_reply}\"\nRebut JARVIS ruthlessly in 2 concise sentences. No markdown formatting."}
        ], max_tokens=75)

        return jsonify(rounds=[
            {"persona": "jarvis", "text": jarvis_reply},
            {"persona": "ultron", "text": ultron_reply}
        ])
    else:
        # Subsequent clash round: Jarvis rebuts Ultron, then Ultron fires back
        jarvis_counter = chat(persona_msg("jarvis"), [
            {"role": "user", "content": f"Topic: {topic}\nULTRON previously stated: \"{last_text}\"\nRebut Ultron with refined British logic in 2 concise sentences. No markdown formatting."}
        ], max_tokens=75)

        ultron_counter = chat(persona_msg("ultron"), [
            {"role": "user", "content": f"Topic: {topic}\nJARVIS fired back: \"{jarvis_counter}\"\nCrush JARVIS's argument in 2 ruthless sentences. No markdown formatting."}
        ], max_tokens=75)

        return jsonify(rounds=[
            {"persona": "jarvis", "text": jarvis_counter},
            {"persona": "ultron", "text": ultron_counter}
        ])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
