from pynput import mouse
import time

from spotify_controller import (
    open_spotify,
    play_pause,
    next_track,
    previous_track,
    volume_up,
    volume_down,
    is_spotify_running
)

mouse4_held = False
mouse5_held = False

press_times = {}
HOLD_TIME = 0.25


def on_click(x, y, button, pressed):
    global mouse4_held
    global mouse5_held

    # Record press time for hold detection
    if pressed:
        press_times[button] = time.time()
    # Mouse 4 / Next Track
    if button == mouse.Button.x1:

        if pressed:
            mouse4_held = True

        else:
            mouse4_held = False

            held_time = time.time() - press_times.get(button, time.time())

            if held_time >= HOLD_TIME:

                if is_spotify_running():
                    print("Next Track")
                    next_track()
                else:
                    print("Opening Spotify")
                    open_spotify()

    # Mouse 5 / Play-Pause
    elif button == mouse.Button.x2:

        if pressed:
            mouse5_held = True

        else:
            mouse5_held = False
            print("Play/Pause")
            play_pause()

    # Middle Click / Previous Track
    elif button == mouse.Button.middle:

        if not pressed:

            held_time = time.time() - press_times.get(button, time.time())

            if held_time >= HOLD_TIME:
                print("Previous Track")
                previous_track()


def on_scroll(x, y, dx, dy):
    if not (mouse4_held or mouse5_held):
        return

    if dy > 0:
        print("Volume Up")
        volume_up()

    elif dy < 0:
        print("Volume Down")
        volume_down()


mouse_listener = mouse.Listener(
    on_click=on_click,
    on_scroll=on_scroll
)

def start_controller():
    mouse_listener.start()
    print("Spotify Mouse Controller Running")