"""
auto_eat.py - presses an "eat" key sequence every few minutes, so the
game character doesn't starve while you're away.

WHAT THIS PROGRAM DOES TO YOUR COMPUTER (read this first!):
  - It pretends to be your keyboard and mouse ("simulated input").
    The computer can't tell the difference between this and real key presses,
    so it will type into WHATEVER window is active. Keep the game focused!
  - It listens for one key (F8) so you can stop it at any time.
  - It does NOT read your files, go on the internet, or install anything.
    You can check that yourself: everything it does is in this file.

How to run:
  1. Install Python from https://www.python.org
  2. In a terminal:  pip install pynput
  3. Then:           python auto_eat.py
"""

import threading
import time

from pynput import keyboard, mouse

# =================== SETTINGS: change these! ===================

INTERVAL_MINUTES = 5        # how often the character should eat
START_DELAY_SECONDS = 5     # time you get to click into the game window
STOP_KEY = keyboard.Key.f8  # press this key to stop the program

# The "eat" sequence. Each step is: (action, value, pause_after_in_seconds)
#   "press" -> tap one key, e.g. "e" or keyboard.Key.enter
#   "type"  -> type a whole word, e.g. "eat"
#   "click" -> click the mouse where it currently is: "left" or "right"
EAT_SEQUENCE = [
    ("press", "e", 0.3),
    ("press", "1", 0.3),
    ("click", "left", 0.3),
    # ("type", "eat", 0.2),
    # ("press", keyboard.Key.enter, 0.2),
]

# ===============================================================

kb = keyboard.Controller()   # our "fake keyboard"
ms = mouse.Controller()      # our "fake mouse"
stop_event = threading.Event()  # a flag that becomes True when F8 is pressed


def do_step(action, value):
    """Perform one step of the sequence."""
    if action == "press":
        kb.press(value)
        time.sleep(0.05)     # hold the key briefly, like a human would
        kb.release(value)
    elif action == "type":
        kb.type(value)
    elif action == "click":
        button = mouse.Button.left if value == "left" else mouse.Button.right
        ms.click(button)
    else:
        print(f"  Unknown action '{action}' - skipping it")


def eat():
    """Run the whole eat sequence once."""
    for action, value, pause in EAT_SEQUENCE:
        if stop_event.is_set():
            return
        do_step(action, value)
        time.sleep(pause)


def on_key_press(key):
    """Called every time ANY key is pressed. We only care about the stop key."""
    if key == STOP_KEY:
        print("\nStop key pressed - stopping.")
        stop_event.set()
        return False  # returning False stops the key listener


def main():
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    print(f"Starting in {START_DELAY_SECONDS} seconds - click into the game now!")
    print("Press F8 at any time to stop.\n")

    # wait() returns True if the stop flag got set while waiting
    if stop_event.wait(START_DELAY_SECONDS):
        return

    meals = 0
    while not stop_event.is_set():
        meals += 1
        print(f"[{time.strftime('%H:%M:%S')}] Eating (meal #{meals})")
        eat()
        print(f"   next meal in {INTERVAL_MINUTES} min...")
        if stop_event.wait(INTERVAL_MINUTES * 60):
            break

    print(f"Done! The character ate {meals} times. Bye!")


if __name__ == "__main__":
    main()
