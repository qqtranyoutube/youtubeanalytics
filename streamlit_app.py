import streamlit as st
import json
import io
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_authenticated_services():
    # Lấy JSON OAuth config từ secrets
    client_secret_str = st.secrets["google_oauth"]["client_secret_json"]
    client_secret_file = io.StringIO(client_secret_str)

    # Load config JSON từ chuỗi
    client_config = json.load(client_secret_file)

    # Tạo flow OAuth từ config JSON
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    # Chạy flow, hiển thị URL ở terminal để user xác thực
    creds = flow.run_console()

    # Tạo service YouTube Analytics & YouTube Data API
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    youtube = build("youtube", "v3", credentials=creds)

    return youtube_analytics, youtube


def main():
    st.title("YouTube Analytics với OAuth qua Streamlit Secrets")

    if st.button("Đăng nhập với Google OAuth"):
        youtube_analytics, youtube = get_authenticated_services()
        st.success("Đăng nhập thành công!")

        # Tiếp tục phần xử lý dữ liệu analytics ...
        st.write("Bạn đã đăng nhập và có thể bắt đầu lấy dữ liệu...")

if __name__ == "__main__":
    main()
