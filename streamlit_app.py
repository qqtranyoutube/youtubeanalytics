import streamlit as st
from google_auth_oauthlib.flow import Flow
import json
import io
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

def get_oauth_flow():
    client_secret_str = st.secrets["google_oauth"]["client_secret_json"]
    client_config = json.load(io.StringIO(client_secret_str))

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    return flow

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

def get_youtube_analytics_service(creds):
    return build('youtubeAnalytics', 'v2', credentials=creds)

def get_channel_id(youtube):
    response = youtube.channels().list(mine=True, part="id").execute()
    channel_id = response['items'][0]['id']
    return channel_id

def get_audience_demographics(analytics, channel_id):
    return analytics.reports().query(
        ids='channel=={}'.format(channel_id),
        startDate='2023-01-01',
        endDate='2023-12-31',
        metrics='views,estimatedMinutesWatched',
        dimensions='ageGroup,gender',
        sort='ageGroup,gender'
    ).execute()

def get_device_type_report(analytics, channel_id):
    return analytics.reports().query(
        ids='channel=={}'.format(channel_id),
        startDate='2023-01-01',
        endDate='2023-12-31',
        metrics='views',
        dimensions='deviceType',
        sort='deviceType'
    ).execute()

def get_rpm_report(analytics, channel_id):
    response = analytics.reports().query(
        ids='channel=={}'.format(channel_id),
        startDate='2023-01-01',
        endDate='2023-12-31',
        metrics='estimatedRevenue,adImpressions',
        dimensions='day',
        filters='estimatedRevenue>0',
        sort='day'
    ).execute()

    rows = response.get('rows', [])
    rpm_data = []
    for row in rows:
        day, revenue, impressions = row
        impressions = float(impressions)
        revenue = float(revenue)
        rpm = revenue / (impressions / 1000) if impressions != 0 else 0
        rpm_data.append({'day': day, 'rpm': rpm})
    return rpm_data

def main():
    st.title("YouTube Analytics OAuth & Data Demo")

    if "credentials" not in st.session_state:
        st.session_state["credentials"] = None

    if st.session_state["credentials"] is None:
        flow = get_oauth_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.markdown("### Bước 1: Mở link cấp quyền OAuth và đăng nhập tài khoản Google của bạn")
        st.markdown(f"[Mở link cấp quyền OAuth]({auth_url})")

        code = st.text_input("Bước 2: Dán mã code nhận được sau khi cấp quyền vào đây")

        if code:
            try:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state["credentials"] = creds_to_dict(creds)
                st.success("Đã cấp quyền thành công! Bạn có thể xem dữ liệu bên dưới.")
            except Exception as e:
                st.error(f"Cấp quyền thất bại: {e}")
    else:
        creds = dict_to_creds(st.session_state["credentials"])
        youtube = build("youtube", "v3", credentials=creds)
        analytics = get_youtube_analytics_service(creds)

        try:
            channel_id = get_channel_id(youtube)
            st.write(f"Channel ID: {channel_id}")

            st.subheader("Phân tích Độ tuổi và Giới tính người xem")
            demographics = get_audience_demographics(analytics, channel_id)
            st.json(demographics)

            st.subheader("Phân tích Loại Thiết bị")
            devices = get_device_type_report(analytics, channel_id)
            st.json(devices)

            st.subheader("Báo cáo RPM (Revenue per Mille)")
            rpm = get_rpm_report(analytics, channel_id)
            st.write(rpm)

        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu YouTube Analytics: {e}")

if __name__ == "__main__":
    main()
