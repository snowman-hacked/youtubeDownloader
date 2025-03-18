import tkinter as tk
from tkinter import simpledialog, messagebox
from pytubefix import YouTube
from pytubefix.cli import on_progress

# YouTube 동영상을 다운로드하는 함수
def youtube_downloader(url):
    try:
        # YouTube 객체 생성 및 진행 상황 콜백 설정
        yt = YouTube(url, on_progress_callback=on_progress)
        print(f"Title: {yt.title}")
        
        # 최고 해상도의 스트림 가져오기
        ys = yt.streams.get_highest_resolution()
        
        # 스트림 다운로드
        ys.download()
        
        # 다운로드 완료 메시지 표시
        messagebox.showinfo("Download Complete", f"Video '{yt.title}' has been downloaded successfully.")
    except Exception as e:
        # 오류 발생 시 오류 메시지 표시
        messagebox.showerror("Error", str(e))

# 사용자로부터 YouTube URL을 입력받는 함수
def get_url():
    # Tkinter 루트 윈도우 생성 및 숨기기
    root = tk.Tk()
    root.withdraw()
    
    # URL 입력 대화상자 표시
    url = simpledialog.askstring("YouTube Downloader", "Enter the YouTube URL:")
    
    # URL이 입력된 경우 다운로드 함수 호출
    if url:
        youtube_downloader(url)
    elif url is None: # 사용자가 "취소" 버튼을 클릭한 경우
        root.destroy() #close the window
    else:
        # URL이 입력되지 않은 경우 경고 메시지 표시
        messagebox.showwarning("Input Required", "Please enter a valid URL!")

# 스크립트가 직접 실행될 때 get_url 함수 호출
if __name__ == "__main__":
    get_url()