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
```

## Running the server

### With Docker Compose

```bash
docker compose up --build
```

### Without Compose

```bash
docker run --env-file .env mcp-mediawiki
```

Interact with the server using the `mcp` CLI. Fetch a page with:

```bash
mcp read wiki://Main_Page
```

Update a page using the `update_page` tool:

```bash
mcp run update_page --title Main_Page --content "New text" --summary "bot edit"
```

## Using with VSCode

1. Open this folder in VSCode.
2. Copy `.env.example` to `.env` and adjust the values for your wiki.
3. Use the integrated terminal to run `python mcp_mediawiki.py` or `docker compose up --build`.
4. The server will be available at `http://localhost:8000`.
