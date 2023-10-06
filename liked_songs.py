import logging
import os
import sys

import requests
from ytmusicapi import YTMusic

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
NOTION_VERSION = "2022-06-28"

YOUTUBE_OAUTH_JSON = os.environ["YOUTUBE_OAUTH_JSON"]
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("")


def retrieve_liked_songs_list(oauth_json):
    ytmusic = YTMusic(oauth_json)
    return ytmusic.get_liked_songs(limit=None)


def retrieve_notion_songs(database_id, notion_version, notion_api_key):
    page_data = []
    start_cursor = None
    while True:
        data = {"page_size": 100}
        if start_cursor:
            data["start_cursor"] = start_cursor
        response = requests.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            json=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Notion-Version": notion_version,
                "Authorization": f"Bearer {notion_api_key}",
            },
        )
        response_data = response.json()
        page_data.extend(response_data["results"])

        if response_data["next_cursor"]:
            start_cursor = response_data["next_cursor"]
        else:
            break
    return page_data


def determine_new_songs(liked_songs, notion_pages):
    new_songs = []
    existing_songs = {
        page["properties"]["video_id"]["rich_text"][0]["text"]["content"]
        for page in notion_pages
    }
    for song in liked_songs:
        if song["videoId"] not in existing_songs:
            new_songs.append(song)
    return new_songs


def add_new_songs(new_songs, database_id, notion_version, notion_api_key):
    for song in new_songs:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Accept": "application/json",
                "Notion-Version": notion_version,
                "Content-Type": "application/json",
                "Authorization": f"Bearer {notion_api_key}",
            },
            json={
                "parent": {"database_id": database_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": song["title"], "link": None},
                            }
                        ]
                    },
                    "Artist": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": ",".join(
                                        artist["name"] for artist in song["artists"]
                                    ),
                                    "link": None,
                                },
                            }
                        ]
                    },
                    "Album": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": song.get("album", {}).get("name", "")
                                    if song["album"]
                                    else "",
                                    "link": None,
                                },
                            }
                        ]
                    },
                    "Cover": {
                        "files": [
                            {
                                "name": "Cover Art",
                                "external": {
                                    "url": song["thumbnails"][-1]["url"],
                                },
                            }
                        ]
                    },
                    "Duration": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": song.get("duration", ""),
                                    "link": None,
                                },
                            }
                        ]
                    },
                    "duration_seconds": {"number": song.get("duration_seconds", 0)},
                    "video_id": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": song["videoId"],
                                    "link": None,
                                },
                            }
                        ]
                    },
                    "Video": {"url": f"https://youtube.com/watch?v={song['videoId']}"},
                },
                "icon": {
                    "type": "external",
                    "external": {"url": song["thumbnails"][0]["url"]},
                },
                "cover": {
                    "type": "external",
                    "external": {"url": song["thumbnails"][-1]["url"]},
                },
            },
        )
        response_data = response.json()
        if response_data.get("object") == "error":
            logger.error(f"Error creating page. Response: {response_data}")


def main(args):
    logger.info("Retrieving liked songs playlist from YouTube...")
    liked_songs = retrieve_liked_songs_list(YOUTUBE_OAUTH_JSON)
    logger.debug(f"Payload: {liked_songs}")
    logger.info(f"Success. Found {len(liked_songs['tracks'])} songs.")

    logger.info("Retrieving Notion songs database...")
    notion_pages = retrieve_notion_songs(
        NOTION_DATABASE_ID, NOTION_VERSION, NOTION_API_KEY
    )
    logger.debug(f"Notion Pages: {notion_pages}")
    logger.info(f"Success. Found {len(notion_pages)} notion pages.")

    logger.info("Determining new songs to add...")
    songs_to_add = determine_new_songs(liked_songs["tracks"], notion_pages)
    logger.info(f"{len(songs_to_add)} new songs to add.")

    logger.info("Adding new songs...")
    add_new_songs(songs_to_add, NOTION_DATABASE_ID, NOTION_VERSION, NOTION_API_KEY)
    logger.info("Success adding new songs.")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
