# Usage

This guide explains how to build and run the dockerised MCP MediaWiki server.

## Building the image

```bash
docker build -t mcp-mediawiki .
```

You can also use the Makefile:
```bash
make build
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

## Network Configuration

The Docker Compose configuration creates a custom network with the 192.168.169.0/24 subnet. The MCP server container is assigned a static IP address of 192.168.169.2. This allows the container to communicate with networks that might otherwise be inaccessible due to Docker's default networking.

To view network information:
```bash
make network-info
```

To check the container's IP address:
```bash
make container-ip
```

If you need to modify the network configuration, edit the `docker-compose.yml` file and adjust the subnet and IP address settings.

## Command Line Arguments

As an alternative to environment variables, you can also pass configuration options as command line arguments:

```bash
python mcp_mediawiki.py --api-host=wiki.example.com --api-path=/w/ --username=mcp-bot --password=secret-password --use-https=true
```

When using Docker, you can pass these arguments to the container:

```bash
docker run -p 8000:8000 mcp-mediawiki --api-host=wiki.example.com --username=mcp-bot
```

Or use the Makefile for convenience:

```bash
make run-args ARGS="--api-host=wiki.example.com --username=mcp-bot"
```

The following arguments are supported:

- `--api-host`: MediaWiki API hostname
- `--api-path`: MediaWiki API path
- `--username`: Bot username
- `--password`: Bot password
- `--use-https`: Use HTTPS connection (`true` or `false`)

Command line arguments take precedence over environment variables.

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
