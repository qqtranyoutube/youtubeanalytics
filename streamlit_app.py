import streamlit as st
import pandas as pd
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import plotly.express as px

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

CLIENT_SECRETS_FILE = "client_secret.json"

def get_authenticated_services():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_console()  # Khi chạy lần đầu, sẽ hiển thị URL để bạn đăng nhập và cấp quyền
    youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube_analytics, youtube

def query_report(service, metrics, dimensions, start_date, end_date, filters=None, sort=None):
    params = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
        "dimensions": dimensions,
        "maxResults": 1000
    }
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    return service.reports().query(**params).execute()

def main():
    st.title("YouTube Analytics nâng cao với OAuth 2.0")

    if st.button("Đăng nhập với Google OAuth"):
        youtube_analytics, youtube = get_authenticated_services()
        st.success("Đăng nhập thành công!")

        start_date = st.date_input("Ngày bắt đầu", datetime.date.today() - datetime.timedelta(days=30))
        end_date = st.date_input("Ngày kết thúc", datetime.date.today())

        # 1. Loại thiết bị
        st.subheader("1. Loại thiết bị xem video")
        resp = query_report(youtube_analytics, "views", "deviceType", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), sort="-views")
        if "rows" in resp:
            df_device = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
            st.dataframe(df_device)
            fig = px.pie(df_device, names="deviceType", values="views", title="Phân bố thiết bị")
            st.plotly_chart(fig)
        else:
            st.write("Không có dữ liệu thiết bị")

        # 2. Thời gian xem từ người đăng ký
        st.subheader("2. Thời gian xem từ người đăng ký")
        resp = query_report(youtube_analytics, "estimatedMinutesWatched", "subscribedStatus", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if "rows" in resp:
            df_sub = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
            st.dataframe(df_sub)
        else:
            st.write("Không có dữ liệu thời gian xem")

        # 3. Độ tuổi và giới tính
        st.subheader("3. Độ tuổi và giới tính")
        resp = query_report(youtube_analytics, "views", "ageGroup,gender", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), sort="-views")
        if "rows" in resp:
            df_age_gender = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
            st.dataframe(df_age_gender)
            fig = px.bar(df_age_gender, x="ageGroup", y="views", color="gender", barmode="group", title="Phân bố views theo tuổi và giới tính")
            st.plotly_chart(fig)
        else:
            st.write("Không có dữ liệu tuổi giới tính")

        # 4. Cách người xem tìm thấy video (traffic sources)
        st.subheader("4. Nguồn traffic")
        resp = query_report(youtube_analytics, "views", "insightTrafficSourceType", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), sort="-views")
        if "rows" in resp:
            df_traffic = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
            st.dataframe(df_traffic)
            fig = px.pie(df_traffic, names="insightTrafficSourceType", values="views", title="Nguồn traffic")
            st.plotly_chart(fig)
        else:
            st.write("Không có dữ liệu nguồn traffic")

        # 5. RPM và Monetization
        st.subheader("5. RPM & Monetization")
        resp = query_report(youtube_analytics, "estimatedRevenue,monetizedPlaybacks,views", "", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if "rows" in resp:
            revenue = float(resp["rows"][0][0])
            monetized = int(resp["rows"][0][1])
            views = int(resp["rows"][0][2])
            rpm = revenue / views * 1000 if views > 0 else 0
            st.markdown(f"- **Estimated Revenue:** ${revenue:,.2f}")
            st.markdown(f"- **Monetized Playbacks:** {monetized:,}")
            st.markdown(f"- **Views:** {views:,}")
            st.markdown(f"- **RPM:** ${rpm:,.2f}")
        else:
            st.write("Không có dữ liệu RPM & Monetization")

if __name__ == "__main__":
    main()
