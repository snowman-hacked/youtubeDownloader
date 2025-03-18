import sys
import yt_dlp
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget,
    QProgressBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import QThread, Signal
from pytubefix import YouTube


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

            self.download_complete.emit(f"Video '{yt.title}' downloaded successfully in:\n{self.save_path}")
        except Exception as e:
            self.download_error.emit(f"Download failed: {str(e)}")

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        percent_complete = int((total_size - bytes_remaining) / total_size * 100)
        self.progress_update.emit(percent_complete)


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Video Search & Downloader")
        self.setGeometry(200, 100, 800, 600)

        self.layout = QVBoxLayout()

        # 검색 입력 필드
        self.label = QLabel("Enter search keyword:")
        self.layout.addWidget(self.label)

        self.search_input = QLineEdit()
        self.layout.addWidget(self.search_input)

        # 검색 버튼
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_youtube)
        self.layout.addWidget(self.search_button)

        # 검색 결과 리스트
        self.result_list = QListWidget()
        self.result_list.itemClicked.connect(self.download_video)
        self.layout.addWidget(self.result_list)

        # 다운로드 폴더 선택 버튼
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.folder_button)

        # 다운로드 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

        self.download_folder = None  # 다운로드 폴더 초기값 (선택되지 않음)

    def search_youtube(self):
        """ 유튜브에서 검색어를 기반으로 동영상을 검색하여 리스트에 표시 """
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Input Required", "Please enter a search keyword!")
            return

        self.result_list.clear()  # 기존 검색 결과 초기화

        # YouTube 검색 옵션 설정
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(keyword, download=False)

            # 검색 결과 확인
            if not info or 'entries' not in info or not info['entries']:
                QMessageBox.warning(self, "No Results", "No videos found for the given search query.")
                return

            print("검색 결과 개수:", len(info['entries']))  # 검색된 동영상 개수 출력

            # 검색 결과를 UI 리스트에 추가
            for entry in info['entries']:
                if 'title' in entry and 'url' in entry:
                    video_title = entry['title']
                    video_url = entry['url']
                    self.result_list.addItem(f"{video_title} ({video_url})")
                else:
                    print("검색 결과에서 title 또는 url 없음:", entry)  # 디버깅용

            QMessageBox.information(self, "Search Complete", "Search results loaded!")

        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"An error occurred while searching:\n{str(e)}")

    def select_folder(self):
        """ 사용자에게 다운로드 폴더를 선택하도록 요청 """
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder
            QMessageBox.information(self, "Folder Selected", f"Download folder set to:\n{folder}")

    def download_video(self, item):
        """ 사용자가 선택한 동영상을 다운로드 """
        if not self.download_folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a download folder first!")
            return

        # 리스트에서 선택한 동영상의 URL 추출
        video_info = item.text()
        video_url = video_info.split("(")[-1].strip(")")

        QMessageBox.information(self, "Download", f"Starting download: {video_url}")

        # 다운로드 실행
        self.download_thread = DownloadThread(video_url, self.download_folder)
        self.download_thread.progress_update.connect(self.progress_bar.setValue)
        self.download_thread.download_complete.connect(self.show_success_message)
        self.download_thread.download_error.connect(self.show_error_message)
        self.download_thread.start()

    def show_success_message(self, message):
        """ 다운로드 완료 메시지 """
        QMessageBox.information(self, "Download Complete", message)

    def show_error_message(self, message):
        """ 다운로드 오류 메시지 """
        QMessageBox.critical(self, "Error", message)


# 프로그램 실행 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())
