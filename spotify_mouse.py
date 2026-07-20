import sys
import os
import threading
from widget import SpotifyWidget
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon

from main import start_controller

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")

print("Icon path:", ICON_PATH)
print("Icon exists:", os.path.exists(ICON_PATH))

tray = QSystemTrayIcon()
tray.setIcon(QIcon(ICON_PATH))
tray.setToolTip("Spotify Mouse Controller")

menu = QMenu()

show_action = QAction("Show Widget")
show_action.triggered.connect(lambda: widget.show())

hide_action = QAction("Hide Widget")
hide_action.triggered.connect(lambda: widget.hide())

exit_action = QAction("Exit")
exit_action.triggered.connect(app.quit)

menu.addAction(show_action)
menu.addAction(hide_action)
menu.addSeparator()
menu.addAction(exit_action)

tray.setContextMenu(menu)
tray.show()

threading.Thread(target=start_controller, daemon=True).start()

widget = SpotifyWidget()
widget.show()

sys.exit(app.exec())