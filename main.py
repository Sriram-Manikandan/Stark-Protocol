from brain import chat, speak, listen
from personas import persona_msg

def _is_menu_command(text):
    command = text.strip().lower().rstrip(" .,!?:;")
    return command in {"menu", "back", "go back", "return to menu", "back to menu", "quit", "exit", "q"}

def direct_chat(persona):
    system = persona_msg(persona)
    history = []
    print(f"\n--- Talking to {persona.upper()} (say or type 'menu' or 'exit' to go back) ---")
    while True:
        user = listen()
        if _is_menu_command(user):
            print("Returning to the main menu.\n")
            return
        history.append({"role": "user", "content": user})
        reply = chat(system, history)
        history.append({"role": "assistant", "content": reply})
        speak(persona, reply)

while True:
    print("\n===== STARK DUAL-PROTOCOL: JARVIS & ULTRON =====  [1] Jarvis  [2] Ultron  [q] Quit")
    c = input("> ").strip()
    if c == "1": direct_chat("jarvis")
    elif c == "2": direct_chat("ultron")
    elif c.lower() == "q": break