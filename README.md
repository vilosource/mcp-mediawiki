# MediaWiki MCP Server Specification

## Overview

The MediaWiki MCP (Model Context Protocol) server provides a structured interface for accessing and editing content on a local MediaWiki instance. It is designed for easy use by LLMs and other automation tools to fetch, process, and optionally update wiki content.

## MediaWiki Endpoint

* **Base URL**: Configurable via environment variables

## Goals

* Serve full-page wiki content in response to LLM queries like "Get me wiki page DevOps"
* Support editing pages with content generated from user interaction
* Ensure clear, predictable API design
* Avoid chunking; return full page content only

## Functional Endpoints

### 1. GET /v1/context

Fetches the full content of a specified MediaWiki page.

**Query Parameters:**

* `title` *(required)*: Title of the page (e.g., `DevOps`)

**Response:**

```json
[
  {
    "id": "wiki:DevOps",
    "name": "DevOps",
    "content": "Full wikitext or rendered content...",
    "metadata": {
      "source": "wiki.example.com",
      "url": "https://wiki.example.com/wiki/DevOps",
      "last_modified": "2025-06-01T14:20:00Z",
      "namespace": 0
    }
  }
]
```

### 2. POST /v1/write

Allows an authenticated client to update a wiki page using a bot account.

**Headers:**

* `Authorization: Bearer <token>`

**Request Payload:**

```json
{
  "title": "DevOps",
  "content": "== New Section ==\nContent here...",
  "summary": "Updated based on discussion"
}
```

**Response:**

```json
{
  "status": "success",
  "revision_id": 12345,
  "url": "https://wiki.example.com/wiki/DevOps"
}
```

## Authentication

* Uses bot accounts with write permissions configured in `LocalSettings.php`:

```php
$wgGroupPermissions['bot']['edit'] = true;
$wgGroupPermissions['bot']['createpage'] = true;
$wgGroupPermissions['bot']['writeapi'] = true;
```

## Implementation Library

* **Preferred**: [MCP Python SDK](https://pypi.org/project/mcp/) for protocol-compliant integration
* **mwclient**: Used internally for interacting with MediaWiki

## LLM-Friendly Design Considerations

* Case-insensitive title matching
* Clear errors with hints (`Page not found`, `Did you mean...?`)
* Optional preview or diff endpoints
* Explicit `operation` field in write payload (e.g., `append`, `replace`)
* Help endpoint with prompt-to-API examples

## Requirements

### `requirements.txt`

```txt
mcp[cli]
mwclient
python-dotenv
```

### `.env` file

```env
MW_API_HOST=wiki.example.com
MW_API_PATH=/wiki/
MW_USE_HTTPS=true
MW_BOT_USER=mcp-bot
MW_BOT_PASS=secret-password
```

## Example Code (MCP SDK + environment variables only)

### `mcp_mediawiki.py`

```python
import os
import mwclient
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

host = os.getenv("MW_API_HOST")
path = os.getenv("MW_API_PATH", "/wiki/")
scheme = "https" if os.getenv("MW_USE_HTTPS", "true").lower() == "true" else "http"
user = os.getenv("MW_BOT_USER")
password = os.getenv("MW_BOT_PASS")

site = mwclient.Site(host=host, path=path, scheme=scheme)
if user and password:
    site.login(user, password)

mcp = FastMCP("mcp_mediawiki")

@mcp.resource("wiki://{title}")
def get_page(title: str):
    page = site.pages[title]
    if not page.exists:
        return {"error": f"Page '{title}' not found"}
    return {
        "id": f"wiki:{title}",
        "name": title,
        "content": page.text(),
        "metadata": {
            "url": f"{scheme}://{host}{path}index.php/{title}",
            "last_modified": page.revisions().next()["timestamp"],
            "namespace": page.namespace
        }
    }

@mcp.tool()
def update_page(title: str, content: str, summary: str):
    page = site.pages[title]
    page.save(text=content, summary=summary)
    return {
        "status": "success",
        "title": title,
        "url": f"{scheme}://{host}/wiki/{title}"
    }

if __name__ == "__main__":
    mcp.run()
```

---

This server enables powerful integration between AI systems and MediaWiki content, with a focus on simplicity, full-page context, and safe edit capabilities. The MCP Python SDK ensures protocol compliance and standard integration behavior.


🐳 Dockerfile
Create a Dockerfile to containerize your application:

Dockerfile
Copy
Edit
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "mcp_mediawiki.py"]
This Dockerfile sets up a Python environment, installs dependencies, and runs your mcp_mediawiki application.
services.duq.edu
+2
instructure.com
+2
csustan.edu
+2

🖥️ CLI Interface
Implement a CLI using argparse to interact with your MCP server:

python
Copy
Edit
import argparse
import requests

def get_page(title):
    response = requests.get(f"http://localhost:8000/v1/context?title={title}")
    print(response.json())

def update_page(title, content, summary):
    payload = {
        "title": title,
        "content": content,
        "summary": summary
    }
    headers = {
        "Authorization": "Bearer YOUR_TOKEN"
    }
    response = requests.post("http://localhost:8000/v1/write", json=payload, headers=headers)
    print(response.json())

def main():
    parser = argparse.ArgumentParser(description="MCP MediaWiki CLI")
    subparsers = parser.add_subparsers(dest="command")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("title", help="Title of the wiki page")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("title", help="Title of the wiki page")
    update_parser.add_argument("content", help="Content to update the page with")
    update_parser.add_argument("summary", help="Edit summary")

    args = parser.parse_args()

    if args.command == "get":
        get_page(args.title)
    elif args.command == "update":
        update_page(args.title, args.content, args.summary)

if __name__ == "__main__":
    main()
This script allows you to fetch and update wiki pages via the command line.

🔍 Additional Search Functionality
Add a search endpoint to your FastAPI application:

python
Copy
Edit
from fastapi import FastAPI, Query
from mediawiki_client import site

app = FastAPI()

@app.get("/v1/search")
def search_pages(query: str = Query(..., min_length=1)):
    results = site.search(query)
    return [{"title": result["title"], "snippet": result["snippet"]} for result in results]
This endpoint allows users to search for wiki pages matching a query string.


