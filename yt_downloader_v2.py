import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, 
    QFileDialog, QProgressBar, QMessageBox
)
from PySide6.QtCore import QThread, Signal
from pytubefix import YouTube
from pytubefix.cli import on_progress


# 비동기 YouTube 다운로드를 위한 QThread
class DownloadThread(QThread):
    progress_update = Signal(int)
    download_complete = Signal(str)
    download_error = Signal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            yt = YouTube(self.url, on_progress_callback=self.progress_callback)
            ys = yt.streams.get_highest_resolution()
            ys.download(self.save_path)
            self.download_complete.emit(f"Video '{yt.title}' has been downloaded successfully.")
        except Exception as e:
            self.download_error.emit(str(e))

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        percent_complete = int((total_size - bytes_remaining) / total_size * 100)
        self.progress_update.emit(percent_complete)


# UI 클래스
class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 400, 200)

        # 레이아웃 생성
        self.layout = QVBoxLayout()

        self.label = QLabel("Enter YouTube URL:") # 라벨 추가
        self.layout.addWidget(self.label)

        self.url_input = QLineEdit() # URL 입력창 생성
        self.layout.addWidget(self.url_input)

        self.download_button = QPushButton("Download") # 다운로드 버튼 추가
        self.download_button.clicked.connect(self.start_download) # 버튼 클릭 이벤트
        self.layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar() # 다운로드 진행바
        self.progress_bar.setValue(0) # 초기값 0
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout) # 적용 함수

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Required", "Please enter a valid URL!")
            return

        save_path = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if not save_path:
            QMessageBox.warning(self, "Warning", "Download folder not selected.")
            return

        # 다운로드 스레드 실행
        self.download_thread = DownloadThread(url, save_path)
        self.download_thread.progress_update.connect(self.progress_bar.setValue)
        self.download_thread.download_complete.connect(self.show_success_message)
        self.download_thread.download_error.connect(self.show_error_message)
        self.download_thread.start()

    def show_success_message(self, message):
        QMessageBox.information(self, "Download Complete", message)

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)


# 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())
