import os
import base64
from ytmusicapi import OAuthCredentials, YTMusic
import requests
from dotenv import load_dotenv

load_dotenv()

# Decode the base64-encoded oauth.json file
oauth_json_base64 = os.getenv('OAUTH_JSON_BASE64')
oauth_json = base64.b64decode(oauth_json_base64).decode('utf-8')

# Write the decoded oauth.json to a file
with open('oauth.json', 'w') as f:
    f.write(oauth_json)
s = requests.Session()
s.request = functools.partial(s.request, timeout=60)
yt = YTMusic('oauth.json', oauth_credentials=OAuthCredentials(client_id=os.getenv('CLIENT_ID'), client_secret=os.getenv('CLIENT_SECRET')), requests_session=s)

def get_jams_from_item_shop():
    url = "https://fortnite-api.com/v2/shop"
    result = {
        "hash": "",
        "tracks": []
    }
    with requests.session() as s:
        response = s.get(url)
        data = response.json()
    if data["status"] == 200:
        result["hash"] = data["data"]["hash"]
        seen_titles = set()
        for item in data["data"]["entries"]:
            if "tracks" in item:
                for track in item["tracks"]:
                    if track["title"] not in seen_titles:
                        result["tracks"].append({
                            "title": track["title"],
                            "artist": track["artist"],
                            "album": track.get("album", ""),
                            "releaseYear": track["releaseYear"]
                        })
                        seen_titles.add(track["title"])
    return result

def search_and_add_tracks_to_playlist(playlist_id, tracks):
    videos = []
    for track in tracks:
        search_results = yt.search(f"{track['artist']} {track['title']} {track.get('album') or ''} {track.get('releaseYear') or ''}")
        if search_results and 'videoId' in search_results[0]:
            videos.append(search_results[0]['videoId'])
            print(f"Added {track['title']} by {track['artist']} to the playlist.")
        else:
            print(f"Could not find {track['title']} by {track['artist']} on YouTube.")
    
    yt.add_playlist_items(playlist_id, videos)

def save_oauth_json():
    with open('oauth.json', 'r') as f:
        updated_oauth_json = f.read()
    updated_oauth_json_base64 = base64.b64encode(updated_oauth_json.encode('utf-8')).decode('utf-8')
    return updated_oauth_json_base64

if __name__ == "__main__":
    playlist_id = os.getenv("PLAYLIST_ID")
    tracks = get_jams_from_item_shop()
    playlist_items = yt.get_playlist(playlist_id)
    videos = [{"videoId" : item['videoId'], "setVideoId": item['setVideoId']} for item in playlist_items['tracks']]
    if videos:
        yt.remove_playlist_items(playlist_id, videos=videos)
    search_and_add_tracks_to_playlist(playlist_id, tracks["tracks"])
    print("Finished adding tracks to the playlist.")
    
    updated_oauth_json_base64 = save_oauth_json()
    print(f"::set-output name=OAUTH_JSON_BASE64::{updated_oauth_json_base64}")
