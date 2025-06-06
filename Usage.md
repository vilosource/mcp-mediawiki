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

## Server Configuration

Create a `.env` file with your MediaWiki connection details as shown above. The
server no longer accepts command line options; all configuration is read from the
environment.

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
