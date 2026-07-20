from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QBrush
import requests
import psutil
import datetime

from now_playing import get_current_song
from spotify_api import get_album_art_url


def get_battery():
    battery = psutil.sensors_battery()
    if battery:
        percent = int(battery.percent)
        charging = battery.power_plugged
        icon = "⚡" if charging else "🔋"
        return f"{icon} {percent}%"
    return ""


def get_time():
    return datetime.datetime.now().strftime("%I:%M %p").lstrip("0")


def extract_dominant_color(image_data):
    try:
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")
        img = img.resize((50, 50))

        pixels = list(img.getdata())

        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)

        return QColor(r, g, b)

    except Exception:
        return QColor(30, 30, 30)


class SongFetcher(QThread):
    song_ready = pyqtSignal(dict)

    def run(self):
        info = get_current_song()

        if info:
            self.song_ready.emit(info)
        else:
            self.song_ready.emit({})


class ArtFetcher(QThread):
    art_ready = pyqtSignal(bytes)

    def __init__(self, title, artist):
        super().__init__()
        self.title = title
        self.artist = artist

    def run(self):
        try:
            url = get_album_art_url(self.title, self.artist)

            if url:
                data = requests.get(url, timeout=5).content
                self.art_ready.emit(data)

        except Exception as e:
            print("Art fetch error:", e)


class SpotifyWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(380, 135)

        self.bg_color = QColor(20, 20, 20)
        self.target_color = QColor(20, 20, 20)

        self.pulse_value = 0
        self.pulse_direction = 1

        # Top Bar
        self.time_label = QLabel(get_time())
        self.time_label.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; background: transparent;"
        )

        self.battery_label = QLabel(get_battery())
        self.battery_label.setStyleSheet(
            "color: white; font-size: 13px; background: transparent;"
        )

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.time_label)
        top_layout.addStretch()
        top_layout.addWidget(self.battery_label)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Song Row
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(90, 90)
        self.cover_label.setStyleSheet(
            "background: transparent; border-radius: 6px;"
        )
        self.cover_label.setScaledContents(True)

        self.song_label = QLabel("No song playing")
        self.song_label.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; background: transparent;"
        )
        self.song_label.setWordWrap(True)

        self.artist_label = QLabel("—")
        self.artist_label.setStyleSheet(
            "color: #dddddd; font-size: 13px; background: transparent;"
        )

        info_layout = QVBoxLayout()
        info_layout.addWidget(self.song_label)
        info_layout.addWidget(self.artist_label)
        info_layout.setSpacing(4)

        song_layout = QHBoxLayout()
        song_layout.addWidget(self.cover_label)
        song_layout.addLayout(info_layout)
        song_layout.setContentsMargins(0, 0, 0, 0)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(song_layout)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        self.setLayout(main_layout)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width() - self.width(),
            screen.height() - self.height()
        )

        self.current_song = None
        self.song_fetcher = None
        self.art_fetcher = None
        self.current_art_data = None

        # Clock Timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)

        # Song Timer
        self.song_timer = QTimer()
        self.song_timer.timeout.connect(self.fetch_song)
        self.song_timer.start(1000)

        # Background Animation Timer
        self.bg_timer = QTimer()
        self.bg_timer.timeout.connect(self.animate_background)
        self.bg_timer.start(33)

    def animate_background(self):
        r = self.bg_color.red() + (
            self.target_color.red() - self.bg_color.red()
        ) // 20

        g = self.bg_color.green() + (
            self.target_color.green() - self.bg_color.green()
        ) // 20

        b = self.bg_color.blue() + (
            self.target_color.blue() - self.bg_color.blue()
        ) // 20

        self.bg_color = QColor(r, g, b)

        self.pulse_value += self.pulse_direction

        if self.pulse_value >= 40:
            self.pulse_direction = -1
        elif self.pulse_value <= 0:
            self.pulse_direction = 1

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        base = QColor(
            min(self.bg_color.red() // 3, 80),
            min(self.bg_color.green() // 3, 80),
            min(self.bg_color.blue() // 3, 80),
            200
        )

        glow = QColor(
            min(self.bg_color.red() + self.pulse_value, 255),
            min(self.bg_color.green() + self.pulse_value, 255),
            min(self.bg_color.blue() + self.pulse_value, 255),
            180
        )

        gradient = QLinearGradient(
            0, 0,
            self.width(),
            self.height()
        )

        gradient.setColorAt(0, base)
        gradient.setColorAt(1, glow)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    def update_clock(self):
        self.time_label.setText(get_time())
        self.battery_label.setText(get_battery())

    def fetch_song(self):
        if self.song_fetcher and self.song_fetcher.isRunning():
            return

        self.song_fetcher = SongFetcher()
        self.song_fetcher.song_ready.connect(self.on_song_ready)
        self.song_fetcher.start()

    def on_song_ready(self, info):
        if not info:
            self.hide()
            self.current_song = None
            return

        self.show()

        self.song_label.setText(info["title"])
        self.artist_label.setText(info["artist"])

        song_key = f"{info['title']}_{info['artist']}"

        if song_key != self.current_song:
            self.current_song = song_key

            if self.art_fetcher and self.art_fetcher.isRunning():
                self.art_fetcher.terminate()

            self.art_fetcher = ArtFetcher(
                info["title"],
                info["artist"]
            )

            self.art_fetcher.art_ready.connect(self.set_album_art)
            self.art_fetcher.start()

    def set_album_art(self, data):
        self.current_art_data = data

        pixmap = QPixmap()
        pixmap.loadFromData(data)

        self.cover_label.setPixmap(pixmap)

        color = extract_dominant_color(data)
        self.target_color = color