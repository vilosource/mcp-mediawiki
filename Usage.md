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
docker run --env-file .env mcp-mediawiki
```

Interact with the server using the `mcp` CLI. Fetch a page with:

```bash
mcp read wiki://Main_Page
```

Update a page using the `update_page` tool:

```bash
mcp run update_page --title Main_Page --content "New text" --summary "bot edit" --token "$MW_WRITE_TOKEN"
```
