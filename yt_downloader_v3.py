# yt_dlp 를 사용한 검색 결과 가져오기
# 다운로드 폴더 사용자 선택 가능하게 하기

import sys
import yt_dlp  # YouTube 검색을 수행하기 위한 라이브러리
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QListWidget,
    QProgressBar, QMessageBox, QFileDialog
)
from PySide6.QtCore import QThread, Signal
from pytubefix import YouTube  # YouTube 동영상 다운로드를 위한 라이브러리


# 다운로드를 비동기적으로 실행하기 위한 QThread 클래스 정의
class DownloadThread(QThread):
    # 다운로드 진행 상태 및 완료 메시지를 보내는 Signal 정의
    progress_update = Signal(int)
    download_complete = Signal(str)
    download_error = Signal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url  # 다운로드할 유튜브 동영상 URL
        self.save_path = save_path  # 다운로드할 파일이 저장될 폴더 경로

    def run(self):
        try:
            # YouTube 객체 생성 및 진행 상황 콜백 함수 설정
            yt = YouTube(self.url, on_progress_callback=self.progress_callback)
            
            # 최고 화질의 스트림 가져오기
            ys = yt.streams.get_highest_resolution()

            # 다운로드 실행
            ys.download(self.save_path)

            # 다운로드 완료 메시지 전송
            self.download_complete.emit(f"Video '{yt.title}' downloaded successfully in:\n{self.save_path}")
        except Exception as e:
            # 오류 발생 시 오류 메시지 전송
            self.download_error.emit(f"Download failed: {str(e)}")

    def progress_callback(self, stream, chunk, bytes_remaining):
        """ 다운로드 진행률을 계산하여 Signal로 전달 """
        total_size = stream.filesize
        percent_complete = int((total_size - bytes_remaining) / total_size * 100)
        self.progress_update.emit(percent_complete)


# YouTube 검색 및 다운로드를 수행하는 메인 UI 클래스
class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        # 윈도우 설정
        self.setWindowTitle("YouTube Video Search & Downloader")
        self.setGeometry(200, 100, 800, 600)  # 창의 위치 및 크기 설정

        # 세로 방향 레이아웃 생성
        self.layout = QVBoxLayout()

        # 검색어 입력 필드 및 라벨 추가
        self.label = QLabel("Enter search keyword:")  # 검색어 입력 안내 라벨
        self.layout.addWidget(self.label)

        self.search_input = QLineEdit()  # 검색어 입력 창
        self.layout.addWidget(self.search_input)

        # 검색 버튼 추가 및 이벤트 연결
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_youtube)  # 버튼 클릭 시 검색 함수 호출
        self.layout.addWidget(self.search_button)

        # 검색 결과 리스트 추가 (검색된 동영상 목록 표시)
        self.result_list = QListWidget()
        self.result_list.itemClicked.connect(self.download_video)  # 리스트에서 항목 선택 시 다운로드 실행
        self.layout.addWidget(self.result_list)

        # 다운로드 폴더 선택 버튼 추가
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)  # 버튼 클릭 시 폴더 선택 창 실행
        self.layout.addWidget(self.folder_button)

        # 다운로드 진행 바 추가 (초기값 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # 최종 레이아웃 적용
        self.setLayout(self.layout)

        # 기본 다운로드 폴더 (사용자가 선택하지 않으면 None)
        self.download_folder = None

    def search_youtube(self):
        """ 유튜브에서 검색어를 기반으로 동영상을 검색하여 리스트에 표시 """
        keyword = self.search_input.text().strip()  # 검색어 가져오기
        if not keyword:
            QMessageBox.warning(self, "Input Required", "Please enter a search keyword!")  # 검색어가 없을 경우 경고
            return

        self.result_list.clear()  # 기존 검색 결과 초기화

        # YouTube 검색 옵션 설정
        ydl_opts = {
            'quiet': True,                      # 검색 중 출력 최소화
            'extract_flat': True,               # 세부 정보만 가져오고 다운로드는 하지 않음
            'default_search': 'ytsearch10',     # 검색 결과 최대 10개 가져오기
        }

        # yt_dlp를 이용하여 유튜브 검색 실행
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(keyword, download=False)  # 검색 실행
            if 'entries' in info:
                for entry in info['entries']:
                    video_title = entry['title']  # 동영상 제목
                    video_url = entry['url']  # 동영상 URL
                    self.result_list.addItem(f"{video_title} ({video_url})")  # 리스트에 추가

        QMessageBox.information(self, "Search Complete", "Search results loaded!")  # 검색 완료 메시지 표시

    def select_folder(self):
        """ 사용자에게 다운로드 폴더를 선택하도록 요청 """
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_folder = folder  # 선택된 폴더 저장
            QMessageBox.information(self, "Folder Selected", f"Download folder set to:\n{folder}")

    def download_video(self, item):
        """ 사용자가 선택한 동영상을 다운로드 """
        if not self.download_folder:
            QMessageBox.warning(self, "No Folder Selected", "Please select a download folder first!")  # 폴더 선택이 안 된 경우 경고
            return

        # 리스트에서 선택한 동영상의 URL 추출
        video_info = item.text()
        video_url = video_info.split("(")[-1].strip(")")

        QMessageBox.information(self, "Download", f"Starting download: {video_url}")  # 다운로드 시작 알림

        # 다운로드를 위한 QThread 실행
        self.download_thread = DownloadThread(video_url, self.download_folder)
        self.download_thread.progress_update.connect(self.progress_bar.setValue)  # 진행률 업데이트 연결
        self.download_thread.download_complete.connect(self.show_success_message)  # 다운로드 완료 시 알림
        self.download_thread.download_error.connect(self.show_error_message)  # 다운로드 오류 발생 시 알림
        self.download_thread.start()

    def show_success_message(self, message):
        """ 다운로드가 완료되었을 때 메시지 박스 표시 """
        QMessageBox.information(self, "Download Complete", message)

    def show_error_message(self, message):
        """ 다운로드 중 오류가 발생했을 때 메시지 박스 표시 """
        QMessageBox.critical(self, "Error", message)


# 프로그램 실행 코드
if __name__ == "__main__":
    app = QApplication(sys.argv)  # Qt 애플리케이션 실행
    window = YouTubeDownloader()  # 메인 UI 인스턴스 생성
    window.show()  # 창 띄우기
    sys.exit(app.exec())  # 이벤트 루프 실행
