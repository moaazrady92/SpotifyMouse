from pynput import mouse
import queue
import threading
import time

from spotify_controller import (
    open_spotify,
    play_pause,
    next_track,
    previous_track,
    volume_up,
    volume_down,
    is_spotify_running,
    has_media_player
)

HOLD_TIME = 0.25

SIDE_BUTTONS = (mouse.Button.x1, mouse.Button.x2)

# pynput callbacks run inside a Windows low-level mouse hook. Windows holds
# back ALL mouse input until the hook returns, so any slow work done in a
# callback (scanning processes, sending keys) freezes the whole PC.
# The callbacks below only record state and queue commands; a worker thread
# does the actual work.
commands = queue.Queue()

press_times = {}
held_buttons = set()
scrolled_buttons = set()


def next_or_open():
    # Only open Spotify when nothing else (e.g. a browser) is playing media
    if has_media_player() or is_spotify_running():
        print("Next Track")
        next_track()
    else:
        print("Opening Spotify")
        open_spotify()


def run_commands():
    while True:
        label, action = commands.get()

        if label:
            print(label)

        try:
            action()
        except Exception as e:
            print("Command error:", e)


def on_click(x, y, button, pressed):
    if pressed:
        press_times[button] = time.monotonic()

        if button in SIDE_BUTTONS:
            held_buttons.add(button)
            scrolled_buttons.discard(button)
        return

    held_time = time.monotonic() - press_times.pop(button, time.monotonic())
    held_buttons.discard(button)

    # A side button held for volume scrolling shouldn't also skip/pause
    if button in scrolled_buttons:
        scrolled_buttons.discard(button)
        return

    # Mouse 4 / Next Track
    if button == mouse.Button.x1:
        if held_time >= HOLD_TIME:
            commands.put((None, next_or_open))

    # Mouse 5 / Play-Pause
    elif button == mouse.Button.x2:
        commands.put(("Play/Pause", play_pause))

    # Middle Click / Previous Track
    elif button == mouse.Button.middle:
        if held_time >= HOLD_TIME:
            commands.put(("Previous Track", previous_track))


def on_scroll(x, y, dx, dy):
    if not held_buttons:
        return

    scrolled_buttons.update(held_buttons)

    if dy > 0:
        commands.put(("Volume Up", volume_up))

    elif dy < 0:
        commands.put(("Volume Down", volume_down))


def start_controller():
    threading.Thread(target=run_commands, daemon=True).start()

    mouse_listener = mouse.Listener(
        on_click=on_click,
        on_scroll=on_scroll
    )
    mouse_listener.start()

    print("Spotify Mouse Controller Running")
    return mouse_listener
