from brain import chat, speak, listen
from personas import persona_msg

def direct_chat(persona):
    system = persona_msg(persona)
    history = []
    print(f"\n--- Talking to {persona.upper()} (say 'menu' to go back) ---")
    while True:
        user = listen()
        if user.lower() in ("menu", "quit", "exit"):
            return
        history.append({"role": "user", "content": user})
        reply = chat(system, history)
        history.append({"role": "assistant", "content": reply})
        speak(persona, reply)

def debate():
    print("\n--- DEBATE MODE: JARVIS vs ULTRON ---")
    question = listen()
    transcript = []
    jarvis_sys, ultron_sys, judge_sys = persona_msg("jarvis"), persona_msg("ultron"), persona_msg("judge")

    history = [{"role": "user", "content": question}]
    r = chat(jarvis_sys, history); transcript.append(("jarvis", r)); speak("jarvis", r)

    for rnd in range(2):
        history = [{"role": "user", "content":
            f"Debate topic: {question}\nJARVIS argued: {transcript[-1][1] if transcript[-1][0]=='jarvis' else ''}\n"
            f"Your turn — attack his position."}]
        r = chat(ultron_sys, history); transcript.append(("ultron", r)); speak("ultron", r)

        history = [{"role": "user", "content":
            f"Debate topic: {question}\nULTRON just said: {r}\nDefend your position or concede gracefully."}]
        r = chat(jarvis_sys, history); transcript.append(("jarvis", r)); speak("jarvis", r)

    debatelog = "\n".join(f"{p.upper()}: {t}" for p, t in transcript)
    verdict = chat(judge_sys, [{"role": "user", "content":
        f"Topic: {question}\n\n{debatelog}\n\nWho won?"}])
    speak("judge", verdict)

while True:
    print("\n===== ULTRON: OFFLINE =====  [1] Jarvis  [2] Ultron  [3] DEBATE  [q] Quit")
    c = input("> ").strip()
    if c == "1": direct_chat("jarvis")
    elif c == "2": direct_chat("ultron")
    elif c == "3": debate()
    elif c.lower() == "q": break