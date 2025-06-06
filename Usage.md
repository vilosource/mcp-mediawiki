# Usage

This guide explains how to build and run the dockerised MCP MediaWiki server.

## Building the image

```bash
docker build -t mcp-mediawiki .
```

## Environment variables
Create a `.env` file with your MediaWiki details:

```
MW_API_HOST=wiki.example.com
MW_API_PATH=/wiki/
MW_USE_HTTPS=true
MW_BOT_USER=mcp-bot
MW_BOT_PASS=secret-password
MW_WRITE_TOKEN=changeme
```

## Running the server

```bash
docker run --env-file .env -p 8000:8000 mcp-mediawiki
```

The server exposes these endpoints:

- `GET /v1/context?title=Page` – fetch page content
- `GET /v1/search?query=term` – search pages
- `POST /v1/write` – update a page (requires `Authorization: Bearer $MW_WRITE_TOKEN`)

## Example request

```bash
curl "http://localhost:8000/v1/context?title=Main_Page"
```
