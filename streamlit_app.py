import streamlit as st
from google_auth_oauthlib.flow import Flow
import json
import io
from googleapiclient.discovery import build

# Các scope bạn cần
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

def get_oauth_flow():
    # Load client_secret.json từ streamlit secrets
    client_secret_str = st.secrets["google_oauth"]["client_secret_json"]
    client_config = json.load(io.StringIO(client_secret_str))

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"  # Manual code input flow
    )
    return flow

def main():
    st.title("YouTube Analytics OAuth Demo")

    # Lưu credentials trong session_state
    if "credentials" not in st.session_state:
        st.session_state["credentials"] = None

    if st.session_state["credentials"] is None:
        flow = get_oauth_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")

        st.markdown(f"### Bước 1: Mở link cấp quyền OAuth bên dưới và đăng nhập tài khoản Google của bạn (đã được thêm trong Test Users)")
        st.markdown(f"[Mở link cấp quyền OAuth]({auth_url})")

        code = st.text_input("Bước 2: Dán mã code nhận được sau khi cấp quyền vào đây")

        if code:
            try:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state["credentials"] = creds_to_dict(creds)
                st.success("Đã cấp quyền thành công! Bạn có thể chạy API tiếp theo.")
            except Exception as e:
                st.error(f"Cấp quyền thất bại: {e}")
    else:
        creds = dict_to_creds(st.session_state["credentials"])
        youtube = build("youtube", "v3", credentials=creds)
        st.success("Đã kết nối thành công với YouTube API!")

        # Ví dụ lấy thông tin kênh của người dùng
        response = youtube.channels().list(mine=True, part="snippet,contentDetails,statistics").execute()
        st.json(response)

        # Bạn có thể thêm code lấy dữ liệu RPM, thiết bị, độ tuổi... ở đây

def creds_to_dict(creds):
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

def dict_to_creds(data):
    from google.oauth2.credentials import Credentials
    return Credentials(
        token=data["token"],
        refresh_token=data.get("refresh_token"),
        token_uri=data["token_uri"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        scopes=data["scopes"]
    )

if __name__ == "__main__":
    main()
