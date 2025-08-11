import streamlit as st
from googleapiclient.discovery import build
import pandas as pd

# Nhập API Key của bạn vào đây hoặc dùng streamlit secrets
API_KEY = st.secrets["youtube_api_key"]

def get_youtube_client():
    return build('youtube', 'v3', developerKey=API_KEY)

def get_channel_info(youtube, channel_id):
    res = youtube.channels().list(
        part='snippet,statistics',
        id=channel_id
    ).execute()
    if res['items']:
        return res['items'][0]
    else:
        return None

def get_channel_videos(youtube, channel_id, max_results=10):
    # Lấy playlist uploads của channel
    res = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()
    uploads_playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    videos = []
    nextPageToken = None
    while len(videos) < max_results:
        res = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=min(max_results - len(videos), 50),
            pageToken=nextPageToken
        ).execute()
        videos.extend(res['items'])
        nextPageToken = res.get('nextPageToken')
        if not nextPageToken:
            break
    return videos[:max_results]

def get_video_statistics(youtube, video_ids):
    res = youtube.videos().list(
        part='statistics,snippet',
        id=','.join(video_ids)
    ).execute()
    return res['items']

def main():
    st.title("YouTube Public Channel Analyzer")

    channel_id = st.text_input("Nhập Channel ID")

    if channel_id:
        youtube = get_youtube_client()

        channel_info = get_channel_info(youtube, channel_id)
        if not channel_info:
            st.error("Không tìm thấy kênh với ID này.")
            return

        st.header("Thông tin kênh")
        st.write(f"**Tên kênh:** {channel_info['snippet']['title']}")
        st.write(f"**Mô tả:** {channel_info['snippet'].get('description','')}")
        st.write(f"**Subscribers:** {channel_info['statistics'].get('subscriberCount','Không công khai')}")
        st.write(f"**Tổng lượt xem:** {channel_info['statistics'].get('viewCount','Không công khai')}")
        st.write(f"**Tổng video:** {channel_info['statistics'].get('videoCount','Không công khai')}")

        st.header("Danh sách video mới nhất")
        videos = get_channel_videos(youtube, channel_id, max_results=10)
        video_ids = [v['snippet']['resourceId']['videoId'] for v in videos]

        video_stats = get_video_statistics(youtube, video_ids)

        data = []
        for vid in video_stats:
            stats = vid['statistics']
            data.append({
                'Video ID': vid['id'],
                'Tiêu đề': vid['snippet']['title'],
                'Ngày đăng': vid['snippet']['publishedAt'][:10],
                'Lượt xem': stats.get('viewCount', 0),
                'Thích': stats.get('likeCount', 0),
                'Bình luận': stats.get('commentCount', 0)
            })

        df = pd.DataFrame(data)
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button("Tải CSV dữ liệu video", csv, "channel_videos.csv")

if __name__ == "__main__":
    main()
