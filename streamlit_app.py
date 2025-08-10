import streamlit as st
import json
import io
import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_oauth_flow():
    client_secret_str = st.secrets["google_oauth"]["client_secret_json"]
    client_secret_file = io.StringIO(client_secret_str)
    client_config = json.load(client_secret_file)
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    return flow

def query_report(service, metrics, dimensions="", start_date=None, end_date=None, filters=None, sort=None, max_results=1000):
    params = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
        "dimensions": dimensions,
        "maxResults": max_results
    }
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    return service.reports().query(**params).execute()

def main():
    st.title("YouTube Analytics Nâng Cao với OAuth 2.0 trên Streamlit")

    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')

    st.markdown(f"### Bước 1: Click link để cấp quyền")
    st.markdown(f"[Google OAuth]({auth_url})")

    code = st.text_input("Bước 2: Dán mã code lấy được từ trang cấp quyền vào đây:")

    if code:
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials

            youtube_analytics = build("youtubeAnalytics", "v2", credentials=creds)
            youtube = build("youtube", "v3", credentials=creds)
            st.success("Đăng nhập thành công!")

            start_date = st.date_input("Ngày bắt đầu", datetime.date.today() - datetime.timedelta(days=30))
            end_date = st.date_input("Ngày kết thúc", datetime.date.today())

            sd = start_date.strftime("%Y-%m-%d")
            ed = end_date.strftime("%Y-%m-%d")

            # 1. Loại thiết bị
            st.subheader("1. Loại thiết bị")
            resp = query_report(youtube_analytics, "views", "deviceType", sd, ed, sort="-views")
            if "rows" in resp:
                df_device = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
                st.dataframe(df_device)
                fig = px.pie(df_device, names="deviceType", values="views", title="Phân bố thiết bị")
                st.plotly_chart(fig)
            else:
                st.write("Không có dữ liệu thiết bị")

            # 2. Thời gian xem từ người đăng ký
            st.subheader("2. Thời gian xem từ người đăng ký")
            resp = query_report(youtube_analytics, "estimatedMinutesWatched", "subscribedStatus", sd, ed)
            if "rows" in resp:
                df_sub = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
                st.dataframe(df_sub)
            else:
                st.write("Không có dữ liệu thời gian xem")

            # 3. Độ tuổi và giới tính
            st.subheader("3. Độ tuổi và giới tính")
            resp = query_report(youtube_analytics, "views", "ageGroup,gender", sd, ed, sort="-views")
            if "rows" in resp:
                df_age_gender = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
                st.dataframe(df_age_gender)
                fig = px.bar(df_age_gender, x="ageGroup", y="views", color="gender", barmode="group", title="Views theo tuổi và giới tính")
                st.plotly_chart(fig)
            else:
                st.write("Không có dữ liệu tuổi và giới tính")

            # 4. Kênh mà khán giả xem
            st.subheader("4. Kênh mà khán giả xem")
            # dimension: "subscribedStatus,video" hoặc dùng "insightPlaybackLocationType"
            # YouTube Analytics không có dimension "channelWatched", nên lấy kênh của video người xem
            # Dùng YouTube Data API tìm info video từ video IDs có thể phức tạp. Tạm bỏ mục này hoặc thay thế

            st.info("Mục này yêu cầu dữ liệu phức tạp, chưa hỗ trợ trực tiếp qua API Analytics.")

            # 5. Cách người xem tìm thấy video (Traffic Source)
            st.subheader("5. Cách người xem tìm thấy video")
            resp = query_report(youtube_analytics, "views", "insightTrafficSourceType", sd, ed, sort="-views")
            if "rows" in resp:
                df_traffic = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
                st.dataframe(df_traffic)
                fig = px.pie(df_traffic, names="insightTrafficSourceType", values="views", title="Nguồn traffic")
                st.plotly_chart(fig)
            else:
                st.write("Không có dữ liệu traffic source")

            # 6 & 7. RPM và Monetization
            st.subheader("6 & 7. RPM & Monetization")
            resp = query_report(youtube_analytics, "estimatedRevenue,monetizedPlaybacks,views", "", sd, ed)
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
                st.write("Không có dữ liệu RPM và Monetization")

            # 8. Video đạt 1000 views nhanh nhất
            st.subheader("8. Video đạt 1000 views nhanh nhất")

            # Lấy danh sách video trong khoảng thời gian để phân tích tốc độ đạt 1000 views
            # YouTube Analytics không có metric chuẩn cho "time to 1000 views" trực tiếp
            # Phương án:
            # - Lấy danh sách video trong khoảng thời gian (ví dụ, 100 video mới nhất)
            # - Lấy ngày đăng video, số view, tính toán gần đúng

            # Lấy 50 video upload gần đây:
            request = youtube.search().list(
                part="snippet",
                channelId="MINE",
                maxResults=50,
                order="date",
                type="video"
            )
            response = request.execute()

            videos = response.get("items", [])

            data = []
            for vid in videos:
                video_id = vid["id"]["videoId"]
                title = vid["snippet"]["title"]
                publish_date = vid["snippet"]["publishedAt"][:10]

                # Lấy số view của video
                stats_req = youtube.videos().list(
                    part="statistics,snippet",
                    id=video_id
                )
                stats_resp = stats_req.execute()
                items = stats_resp.get("items", [])
                if items:
                    stats = items[0]["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    data.append({
                        "video_id": video_id,
                        "title": title,
                        "publish_date": publish_date,
                        "view_count": view_count
                    })

            # Tính số ngày từ đăng video đến hôm nay
            today = datetime.date.today()
            for d in data:
                pub_date = datetime.datetime.strptime(d["publish_date"], "%Y-%m-%d").date()
                d["days_since_publish"] = (today - pub_date).days
                # Tránh chia cho 0
                d["days_since_publish"] = d["days_since_publish"] if d["days_since_publish"] > 0 else 1
                d["views_per_day"] = d["view_count"] / d["days_since_publish"]

            df_videos = pd.DataFrame(data)
            # Lọc video có view >= 1000
            df_1000 = df_videos[df_videos["view_count"] >= 1000]
            if not df_1000.empty:
                # Sắp xếp video đạt 1000 views nhanh nhất (days_since_publish nhỏ nhất)
                df_1000_sorted = df_1000.sort_values("days_since_publish")
                st.dataframe(df_1000_sorted[["title", "view_count", "publish_date", "days_since_publish", "views_per_day"]])
            else:
                st.write("Chưa có video nào đạt 1000 views trong khoảng thời gian này.")

        except Exception as e:
            st.error(f"Lỗi trong quá trình lấy dữ liệu hoặc đăng nhập: {e}")

if __name__ == "__main__":
    main()
