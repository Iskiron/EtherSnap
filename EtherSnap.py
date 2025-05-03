import sys
import os
import subprocess
import pyperclip
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QHBoxLayout,
    QProgressBar,
    QCheckBox,
)
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class DownloadThread(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal()

    def __init__(self, cmd, env):
        super().__init__()
        self.cmd = cmd
        self.env = env
        self.process = None

    def run(self):
        CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
        self.process = subprocess.Popen(
            self.cmd,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NO_WINDOW,
            universal_newlines=True,
        )

        for line in self.process.stdout:
            self.progress.emit(line.strip())

        self.done.emit()

    def stop(self):
        if self.process:
            self.process.terminate()


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("EtherSnap - YouTube Downloader")
        self.setFixedSize(550, 400)
        self.setWindowIcon(QIcon(self.resource_path("icon.png")))

        self.setStyleSheet("background-color: #ffe1be;")

        layout = QVBoxLayout()

        # URL label and input
        self.label = QLabel("Enter YouTube URL:")
        self.label.setFont(QFont("Arial", 10))
        layout.addWidget(self.label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://youtube.com/...")
        self.url_input.setFont(QFont("Arial", 10))
        layout.addWidget(self.url_input)

        # Paste button
        self.paste_btn = QPushButton("Paste from Clipboard")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        self.paste_btn.setStyleSheet(
            "border-radius: 8px; padding: 6px; background-color: #FF8C42; color: white;"
        )
        layout.addWidget(self.paste_btn)

        # Quality selection
        quality_layout = QHBoxLayout()
        self.quality_label = QLabel("Select Video Quality:")
        self.quality_box = QComboBox()
        self.quality_box.addItems(["best", "720p", "480p", "360p"])
        quality_layout.addWidget(self.quality_label)
        quality_layout.addWidget(self.quality_box)
        layout.addLayout(quality_layout)

        # Playlist toggle
        self.playlist_checkbox = QCheckBox("Download as Playlist")
        layout.addWidget(self.playlist_checkbox)

        # Download location
        self.location_btn = QPushButton("Choose Download Folder")
        self.location_btn.clicked.connect(self.choose_folder)
        self.location_btn.setStyleSheet(
            "border-radius: 8px; padding: 6px; background-color: #FF8C42; color: white;"
        )
        layout.addWidget(self.location_btn)
        self.download_folder = "."

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status = QLabel("")
        self.status.setFont(QFont("Arial", 9))
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)

        # Download buttons
        self.video_btn = QPushButton("Download Video")
        self.video_btn.clicked.connect(self.download_video)
        self.video_btn.setStyleSheet(
            "border-radius: 8px; padding: 8px; background-color: #F25C54; color: white;"
        )
        layout.addWidget(self.video_btn)

        self.audio_btn = QPushButton("Download Audio (MP3)")
        self.audio_btn.clicked.connect(self.download_audio)
        self.audio_btn.setStyleSheet(
            "border-radius: 8px; padding: 8px; background-color: #F25C54; color: white;"
        )
        layout.addWidget(self.audio_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel Download")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)
        self.ffmpeg_path = self.resource_path("ffmpeg.exe")
        self.worker = None

    def paste_from_clipboard(self):
        self.url_input.setText(pyperclip.paste())

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder
            self.status.setText(f"Download folder: {folder}")

    def get_quality_option(self):
        quality = self.quality_box.currentText()
        if quality == "best":
            return []
        return ["-f", f"bestvideo[height<={quality[:-1]}]+bestaudio/best"]

    def run_command(self, cmd):
        env = os.environ.copy()
        env["PATH"] = f"{os.path.dirname(self.ffmpeg_path)};{env['PATH']}"

        self.worker = DownloadThread(cmd, env)
        self.worker.progress.connect(self.update_progress)
        self.worker.done.connect(self.download_complete)
        self.worker.start()
        self.cancel_btn.setEnabled(True)

    def download_video(self):
        url = self.url_input.text()
        if url:
            self.status.setText("Downloading video...")
            QApplication.processEvents()
            cmd = ["yt-dlp", *self.get_quality_option()]
            if self.playlist_checkbox.isChecked():
                cmd.append("--yes-playlist")
            else:
                cmd.append("--no-playlist")
            cmd += ["-o", f"{self.download_folder}/%(title)s.%(ext)s", url]
            self.run_command(cmd)

    def download_audio(self):
        url = self.url_input.text()
        if url:
            self.status.setText("Downloading audio...")
            QApplication.processEvents()
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3"]
            if self.playlist_checkbox.isChecked():
                cmd.append("--yes-playlist")
            else:
                cmd.append("--no-playlist")
            cmd += ["-o", f"{self.download_folder}/%(title)s.%(ext)s", url]
            self.run_command(cmd)

    def update_progress(self, line):
        if "[download]" in line and "%" in line:
            parts = line.split()
            for part in parts:
                if "%" in part:
                    try:
                        percent = float(part.strip("%"))
                        self.progress_bar.setValue(int(percent))
                    except ValueError:
                        pass
        self.status.setText(line)

    def download_complete(self):
        self.status.setText("Download complete.")
        self.progress_bar.setValue(100)
        self.cancel_btn.setEnabled(False)

    def cancel_download(self):
        if self.worker:
            self.worker.stop()
            self.worker.terminate()
            self.status.setText("Download canceled.")
            self.cancel_btn.setEnabled(False)

    def resource_path(self, relative_path):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())
