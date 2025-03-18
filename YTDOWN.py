import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QProgressBar, QMessageBox, QFileDialog, QHBoxLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QThread, Signal, Qt
from pytubefix import YouTube
from io import BytesIO

# YouTube Data API v3 키
YOUTUBE_API_KEY = "AIzaSyDNfKj_lEypRW--r1SEsMcew4xM_uxymdo"

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

        # 검색어 입력 필드
        self.label = QLabel("Enter search keyword:")
        self.layout.addWidget(self.label)

        self.search_input = QLineEdit()
        self.layout.addWidget(self.search_input)

        # 검색 버튼
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_youtube)
        self.layout.addWidget(self.search_button)

        # 검색 결과 테이블 (썸네일, 제목, URL)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Thumbnail", "Title", "URL"])
        self.result_table.setColumnWidth(0, 120)  # 썸네일 크기 조정
        self.result_table.setColumnWidth(1, 400)  # 제목 크기 조정
        self.result_table.setColumnWidth(2, 250)  # URL 크기 조정
        self.result_table.cellClicked.connect(self.download_video)  # 셀 클릭 시 다운로드 실행
        self.layout.addWidget(self.result_table)

        # 페이지 네비게이션 버튼
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.navigation_layout)

        # 다운로드 폴더 선택 버튼
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.folder_button)

        # 다운로드 진행 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

        self.download_folder = None  # 다운로드 폴더 초기값
        self.current_page = 1  # 현재 페이지 번호
        self.next_page_token = None  # 다음 페이지 토큰
        self.prev_page_token = None  # 이전 페이지 토큰

    def search_youtube(self):
        """ YouTube Data API를 사용하여 검색 수행 """
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Input Required", "Please enter a search keyword!")
            return

        self.result_table.setRowCount(0)  # 기존 검색 결과 초기화
        self.current_page = 1
        self.next_page_token = None
        self.prev_page_token = None
        self.load_search_results(keyword)

    def load_search_results(self, keyword, page_token=None):
        """ YouTube Data API를 사용하여 검색 결과 로드 """
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={keyword}&type=video&maxResults=10&key={YOUTUBE_API_KEY}"
        if page_token:
            url += f"&pageToken={page_token}"

        try:
            response = requests.get(url)
            data = response.json()

            if "items" not in data:
                QMessageBox.warning(self, "No Results", "No videos found for the given search query.")
                return

            self.next_page_token = data.get("nextPageToken")
            self.prev_page_token = data.get("prevPageToken")

            for idx, item in enumerate(data["items"]):
                video_id = item["id"]["videoId"]
                video_title = item["snippet"]["title"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                thumbnail_url = item["snippet"]["thumbnails"]["default"]["url"]

                self.result_table.insertRow(idx)  # 새로운 행 추가

                # 썸네일 로드 및 추가
                thumbnail_label = QLabel()
                pixmap = self.load_thumbnail(thumbnail_url)
                thumbnail_label.setPixmap(pixmap.scaled(100, 75, Qt.KeepAspectRatio))
                self.result_table.setCellWidget(idx, 0, thumbnail_label)

                # 제목 추가
                title_item = QTableWidgetItem(video_title)
                self.result_table.setItem(idx, 1, title_item)

                # URL 추가
                url_item = QTableWidgetItem(video_url)
                self.result_table.setItem(idx, 2, url_item)

            QMessageBox.information(self, "Search Complete", "Search results loaded!")

        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"An error occurred while searching:\n{str(e)}")

    def load_thumbnail(self, url):
        """ 썸네일 이미지를 다운로드하여 QPixmap으로 변환 """
        response = requests.get(url)
        image = QPixmap()
        image.loadFromData(BytesIO(response.content).read())
        return image

    def select_folder(self):
        """ 사용자에게 다운로드 폴더를 선택하도록 요청 """
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder
            QMessageBox.information(self, "Folder Selected", f"Download folder set to:\n{folder}")

    def download_video(self, row, column):
        """ 사용자가 선택한 동영상을 다운로드 """
        if column != 2:  # URL 클릭한 경우만 다운로드
            return

        if not self.download_folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a download folder first!")
            return

        video_url = self.result_table.item(row, 2).text()  # 선택한 행의 URL 가져오기

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

    def next_page(self):
        """ 다음 페이지로 이동 """
        if self.next_page_token:
            self.current_page += 1
            self.load_search_results(self.search_input.text().strip(), self.next_page_token)

    def prev_page(self):
        """ 이전 페이지로 이동 """
        if self.prev_page_token:
            self.current_page -= 1
            self.load_search_results(self.search_input.text().strip(), self.prev_page_token)


# 프로그램 실행 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())