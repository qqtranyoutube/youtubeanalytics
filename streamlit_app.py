import streamlit as st
import pandas as pd
import datetime
from googleapiclient.discovery import build
import plotly.express as px

st.title("YouTube Channel Analyzer - API Key version")

api_key = st.text_input("Nhập YouTube API Key của bạn", type="password")

channel_id = st.text_input("Nhập Channel ID cần phân tích (ví dụ: UC_x5XG1OV2P6uZZ5FSM9Ttw)")

if api_key and channel_id:
    youtube = build("youtube", "v3", developerKey=api_key)

    # Lấy playlist uploads của channel
    def get_uploads_playlist(youtube, channel_id):
        res = youtube.channels().list(part="contentDetails", id=channel_id).execute()
        items = res.get("items")
        if not items:
            return None
        uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return uploads_playlist_id

    # Lấy video trong playlist uploads
    def get_videos_in_playlist(youtube, playlist_id):
        videos = []
        nextPageToken = None
        while True:
            res = youtube.playlistItems().list(
                playlistId=playlist_id,
                part="snippet,contentDetails",
                maxResults=50,
                pageToken=nextPageToken
            ).execute()
            for item in res["items"]:
                videos.append({
                    "videoId": item["contentDetails"]["videoId"],
                    "title": item["snippet"]["title"],
                    "publishedAt": item["contentDetails"]["videoPublishedAt"]
                })
            nextPageToken = res.get("nextPageToken")
            if not nextPageToken:
                break
        return videos

    # Lấy stats video
    def get_video_stats(youtube, video_ids):
        stats = {}
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            res = youtube.videos().list(
                part="statistics,snippet",
                id=",".join(batch_ids)
            ).execute()
            for item in res["items"]:
                stats[item["id"]] = {
                    "title": item["snippet"]["title"],
                    "publishedAt": item["snippet"]["publishedAt"],
                    "viewCount": int(item["statistics"].get("viewCount", 0)),
                    "likeCount": int(item["statistics"].get("likeCount", 0))
                }
        return stats

    with st.spinner("Đang lấy dữ liệu..."):
        uploads_playlist_id = get_uploads_playlist(youtube, channel_id)
        if not uploads_playlist_id:
            st.error("Không tìm thấy channel hoặc playlist uploads.")
        else:
            videos = get_videos_in_playlist(youtube, uploads_playlist_id)
            video_ids = [v["videoId"] for v in videos]
            stats = get_video_stats(youtube, video_ids)

            # Kết hợp data
            data = []
            for v in videos:
                vid = v["videoId"]
                if vid in stats:
                    data.append({
                        "videoId": vid,
                        "title": stats[vid]["title"],
                        "publishedAt": stats[vid]["publishedAt"],
                        "viewCount": stats[vid]["viewCount"],
                        "likeCount": stats[vid]["likeCount"]
                    })
            df = pd.DataFrame(data)
            df["publishedAt"] = pd.to_datetime(df["publishedAt"])

            st.write("### Danh sách video")
            st.dataframe(df.sort_values("publishedAt", ascending=False))

            # Tìm video đạt 1000 views nhanh nhất (giả định: video có views >= 1000 và ngày đăng gần nhất)
            df_1000 = df[df["viewCount"] >= 1000]
            if not df_1000.empty:
                fastest_video = df_1000.sort_values("publishedAt", ascending=False).iloc[0]
                st.write("### Video đạt 1000 views nhanh nhất (theo ngày đăng gần nhất):")
                st.write(f"**{fastest_video['title']}**")
                st.write(f"Views: {fastest_video['viewCount']}")
                st.write(f"Ngày đăng: {fastest_video['publishedAt']}")
                st.video(f"https://www.youtube.com/watch?v={fastest_video['videoId']}")
            else:
                st.write("Chưa có video nào đạt 1000 views")

            # Biểu đồ views theo ngày đăng
            fig = px.bar(df.sort_values("publishedAt"), x="publishedAt", y="viewCount", hover_data=["title"],
                         title="Lượt xem video theo ngày đăng")
            st.plotly_chart(fig)
