import sys
import os
import webbrowser
import win32api
import win32event
import winerror
from widget import SpotifyWidget
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon

from main import start_controller
from startup import is_startup_enabled, set_startup, sync_startup
import ytmusic_bridge

# Only one copy may run: two mouse hooks would fire every command twice
instance_mutex = win32event.CreateMutex(None, False, "SpotifyMouse_SingleInstance")
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    sys.exit(0)

sync_startup()

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")

print("Icon path:", ICON_PATH)
print("Icon exists:", os.path.exists(ICON_PATH))

app.setWindowIcon(QIcon(ICON_PATH))

tray = QSystemTrayIcon()
tray.setIcon(QIcon(ICON_PATH))
tray.setToolTip("Spotify Mouse Controller")

menu = QMenu()

show_action = QAction("Show Widget")
show_action.triggered.connect(lambda: widget.user_show())

hide_action = QAction("Hide Widget")
hide_action.triggered.connect(lambda: widget.user_hide())

startup_action = QAction("Start with Windows")
startup_action.setCheckable(True)
startup_action.setChecked(is_startup_enabled())
startup_action.toggled.connect(set_startup)

# Opens the userscript in the default browser; a userscript manager
# (Violentmonkey/Tampermonkey) then offers to install it
ytmusic_action = QAction("Install YouTube Music Volume Script")
ytmusic_action.triggered.connect(lambda: webbrowser.open(ytmusic_bridge.SCRIPT_URL))

exit_action = QAction("Exit")
exit_action.triggered.connect(app.quit)

menu.addAction(show_action)
menu.addAction(hide_action)
menu.addSeparator()
menu.addAction(startup_action)
menu.addAction(ytmusic_action)
menu.addSeparator()
menu.addAction(exit_action)

tray.setContextMenu(menu)
tray.show()

widget = SpotifyWidget()
widget.show()

ytmusic_server = ytmusic_bridge.start()
mouse_listener = start_controller(on_volume=widget.volume_changed.emit)

sys.exit(app.exec())