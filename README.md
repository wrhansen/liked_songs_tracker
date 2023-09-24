# Liked Songs

Retrieves liked songs playlist from YouTube music api, and saves them to a Notion database for safe keeping. This program is designed to be run through github actions automation so that your notion database is
always updated with your current "liked songs" playlist.

# Environment Variables

* NOTION_API_KEY: Notion API key that you create with your integration
* NOTION_DATABASE_ID: The ID to the database page your are saving songs data to. Don't forget to connect your intregration to the database: [link](https://developers.notion.com/docs/create-a-notion-integration#give-your-integration-page-permissions)
* YOUTUBE_OAUTH_JSON: Json string containing oauth creds. For more information read this: [link](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html)
