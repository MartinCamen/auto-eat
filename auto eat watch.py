"""
auto_eat_watch.py - watches the hunger bar and eats only when it gets low.

auto_eat.py used a CLOCK: "eat every 5 minutes, no matter what".
This version uses EYES: it looks at one single pixel of the hunger bar,
and eats when that pixel stops being orange.

    sense   ->   decide    ->   act
    (look)      (hungry?)      (eat)

That loop is how robots, thermostats and self-driving cars work too!

WHAT THIS PROGRAM DOES TO YOUR COMPUTER (read this first!):
  - Every few seconds it takes a screenshot of ONE pixel. Nothing is saved.
  - It pretends to be your keyboard and mouse, just like auto_eat.py.
  - It listens for F7 (calibrate) and F8 (stop).
  - It does NOT go on the internet, save files, or install anything.

How to run:
  1. In a terminal:  pip install pynput pillow
  2. Then:           python auto_eat_watch.py
  3. Follow the calibration steps it prints.
"""

import platform
import threading
import time

from PIL import ImageGrab          # Pillow: lets us look at the screen
from pynput import keyboard, mouse

# =================== SETTINGS: change these! ===================

CHECK_EVERY_SECONDS = 2   # how often to look at the hunger bar
COOLDOWN_SECONDS = 8      # after eating, give the bar time to fill up
COLOR_TOLERANCE = 60      # how different the color must be to mean "empty"
MAX_FAILED_MEALS = 3      # give up if eating doesn't help (out of stew?)

CALIBRATE_KEY = keyboard.Key.f7
STOP_KEY = keyboard.Key.f8

# Same format as in auto_eat.py: (action, value, pause_after_in_seconds)
EAT_SEQUENCE = [
    ("press", "1", 0.3),      # select a food slot in the hotbar
    ("click", "left", 0.3),   # eat it
]

# ===============================================================

# Windows trick: if display scaling is e.g. 150%, the mouse position and
# the screenshot would disagree about where things are. This fixes that.
if platform.system() == "Windows":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

kb = keyboard.Controller()
ms = mouse.Controller()
stop_event = threading.Event()   # becomes True when F8 is pressed
calibrated = threading.Event()   # becomes True when F7 is pressed

watch_point = None   # (x, y) - the pixel on screen we keep an eye on
full_color = None    # (r, g, b) - what that pixel looks like when NOT hungry


def read_pixel(x, y):
    """Take a 1x1 pixel screenshot and return its color as (red, green, blue)."""
    image = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
    return image.getpixel((0, 0))[:3]


def color_distance(a, b):
    """How different are two colors? 0 = identical, 765 = black vs white."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def is_hungry():
    """The bar is 'empty' at our point if the color changed a lot."""
    return color_distance(read_pixel(*watch_point), full_color) > COLOR_TOLERANCE


def do_step(action, value):
    if action == "press":
        kb.press(value)
        time.sleep(0.05)
        kb.release(value)
    elif action == "type":
        kb.type(value)
    elif action == "click":
        button = mouse.Button.left if value == "left" else mouse.Button.right
        ms.click(button)


def eat():
    for action, value, pause in EAT_SEQUENCE:
        if stop_event.is_set():
            return
        do_step(action, value)
        time.sleep(pause)


def on_key_press(key):
    global watch_point, full_color
    if key == CALIBRATE_KEY:
        x, y = (int(v) for v in ms.position)
        watch_point = (x, y)
        full_color = read_pixel(x, y)
        print(f"  Got it! Watching pixel {watch_point}, 'full' color = {full_color}\n")
        calibrated.set()
    elif key == STOP_KEY:
        print("\nStop key pressed - stopping.")
        stop_event.set()
        calibrated.set()   # in case we're still waiting for calibration
        return False


def main():
    keyboard.Listener(on_press=on_key_press).start()

    print("CALIBRATION")
    print("  1. Make sure the hunger bar is full.")
    print("  2. Hover the mouse over the orange bar at the point where he")
    print("     should eat, e.g. one third from the left.")
    print("  3. Press F7.        (F8 stops the program at any time.)\n")

    calibrated.wait()
    if stop_event.is_set():
        return

    print("Watching the hunger bar... (click into the game now)\n")
    meals = 0
    failed_in_a_row = 0

    while not stop_event.is_set():
        if is_hungry():                                   # SENSE + DECIDE
            meals += 1
            print(f"[{time.strftime('%H:%M:%S')}] Hungry! Eating (meal #{meals})")
            eat()                                         # ACT
            if stop_event.wait(COOLDOWN_SECONDS):
                break

            # Check our own work: did eating actually help?
            if is_hungry():
                failed_in_a_row += 1
                print(f"   Still hungry ({failed_in_a_row}/{MAX_FAILED_MEALS})")
                if failed_in_a_row >= MAX_FAILED_MEALS:
                    print("   Eating isn't working. Out of food? Wrong window?")
                    print("   Stopping to be safe.")
                    break
            else:
                failed_in_a_row = 0
                print("   Full again!")

        stop_event.wait(CHECK_EVERY_SECONDS)

    print(f"Done! The character ate {meals} times. Bye!")


if __name__ == "__main__":
    main()
