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
    client_secret_str = st.secrets["google_oauth"]["client_secret_json"]
    client_secret_file = io.StringIO(client_secret_str)
    client_config = json.load(client_secret_file)
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    auth_url, _ = flow.authorization_url(prompt='consent')

    st.markdown(f"**Click link dưới để cấp quyền:** [Google OAuth]({auth_url})")
    code = st.text_input("Dán mã code từ trang cấp quyền ở đây:")

    creds = None
    if code:
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
        except Exception as e:
            st.error(f"Lỗi lấy token: {e}")

    if creds:
        youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
        youtube = build("youtube", "v3", credentials=creds)
        return youtube_analytics, youtube
    else:
        return None, None

def main():
    st.title("YouTube Analytics OAuth trên Streamlit Cloud")

    if st.button("Bắt đầu đăng nhập OAuth"):
        youtube_analytics, youtube = get_authenticated_services()
        if youtube_analytics and youtube:
            st.success("Đăng nhập thành công!")
            # Bạn có thể gọi hàm lấy dữ liệu ở đây...
            st.write("Bây giờ bạn có thể lấy dữ liệu YouTube Analytics rồi.")
        else:
            st.info("Vui lòng làm theo hướng dẫn cấp quyền và nhập mã code.")

if __name__ == "__main__":
    main()
