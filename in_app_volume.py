import time

import comtypes
import comtypes.client
import psutil
import win32gui
import win32process

try:
    from comtypes.gen import UIAutomationClient as UIA
except ImportError:
    comtypes.client.GetModule("UIAutomationCore.dll")
    from comtypes.gen import UIAutomationClient as UIA

# Moves a player's own volume slider (e.g. the one in Spotify's bottom
# bar) through Windows UI Automation, the accessibility API screen readers
# use. Only works for apps whose slider accepts values that way: Spotify's
# does; web pages' sliders (YouTube Music in a browser) don't.

# exe -> accessible names of its volume slider (lowercase)
SLIDER_NAMES = {
    "spotify.exe": {"change volume"},
}

_automation = None
_sliders = {}
_last_set = {}


def supports(exe):
    return exe in SLIDER_NAMES


def _get_automation():
    global _automation
    if _automation is None:
        _automation = comtypes.client.CreateObject(
            UIA.CUIAutomation, interface=UIA.IUIAutomation
        )
    return _automation


def _app_windows(exe):
    windows = []

    def check(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
            return
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if psutil.Process(pid).name().lower() == exe:
                windows.append(hwnd)
        except Exception:
            pass

    win32gui.EnumWindows(check, None)
    return windows


def _range_value(element):
    pattern = element.GetCurrentPattern(UIA.UIA_RangeValuePatternId)
    return pattern.QueryInterface(UIA.IUIAutomationRangeValuePattern)


def _find_slider(exe):
    automation = _get_automation()
    is_slider = automation.CreatePropertyCondition(
        UIA.UIA_ControlTypePropertyId, UIA.UIA_SliderControlTypeId
    )

    for hwnd in _app_windows(exe):
        try:
            window = automation.ElementFromHandle(hwnd)
            found = window.FindAll(UIA.TreeScope_Descendants, is_slider)
        except comtypes.COMError:
            continue

        for i in range(found.Length):
            element = found.GetElement(i)
            try:
                if (element.CurrentName or "").lower() in SLIDER_NAMES[exe]:
                    return _range_value(element)
            except comtypes.COMError:
                pass

    return None


def _slider(exe):
    # Finding the slider takes ~1s, so reuse it while it's still alive
    slider = _sliders.get(exe)
    if slider is not None:
        try:
            slider.CurrentValue
            return slider
        except comtypes.COMError:
            pass

    slider = _find_slider(exe)
    _sliders[exe] = slider
    return slider


def change_volume(exe, direction):
    """Move the app's own volume slider one step up (direction > 0) or
    down. Returns the new level in percent, or None if the slider can't
    be reached (e.g. the app's window is closed to the tray)."""
    try:
        slider = _slider(exe)
        if slider is None:
            return None

        low, high = slider.CurrentMinimum, slider.CurrentMaximum
        step = slider.CurrentSmallChange or (high - low) / 10

        # The app applies a new value a moment after SetValue, so reading
        # it straight back is stale; during quick scrolling, build on the
        # value we last set instead
        last_value, last_time = _last_set.get(exe, (None, 0))
        if last_value is not None and time.monotonic() - last_time < 1:
            current = last_value
        else:
            current = slider.CurrentValue

        value = current + (step if direction > 0 else -step)
        value = round(min(max(value, low), high), 4)

        slider.SetValue(value)
        _last_set[exe] = (value, time.monotonic())
        return round((value - low) / (high - low) * 100)

    except comtypes.COMError as e:
        print("In-app volume error:", e)
        _sliders.pop(exe, None)
        _last_set.pop(exe, None)
        return None
